"""
MenuRAGService — TF-IDF search trên danh sách sản phẩm từ DB.
Load/rebuild index khi khởi động hoặc khi admin gọi reload.
"""
import logging
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class MenuRAGService:
    """In-memory TF-IDF index cho menu sản phẩm."""

    def __init__(self):
        self._items: list[dict] = []
        self._corpus: list[str] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None

    # ── Build / Reload ──────────────────────────────────────

    def build_index(self, products: list) -> None:
        """Nhận danh sách Product ORM objects, build TF-IDF index."""
        self._items = [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "description": p.description or "",
                "emoji": p.emoji or "☕",
            }
            for p in products
        ]

        if not self._items:
            logger.warning("MenuRAGService: không có sản phẩm nào trong DB.")
            return

        # Corpus: ghép các trường text để search
        self._corpus = [
            f"{item['name']} {item['category']} {item['description']}"
            for item in self._items
        ]

        # char_wb ngram bắt được substring tiếng Việt tốt hơn word tokenizer
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 4), min_df=1
        )
        self._matrix = self._vectorizer.fit_transform(self._corpus)
        logger.info(f"MenuRAGService: indexed {len(self._items)} sản phẩm.")

    # ── Search ──────────────────────────────────────────────

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        """Trả về top_k món phù hợp nhất với query."""
        if self._vectorizer is None or not self._items:
            return self._items[:top_k]  # fallback: trả đầu danh sách

        q_vec = self._vectorizer.transform([query.lower()])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Chỉ trả kết quả có điểm > 0 (có liên quan)
        results = [self._items[i] for i in top_indices if scores[i] > 0]
        # Nếu không tìm được gì, trả toàn bộ menu để LLM tự chọn
        return results if results else self._items

    # ── Format context cho LLM ──────────────────────────────

    def format_context(self, items: list[dict]) -> str:
        """Chuyển danh sách sản phẩm thành đoạn text cho system prompt."""
        if not items:
            return "Hiện chưa có thông tin thực đơn."

        lines = []
        for item in items:
            price_str = f"{item['price']:,}đ".replace(",", ".")
            lines.append(
                f"{item['emoji']} {item['name']} ({item['category']}) — {price_str}\n"
                f"   {item['description']}"
            )
        return "\n\n".join(lines)

    def all_items_context(self) -> str:
        """Toàn bộ menu dạng compact để nhúng vào system prompt."""
        return self.format_context(self._items)

    @property
    def total(self) -> int:
        return len(self._items)


# Singleton dùng chung toàn app
menu_rag = MenuRAGService()
