"""
Chatbot router — POST /api/chat (SSE streaming qua Ollama local).
RAG: TF-IDF search trên Product DB, inject context vào system prompt.
"""
import json
import logging
import os
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from highlands import models
from highlands.database import get_db
from highlands.services.menu_rag_service import menu_rag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chatbot"])

# ── Cấu hình Ollama ─────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

SYSTEM_PROMPT_TEMPLATE = """Bạn là trợ lý tư vấn thực đơn thân thiện của Highlands Coffee.

NHIỆM VỤ:
- Tư vấn, giới thiệu các món trong thực đơn
- Giải đáp về giá, kích thước, thành phần, hương vị
- Gợi ý món phù hợp với sở thích hoặc dịp (buổi sáng, ăn kèm, không cà phê,...)
- Hỗ trợ khách lựa chọn để đặt món

GIỚI HẠN:
- CHỈ trả lời trong phạm vi thực đơn và dịch vụ Highlands Coffee
- Nếu hỏi ngoài phạm vi, trả lời: "Xin lỗi, tôi chỉ có thể tư vấn về thực đơn của Highlands Coffee ạ 😊"
- Không đưa lời khuyên y tế, chính trị hay chủ đề không liên quan

PHONG CÁCH:
- Thân thiện, nhiệt tình như nhân viên phục vụ thực thụ
- Trả lời bằng tiếng Việt, ngắn gọn (dưới 120 từ)
- Dùng emoji phù hợp ☕🧋🍞

THỰC ĐƠN LIÊN QUAN:
{menu_context}
"""


# ── Schemas ─────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


# ── Helpers ─────────────────────────────────────────────────

def _build_system_prompt(query: str) -> str:
    """RAG: tìm món liên quan, build system prompt với context."""
    matched = menu_rag.search(query, top_k=4)
    context = menu_rag.format_context(matched)
    return SYSTEM_PROMPT_TEMPLATE.format(menu_context=context)


async def _stream_ollama(system: str, messages: list[dict]) -> AsyncGenerator[str, None]:
    """Gọi Ollama /api/chat với stream=True, yield SSE data chunks."""
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
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield f"data: {json.dumps({'token': token})}\n\n"
                        if chunk.get("done"):
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
async def chat_stream(req: ChatRequest):
    """Chat với chatbot, trả về SSE stream."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Tin nhắn không được trống")
    if len(req.message) > 500:
        raise HTTPException(status_code=400, detail="Tin nhắn quá dài (tối đa 500 ký tự)")

    system = _build_system_prompt(req.message)
    messages = [{"role": m.role, "content": m.content} for m in req.history[-6:]]
    messages.append({"role": "user", "content": req.message})

    return StreamingResponse(
        _stream_ollama(system, messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # tắt Nginx buffering
        },
    )


@router.post("/reload-menu")
def reload_menu(db: Session = Depends(get_db)):
    """Reload TF-IDF index từ DB (gọi sau khi admin thêm/sửa sản phẩm)."""
    products = db.query(models.Product).filter(models.Product.is_active == 1).all()
    menu_rag.build_index(products)
    return {"message": f"Đã reload {menu_rag.total} sản phẩm vào chatbot index."}


@router.get("/status")
def chat_status():
    """Kiểm tra trạng thái chatbot và Ollama."""
    return {
        "menu_items_indexed": menu_rag.total,
        "ollama_url": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL,
    }
