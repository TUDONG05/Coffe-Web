"""
ImageSearchService — tìm sản phẩm bằng hình ảnh dùng CLIP embedding.

Embedding sinh bởi Jina CLIP v2 (API ngoài), so khớp bằng cosine similarity
trên ma trận numpy trong bộ nhớ. Với ~30 sản phẩm, một phép nhân ma trận
(30, 512) x (512,) tốn dưới 1ms — không cần vector database.

Vector được chuẩn hoá L2 nên cosine similarity rút gọn thành tích vô hướng.
"""
import base64
import json
import logging
import os

import httpx
import numpy as np

logger = logging.getLogger(__name__)

# ── Cấu hình Jina ───────────────────────────────────────────
JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_URL     = "https://api.jina.ai/v1/embeddings"
JINA_MODEL   = "jina-clip-v2"

# Matryoshka: cắt từ 1024 xuống 512 chiều — giảm nửa dung lượng,
# gần như không mất độ chính xác.
EMBED_DIM = 512
TIMEOUT   = 20.0

# Endpoint jina-clip-v2 hiện tại CHỈ chấp nhận task="retrieval.query" cho ảnh
# (xác nhận bằng gọi API thật: "retrieval.passage" và không truyền task đều
# hợp lệ về response nhưng "retrieval.passage" bị 422 — không có cặp bất đối
# xứng passage/query cho input ảnh như tài liệu chung của Jina mô tả cho text).
# Dùng chung một task cho cả ảnh index lẫn ảnh truy vấn.
TASK_QUERY = "retrieval.query"


def is_configured() -> bool:
    """True khi đã có JINA_API_KEY — dùng để tắt mềm tính năng khi thiếu key."""
    return bool(JINA_API_KEY)


# ── Gọi API ─────────────────────────────────────────────────

async def _embed(inputs: list[dict], task: str) -> list[list[float]]:
    """Gửi danh sách input tới Jina, trả về embedding theo đúng thứ tự đầu vào."""
    if not JINA_API_KEY:
        raise RuntimeError("JINA_API_KEY chưa được cấu hình")

    payload = {
        "model": JINA_MODEL,
        "dimensions": EMBED_DIM,
        "normalized": True,
        "embedding_type": "float",
        "task": task,
        "input": inputs,
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            JINA_URL,
            json=payload,
            headers={"Authorization": f"Bearer {JINA_API_KEY}"},
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Jina API lỗi {resp.status_code}: {resp.text[:200]}")

    data = resp.json().get("data", [])
    if len(data) != len(inputs):
        raise RuntimeError(f"Jina trả {len(data)} embedding cho {len(inputs)} đầu vào")

    # Sắp lại theo "index" — không tin thứ tự trả về của API.
    data.sort(key=lambda d: d.get("index", 0))
    return [d["embedding"] for d in data]


async def embed_image_urls(urls: list[str]) -> list[list[float]]:
    """Embed nhiều ảnh từ URL công khai (dùng khi index sản phẩm)."""
    return await _embed([{"image": u} for u in urls], TASK_QUERY)


async def embed_image_bytes(data: bytes, task: str = TASK_QUERY) -> list[float]:
    """Embed một ảnh từ bytes. Dùng cho ảnh người dùng upload (không có URL công khai)."""
    b64 = base64.b64encode(data).decode("ascii")
    vectors = await _embed([{"image": b64}], task)
    return vectors[0]


# ── Tiện ích vector ─────────────────────────────────────────

def normalize(vec: list[float] | np.ndarray) -> np.ndarray:
    """Chuẩn hoá L2. Jina đã trả vector chuẩn hoá sẵn nhưng làm lại cho chắc."""
    arr = np.asarray(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    return arr / norm if norm > 0 else arr


def serialize(vec: list[float] | np.ndarray) -> str:
    """Đóng gói vector thành JSON để lưu vào cột TEXT.

    Làm tròn 6 chữ số thập phân: giữ nguyên độ chính xác cosine ở mức
    có ý nghĩa, giảm khoảng 40% dung lượng lưu trữ.
    """
    return json.dumps([round(float(x), 6) for x in vec])


# ── Index trong bộ nhớ ──────────────────────────────────────

class ImageSearchService:
    """Ma trận embedding của toàn bộ sản phẩm có ảnh, giữ trong RAM."""

    def __init__(self):
        self._ids: list[int] = []          # product_id theo đúng thứ tự hàng ma trận
        self._matrix: np.ndarray | None = None   # (N, EMBED_DIM) float32, đã chuẩn hoá

    def build_index(self, products: list) -> None:
        """Nhận danh sách Product ORM, nạp những sản phẩm đã có embedding hợp lệ.

        Sản phẩm thiếu embedding hoặc JSON hỏng bị bỏ qua kèm cảnh báo —
        không raise, để một bản ghi lỗi không làm sập cả tính năng.
        """
        ids: list[int] = []
        rows: list[np.ndarray] = []

        for p in products:
            raw = getattr(p, "image_embedding", None)
            if not raw:
                continue
            try:
                vec = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                logger.warning("ImageSearch: embedding hỏng ở sản phẩm %s", p.id)
                continue
            if len(vec) != EMBED_DIM:
                logger.warning(
                    "ImageSearch: sản phẩm %s có %d chiều, cần %d",
                    p.id, len(vec), EMBED_DIM,
                )
                continue
            ids.append(p.id)
            rows.append(normalize(vec))

        if rows:
            self._ids = ids
            self._matrix = np.vstack(rows).astype(np.float32)
            logger.info("ImageSearch: đã index %d sản phẩm.", len(ids))
        else:
            self._ids = []
            self._matrix = None
            logger.warning("ImageSearch: không có sản phẩm nào có embedding.")

    def is_ready(self) -> bool:
        return self._matrix is not None and len(self._ids) > 0

    @property
    def total(self) -> int:
        return len(self._ids)

    def search(self, vec, top_k: int = 5) -> list[tuple[int, float]]:
        """Trả về [(product_id, score)] xếp giảm dần theo độ tương đồng."""
        if not self.is_ready():
            return []
        q = normalize(vec)
        scores = self._matrix @ q                      # cosine vì cả hai đã chuẩn hoá
        order = np.argsort(scores)[::-1][:top_k]
        return [(self._ids[i], float(scores[i])) for i in order]

    def search_similar(self, product_id: int, top_k: int = 4) -> list[tuple[int, float]]:
        """Món nhìn giống nhất với một sản phẩm đã index. Không gọi API ngoài."""
        if not self.is_ready() or product_id not in self._ids:
            return []
        idx = self._ids.index(product_id)
        # Lấy dư một kết quả rồi loại chính nó ra.
        hits = self.search(self._matrix[idx], top_k=top_k + 1)
        return [(pid, score) for pid, score in hits if pid != product_id][:top_k]


image_search = ImageSearchService()
