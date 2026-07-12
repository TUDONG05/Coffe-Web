"""
Chatbot router — POST /api/chat (SSE streaming qua Ollama local).
RAG: TF-IDF search trên Product DB, inject context vào system prompt.
Hỗ trợ đặt hàng: phát hiện intent, trích xuất món song song, inject order_form event.
"""
import asyncio
import json
import logging
import os
import re
import time
from collections import defaultdict
from typing import AsyncGenerator, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from highlands import models
from highlands.auth_utils import require_admin
from highlands.database import get_db
from highlands.services.menu_rag_service import menu_rag, compute_hot_items

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chatbot"])

# ── Cấu hình Ollama ─────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Từ khoá nhận diện intent đặt hàng
ORDER_KEYWORDS = [
    "đặt", "order", "mua", "cho tôi", "cho mình",
    "gọi món", "thêm vào", "lấy cho", "muốn dùng", "muốn uống",
]

SYSTEM_PROMPT_TEMPLATE = """Bạn là trợ lý tư vấn và đặt hàng thân thiện của Tu's Coffee.

!!! QUAN TRỌNG NHẤT: CHỈ ĐƯỢC VIẾT BẰNG TIẾNG VIỆT. KHÔNG ĐƯỢC DÙNG CHỮ HÁN, CHỮ TRUNG QUỐC, KÝ TỰ TIẾNG TRUNG. Mọi ký tự trong câu trả lời phải là tiếng Việt hoặc số hoặc emoji. !!!

NHIỆM VỤ:
- Tư vấn, giới thiệu các món trong thực đơn
- Giải đáp về giá, kích thước, thành phần, hương vị
- Gợi ý món phù hợp với sở thích hoặc dịp
- Hỗ trợ khách đặt hàng khi được yêu cầu

KHI KHÁCH MUỐN ĐẶT HÀNG:
- Xác nhận ngắn gọn các món và giá tiền
- Thông báo form đặt hàng đã sẵn sàng bên dưới để khách điền thông tin
- Ví dụ: "Tuyệt! Mình đã chuẩn bị đơn hàng cho bạn 📋 Vui lòng điền thông tin giao hàng bên dưới nhé!"

GIỚI HẠN:
- CHỈ trả lời trong phạm vi các thông tin cửa hàng, thực đơn và dịch vụ Tu's Coffee
- Nếu hỏi ngoài phạm vi: "Xin lỗi, tôi chỉ có thể tư vấn về thực đơn của Tu's Coffee ạ 😊"

PHONG CÁCH:
- Thân thiện, nhiệt tình như nhân viên phục vụ thực thụ
- Ngắn gọn (dưới 120 từ)
- Dùng emoji phù hợp ☕🧋🍞

THỰC ĐƠN LIÊN QUAN:
{menu_context}
"""

EXTRACT_PROMPT = """Bạn là hệ thống trích xuất thông tin đặt hàng. Trả về JSON, KHÔNG có text khác.

Tin nhắn khách: "{message}"

Danh sách menu (product_id|tên_món|giá):
{menu_list}

Trả về JSON (không giải thích):
{{"items": [{{"product_id": <id số nguyên>, "name": "<tên chính xác từ menu>", "qty": <số lượng>}}], "customer_name": <"tên" hoặc null>, "phone": <"sdt" hoặc null>, "address": <"địa chỉ" hoặc null>, "note": <"ghi chú" hoặc null>}}

Lưu ý: qty mặc định = 1 nếu không nêu rõ. Chỉ lấy các món có trong menu. Nếu không tìm thấy: {{"items": []}}"""


# ── Schemas ─────────────────────────────────────────────────

# ── Simple in-memory rate limiter ───────────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW = 60   # seconds
_RATE_MAX    = 20   # requests per window per IP

def _enforce_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    hits = [t for t in _rate_store[ip] if now - t < _RATE_WINDOW]
    if len(hits) >= _RATE_MAX:
        raise HTTPException(status_code=429, detail="Quá nhiều yêu cầu, vui lòng thử lại sau 1 phút")
    hits.append(now)
    _rate_store[ip] = hits


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=2000)


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default=[], max_length=20)
    user_name: str = Field(default="", max_length=100)
    user_phone: str = Field(default="", max_length=20)
    user_address: str = Field(default="", max_length=300)


# ── Helpers ─────────────────────────────────────────────────

def _strip_chinese(text: str) -> str:
    """Xóa ký tự Hán/Trung Quốc khỏi text (CJK Unified Ideographs)."""
    return re.sub(r"[一-鿿㐀-䶿豈-﫿]", "", text)


def _detect_order_intent(message: str) -> bool:
    """Kiểm tra tin nhắn có intent đặt hàng không."""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in ORDER_KEYWORDS)


def _build_system_prompt(query: str) -> str:
    """RAG: tìm món liên quan, build system prompt với context."""
    matched = menu_rag.search(query, top_k=6)
    context = menu_rag.format_context(matched)
    return SYSTEM_PROMPT_TEMPLATE.format(menu_context=context)


async def _extract_order_data(message: str, req: ChatRequest) -> dict | None:
    """Dùng LLM trích xuất món + thông tin đặt hàng từ message. Chạy song song với stream."""
    if not menu_rag._items:
        return None

    products_by_id = {item["id"]: item for item in menu_rag._items}
    menu_list = "\n".join(
        f"{item['id']}|{item['name']}|{item['price']:,}đ"
        for item in menu_rag._items
    )
    prompt = EXTRACT_PROMPT.format(message=message, menu_list=menu_list)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {"temperature": 0.1, "num_predict": 400},
                },
            )
            if resp.status_code != 200:
                return None
            raw = resp.json().get("message", {}).get("content", "")
    except Exception as e:
        logger.warning(f"Order extraction request failed: {e}")
        return None

    # Parse JSON từ response
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return None
        data = json.loads(m.group())
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Order extraction JSON parse failed: {e} | raw={raw[:200]}")
        return None

    # Kiểm tra từng món với in-memory index
    items = []
    for item in data.get("items", []):
        try:
            pid = int(item.get("product_id", 0))
        except (TypeError, ValueError):
            continue
        if pid in products_by_id:
            product = products_by_id[pid]
            qty = max(1, int(item.get("qty", 1)))
            items.append({
                "product_id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "qty": qty,
            })

    if not items:
        return None

    total = sum(i["price"] * i["qty"] for i in items)
    return {
        "items": items,
        "customer_name": data.get("customer_name") or req.user_name,
        "phone": data.get("phone") or req.user_phone,
        "address": data.get("address") or req.user_address,
        "note": data.get("note") or "",
        "total": total,
    }


async def _stream_ollama(
    system: str,
    messages: list[dict],
    order_task: asyncio.Task | None = None,
    product_cards: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream Ollama response, inject product_cards + order_form trước [DONE] nếu có."""
    payload = {
        "model": OLLAMA_MODEL,
        "stream": True,
        "messages": [{"role": "system", "content": system}] + messages,
        "options": {"temperature": 0.7, "num_predict": 300},
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload
            ) as resp:
                if resp.status_code != 200:
                    yield f"data: {json.dumps({'error': 'Ollama không phản hồi'})}\n\n"
                    return

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = _strip_chinese(chunk.get("message", {}).get("content", ""))
                        if token:
                            yield f"data: {json.dumps({'token': token})}\n\n"
                        if chunk.get("done"):
                            # 1. Product cards
                            if product_cards:
                                yield f"data: {json.dumps({'type': 'product_cards', 'products': product_cards})}\n\n"
                            # 2. Order form (chờ extraction task song song)
                            if order_task is not None:
                                try:
                                    order_data = await asyncio.wait_for(
                                        order_task, timeout=10.0
                                    )
                                    if order_data:
                                        yield f"data: {json.dumps({'type': 'order_form', 'order': order_data})}\n\n"
                                except asyncio.TimeoutError:
                                    logger.warning("Order extraction timed out")
                                except Exception as e:
                                    logger.warning(f"Order task error: {e}")
                            yield "data: [DONE]\n\n"
                            return
                    except json.JSONDecodeError:
                        continue

    except httpx.ConnectError:
        yield f"data: {json.dumps({'error': 'Không kết nối được Ollama. Hãy đảm bảo Ollama đang chạy.'})}\n\n"
    except Exception as e:
        logger.error(f"Ollama stream error: {e}")
        yield f"data: {json.dumps({'error': 'Đã xảy ra lỗi, vui lòng thử lại.'})}\n\n"


# ── Endpoints ────────────────────────────────────────────────

@router.post("/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """Chat với chatbot, trả về SSE stream. Hỗ trợ đặt hàng qua order_form event."""
    _enforce_rate_limit(request)
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Tin nhắn không được trống")
    if len(req.message) > 500:
        raise HTTPException(status_code=400, detail="Tin nhắn quá dài (tối đa 500 ký tự)")

    system = _build_system_prompt(req.message)
    messages = [{"role": m.role, "content": m.content} for m in req.history[-6:]]
    messages.append({"role": "user", "content": req.message})

    # Product cards: chỉ hiện khi có kết quả liên quan (không fallback)
    relevant = menu_rag.search_relevant(req.message, top_k=4)
    product_cards: list[dict] | None = [
        {
            "id":        p["id"],
            "name":      p["name"],
            "price":     p["price"],
            "image_url": p.get("image_url", ""),
            "category":  p.get("category", ""),
        }
        for p in relevant
    ] or None

    # Tạo extraction task song song nếu phát hiện order intent
    order_task = None
    if _detect_order_intent(req.message):
        order_task = asyncio.create_task(_extract_order_data(req.message, req))

    return StreamingResponse(
        _stream_ollama(system, messages, order_task, product_cards),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/reload-menu")
def reload_menu(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reload TF-IDF index + hot items từ DB (gọi sau khi admin thêm/sửa sản phẩm)."""
    products = db.query(models.Product).filter(models.Product.is_active == 1).all()
    menu_rag.build_index(products)
    menu_rag.set_hot_items(compute_hot_items(db))
    return {"message": f"Đã reload {menu_rag.total} sản phẩm vào chatbot index."}


@router.get("/status")
def chat_status():
    """Kiểm tra trạng thái chatbot và Ollama."""
    return {
        "menu_items_indexed": menu_rag.total,
        "ollama_url": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL,
    }
