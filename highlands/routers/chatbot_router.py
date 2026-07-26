"""
Chatbot router — POST /api/chat (SSE streaming).
Backend: Groq API (production) hoặc Ollama local (dev, khi không có GROQ_API_KEY).
RAG: hybrid search (embedding Gemini qua pgvector + TF-IDF) trên Product DB,
inject context vào system prompt.
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
from highlands.services import embedding_service
from highlands.services.menu_rag_service import (
    backfill_embeddings,
    compute_hot_items,
    ensure_index_loaded,
    menu_rag,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chatbot"])

# ── Cấu hình LLM ────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL  = "https://api.groq.com/openai/v1"
GROQ_MODEL     = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Fallback Ollama cho dev local
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

USE_GROQ = bool(GROQ_API_KEY)

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


async def _build_system_prompt(db: Session, query: str) -> str:
    """RAG: hybrid search món liên quan, build system prompt với context."""
    context = await menu_rag.hybrid_context(db, query, top_k=6)
    return SYSTEM_PROMPT_TEMPLATE.format(menu_context=context)


async def _llm_complete(messages: list[dict], temperature: float = 0.1, max_tokens: int = 400) -> str:
    """Gọi LLM (Groq hoặc Ollama) và trả về nội dung text."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            if USE_GROQ:
                resp = await client.post(
                    f"{GROQ_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    json={"model": GROQ_MODEL, "messages": messages,
                          "temperature": temperature, "max_tokens": max_tokens, "stream": False},
                )
                if resp.status_code != 200:
                    return ""
                return resp.json()["choices"][0]["message"]["content"]
            else:
                resp = await client.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json={"model": OLLAMA_MODEL, "stream": False, "messages": messages,
                          "options": {"temperature": temperature, "num_predict": max_tokens}},
                )
                if resp.status_code != 200:
                    return ""
                return resp.json().get("message", {}).get("content", "")
    except Exception as e:
        logger.warning(f"LLM complete failed: {e}")
        return ""


async def _extract_order_data(message: str, req: ChatRequest) -> dict | None:
    """Dùng LLM trích xuất món + thông tin đặt hàng từ message. Chạy song song với stream."""
    if not menu_rag.items:
        return None

    products_by_id = {item["id"]: item for item in menu_rag.items}
    menu_list = "\n".join(
        f"{item['id']}|{item['name']}|{item['price']:,}đ"
        for item in menu_rag.items
    )
    prompt = EXTRACT_PROMPT.format(message=message, menu_list=menu_list)

    try:
        raw = await _llm_complete([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=400)
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


async def _stream_llm(
    system: str,
    messages: list[dict],
    order_task: asyncio.Task | None = None,
    product_cards: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream LLM response (Groq hoặc Ollama), inject product_cards + order_form trước [DONE]."""
    all_messages = [{"role": "system", "content": system}] + messages

    async def _finish():
        if product_cards:
            yield f"data: {json.dumps({'type': 'product_cards', 'products': product_cards})}\n\n"
        if order_task is not None:
            try:
                order_data = await asyncio.wait_for(order_task, timeout=10.0)
                if order_data:
                    yield f"data: {json.dumps({'type': 'order_form', 'order': order_data})}\n\n"
            except asyncio.TimeoutError:
                logger.warning("Order extraction timed out")
            except Exception as e:
                logger.warning(f"Order task error: {e}")
        yield "data: [DONE]\n\n"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if USE_GROQ:
                payload = {"model": GROQ_MODEL, "messages": all_messages,
                           "temperature": 0.7, "max_tokens": 300, "stream": True}
                async with client.stream("POST", f"{GROQ_BASE_URL}/chat/completions",
                                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                                         json=payload) as resp:
                    if resp.status_code != 200:
                        yield f"data: {json.dumps({'error': 'Groq không phản hồi'})}\n\n"
                        return
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            async for chunk in _finish():
                                yield chunk
                            return
                        try:
                            token = json.loads(data)["choices"][0]["delta"].get("content", "")
                            if token:
                                yield f"data: {json.dumps({'token': token})}\n\n"
                        except (json.JSONDecodeError, KeyError):
                            continue
            else:
                payload = {"model": OLLAMA_MODEL, "stream": True, "messages": all_messages,
                           "options": {"temperature": 0.7, "num_predict": 300}}
                async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload) as resp:
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
                                async for c in _finish():
                                    yield c
                                return
                        except json.JSONDecodeError:
                            continue

    except httpx.ConnectError:
        err = "Groq không kết nối được." if USE_GROQ else "Ollama chưa chạy."
        yield f"data: {json.dumps({'error': err})}\n\n"
    except Exception as e:
        logger.error(f"LLM stream error: {e}")
        yield f"data: {json.dumps({'error': 'Đã xảy ra lỗi, vui lòng thử lại.'})}\n\n"


# ── Endpoints ────────────────────────────────────────────────

@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Chat với chatbot, trả về SSE stream. Hỗ trợ đặt hàng qua order_form event."""
    _enforce_rate_limit(request)
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Tin nhắn không được trống")
    if len(req.message) > 500:
        raise HTTPException(status_code=400, detail="Tin nhắn quá dài (tối đa 500 ký tự)")

    # Toàn bộ truy vấn DB nằm ở đây, trước khi StreamingResponse bắt đầu —
    # generator chỉ đọc dữ liệu đã lấy sẵn nên không giữ session qua stream.
    ensure_index_loaded(db)
    system = await _build_system_prompt(db, req.message)
    messages = [{"role": m.role, "content": m.content} for m in req.history[-6:]]
    messages.append({"role": "user", "content": req.message})

    # Product cards: chỉ hiện khi có kết quả liên quan (không fallback)
    relevant = await menu_rag.hybrid_search(db, req.message, top_k=4)
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
        _stream_llm(system, messages, order_task, product_cards),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/reload-menu")
async def reload_menu(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
    rebuild_all: bool = False,
):
    """Reload index + hot items từ DB, đồng thời nhúng các sản phẩm còn thiếu vector.

    `rebuild_all=true` nhúng lại toàn bộ menu — dùng khi đổi model hoặc số chiều.
    """
    embedded = await backfill_embeddings(db, only_missing=not rebuild_all)
    products = db.query(models.Product).filter(models.Product.is_active == 1).all()
    menu_rag.build_index(products)
    menu_rag.set_hot_items(compute_hot_items(db))
    return {
        "message": f"Đã reload {menu_rag.total} sản phẩm vào chatbot index.",
        "embedded": embedded,
    }


@router.get("/status")
def chat_status(db: Session = Depends(get_db)):
    """Kiểm tra trạng thái chatbot, LLM backend và độ phủ embedding."""
    total_active = db.query(models.Product).filter(models.Product.is_active == 1).count()
    with_vector = (
        db.query(models.Product)
        .filter(models.Product.is_active == 1, models.Product.embedding.isnot(None))
        .count()
    )
    return {
        "menu_items_indexed": menu_rag.total,
        "llm_backend": "groq" if USE_GROQ else "ollama",
        "model": GROQ_MODEL if USE_GROQ else OLLAMA_MODEL,
        "embedding_enabled": embedding_service.is_enabled(),
        "embedding_model": embedding_service.GEMINI_EMBED_MODEL,
        "embedding_dim": embedding_service.EMBED_DIM,
        "products_with_embedding": f"{with_vector}/{total_active}",
    }
