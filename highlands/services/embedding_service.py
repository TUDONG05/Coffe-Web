"""
Gemini embedding client — sinh vector cho sản phẩm (document) và câu hỏi (query).

Dùng REST API nên không kéo theo torch/transformers, giữ được kích thước
function dưới giới hạn 250MB của Vercel serverless.

Model `gemini-embedding-001` trả về 3072 chiều mặc định; ta cắt xuống 768 chiều
qua `outputDimensionality` để cột pgvector và index HNSW gọn hơn. Google yêu cầu
tự chuẩn hoá L2 khi dùng số chiều khác 3072, nên `_l2_normalize` là bắt buộc.
"""
import asyncio
import logging
import os
import threading
from collections import OrderedDict
from typing import Optional

import httpx
import numpy as np

logger = logging.getLogger(__name__)

# ── Cấu hình ────────────────────────────────────────────────
GEMINI_API_KEY     = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
GEMINI_BASE_URL    = "https://generativelanguage.googleapis.com/v1beta"

# Đổi giá trị này bắt buộc phải migrate lại cột vector trong DB (kích thước cố định).
EMBED_DIM = int(os.getenv("GEMINI_EMBED_DIM", "768"))

# Embedding bất đối xứng: câu hỏi và tài liệu được nhúng bằng task type khác nhau.
TASK_DOCUMENT = "RETRIEVAL_DOCUMENT"
TASK_QUERY    = "RETRIEVAL_QUERY"

# Gemini giới hạn số request mỗi lần gọi batch.
_BATCH_LIMIT = 100
_TIMEOUT     = 20.0

# Cache vector câu hỏi: user hay hỏi lặp ("menu có gì", "gợi ý món ngon").
_QUERY_CACHE_MAX = 256
_query_cache: "OrderedDict[str, list[float]]" = OrderedDict()
_cache_lock = threading.Lock()


def is_enabled() -> bool:
    """Có API key thì mới bật embedding; không có thì hệ thống rơi về TF-IDF."""
    return bool(GEMINI_API_KEY)


def build_product_text(name: str, category: str, description: str) -> str:
    """Ghép các trường sản phẩm thành đoạn text đem đi nhúng.

    Dùng chung cho cả lúc backfill và lúc admin sửa sản phẩm để vector
    luôn được sinh từ cùng một định dạng.
    """
    return f"{name}. Loại: {category}. {description or ''}".strip()


# ── Nội bộ ──────────────────────────────────────────────────

def _l2_normalize(values: list[float]) -> list[float]:
    """Chuẩn hoá L2. Bắt buộc khi cắt chiều xuống dưới 3072."""
    vec = np.asarray(values, dtype=np.float32)
    norm = float(np.linalg.norm(vec))
    if norm == 0.0:
        return vec.tolist()
    return (vec / norm).tolist()


def _extract_vectors(payload: dict, expected: int) -> Optional[list[list[float]]]:
    """Đọc vector từ response.

    API trả về `embeddings` (mảng) cho batch và `embedding` (object) cho
    request đơn lẻ, nên chấp nhận cả hai dạng.
    """
    raw = payload.get("embeddings")
    if raw is None:
        single = payload.get("embedding")
        raw = [single] if single else None
    if not raw or len(raw) != expected:
        logger.warning(
            f"Embedding response không khớp: nhận {len(raw) if raw else 0}, cần {expected}"
        )
        return None

    vectors = []
    for entry in raw:
        values = (entry or {}).get("values")
        if not values:
            return None
        vectors.append(_l2_normalize(values))
    return vectors


async def _post_batch(client: httpx.AsyncClient, texts: list[str], task_type: str):
    """Gọi batchEmbedContents cho tối đa _BATCH_LIMIT đoạn text."""
    model_path = f"models/{GEMINI_EMBED_MODEL}"
    body = {
        "requests": [
            {
                "model": model_path,
                "content": {"parts": [{"text": t}]},
                "taskType": task_type,
                "outputDimensionality": EMBED_DIM,
            }
            for t in texts
        ]
    }
    resp = await client.post(
        f"{GEMINI_BASE_URL}/{model_path}:batchEmbedContents",
        params={"key": GEMINI_API_KEY},
        json=body,
    )
    if resp.status_code != 200:
        logger.warning(f"Gemini embed lỗi {resp.status_code}: {resp.text[:200]}")
        return None
    return _extract_vectors(resp.json(), expected=len(texts))


# ── API công khai ───────────────────────────────────────────

async def embed_texts(texts: list[str], task_type: str = TASK_DOCUMENT) -> Optional[list[list[float]]]:
    """Nhúng nhiều đoạn text. Trả None nếu thiếu key hoặc gọi API thất bại."""
    if not texts:
        return []
    if not is_enabled():
        logger.warning("Chưa cấu hình GOOGLE_API_KEY — bỏ qua embedding.")
        return None

    chunks = [texts[i:i + _BATCH_LIMIT] for i in range(0, len(texts), _BATCH_LIMIT)]
    results: list[list[float]] = []
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for chunk in chunks:
                vectors = await _post_batch(client, chunk, task_type)
                if vectors is None:
                    return None
                results.extend(vectors)
    except Exception as e:
        logger.warning(f"Gọi Gemini embedding thất bại: {e}")
        return None
    return results


async def embed_document(text: str) -> Optional[list[float]]:
    """Nhúng một sản phẩm."""
    vectors = await embed_texts([text], TASK_DOCUMENT)
    return vectors[0] if vectors else None


async def embed_query(text: str) -> Optional[list[float]]:
    """Nhúng câu hỏi của user, có cache LRU để giảm latency và chi phí."""
    key = text.strip().lower()
    if not key:
        return None

    with _cache_lock:
        cached = _query_cache.get(key)
        if cached is not None:
            _query_cache.move_to_end(key)
            return cached

    vectors = await embed_texts([key], TASK_QUERY)
    if not vectors:
        return None
    vector = vectors[0]

    with _cache_lock:
        _query_cache[key] = vector
        if len(_query_cache) > _QUERY_CACHE_MAX:
            _query_cache.popitem(last=False)
    return vector


def embed_document_sync(text: str) -> Optional[list[float]]:
    """Bản đồng bộ cho script migration (chạy ngoài event loop)."""
    return asyncio.run(embed_document(text))


def embed_texts_sync(texts: list[str], task_type: str = TASK_DOCUMENT) -> Optional[list[list[float]]]:
    """Bản đồng bộ cho script migration (chạy ngoài event loop)."""
    return asyncio.run(embed_texts(texts, task_type))
