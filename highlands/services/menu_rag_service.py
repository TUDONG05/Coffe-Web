"""
MenuRAGService — tìm kiếm lai (hybrid) trên danh sách sản phẩm.

Hai nhánh bổ trợ nhau:
  - Semantic: vector Gemini lưu trong cột pgvector, bắt được ý nghĩa
    ("đồ uống mát cho mùa hè" → trà đào, đá xay).
  - Lexical: TF-IDF char n-gram in-memory, bắt được tên món gõ sai hoặc
    thiếu dấu ("caphe sua" → Cà Phê Sữa Đá).

Điểm cuối = ALPHA * semantic + (1 - ALPHA) * lexical. Khi chưa cấu hình
GOOGLE_API_KEY hoặc Gemini lỗi, hệ thống tự rơi về thuần TF-IDF.
"""
import logging
import os
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sqlalchemy.orm import Session

from highlands.services import embedding_service

logger = logging.getLogger(__name__)

# Trọng số nhánh semantic. Ngưỡng điểm để hiện product card.
# Cả hai nên được tinh chỉnh lại theo dữ liệu thật sau khi chạy.
HYBRID_ALPHA     = float(os.getenv("RAG_HYBRID_ALPHA", "0.7"))
HYBRID_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.38"))

# Số ứng viên lấy từ pgvector trước khi trộn điểm với TF-IDF.
_CANDIDATE_K = 20


RECOMMEND_KEYWORDS = [
    "gợi ý", "recommend", "đề xuất", "nên uống", "nên dùng", "nên ăn",
    "hot", "bán chạy", "nổi tiếng", "phổ biến", "best seller", "bestseller",
    "ngon nhất", "ngon", "đặc biệt", "thử xem", "thử cái gì", "muốn thử",
    "không biết chọn", "giúp chọn", "chọn gì", "uống gì", "ăn gì",
]


class MenuRAGService:
    """In-memory TF-IDF index cho menu sản phẩm."""

    def __init__(self):
        self._items: list[dict] = []
        self._by_id: dict[int, dict] = {}
        self._corpus: list[str] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None
        self._hot_items: list[dict] = []  # top-selling products, set externally

    @property
    def items(self) -> list[dict]:
        """Menu đang index. Chỉ để đọc — build_index() mới là nơi thay đổi."""
        return self._items

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
                "image_url": p.image_url or "",
            }
            for p in products
        ]

        self._by_id = {item["id"]: item for item in self._items}

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
                f"{item['name']} ({item['category']}) — {price_str}\n"
                f"   {item['description']}"
            )
        return "\n\n".join(lines)

    def set_hot_items(self, items: list[dict]) -> None:
        """Lưu danh sách sản phẩm bán chạy để dùng làm fallback."""
        self._hot_items = items

    def search_relevant(self, query: str, top_k: int = 4, min_score: float = 0.20) -> list[dict]:
        """Trả về top_k sản phẩm liên quan (score >= min_score).
        Fallback về hot_items nếu query chứa từ khoá gợi ý và không khớp sản phẩm nào."""
        if self._vectorizer is None or not self._items:
            return []
        q_vec = self._vectorizer.transform([query.lower()])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [self._items[i] for i in top_indices if scores[i] >= min_score]
        if results:
            return results
        # Fallback: nếu câu hỏi có từ gợi ý/hot thì trả top bán chạy
        q_lower = query.lower()
        if any(kw in q_lower for kw in RECOMMEND_KEYWORDS):
            return self._hot_items[:top_k] or self._items[:top_k]
        return []

    # ── Hybrid search (semantic + lexical) ──────────────────

    def tfidf_scores(self, query: str) -> dict[int, float]:
        """Điểm TF-IDF của mọi sản phẩm, khoá theo product_id."""
        if self._vectorizer is None or not self._items:
            return {}
        q_vec = self._vectorizer.transform([query.lower()])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        return {item["id"]: float(scores[i]) for i, item in enumerate(self._items)}

    async def semantic_scores(self, db: Session, query: str) -> dict[int, float]:
        """Điểm cosine từ pgvector. Trả dict rỗng nếu embedding không khả dụng."""
        if not embedding_service.is_enabled():
            return {}

        q_vec = await embedding_service.embed_query(query)
        if q_vec is None:
            return {}

        from highlands import models

        try:
            distance = models.Product.embedding.cosine_distance(q_vec)
            rows = (
                db.query(models.Product.id, distance.label("distance"))
                .filter(
                    models.Product.is_active == 1,
                    models.Product.embedding.isnot(None),
                )
                .order_by(distance)
                .limit(_CANDIDATE_K)
                .all()
            )
        except Exception as e:
            logger.warning(f"pgvector search lỗi, rơi về TF-IDF: {e}")
            return {}

        # cosine_distance ∈ [0, 2] → similarity = 1 - distance
        return {row.id: 1.0 - float(row.distance) for row in rows}

    async def hybrid_search(
        self,
        db: Session,
        query: str,
        top_k: int = 4,
        min_score: float = HYBRID_MIN_SCORE,
    ) -> list[dict]:
        """Trộn điểm semantic và lexical, trả top_k sản phẩm vượt ngưỡng."""
        lexical = self.tfidf_scores(query)
        semantic = await self.semantic_scores(db, query)

        if not semantic:
            # Không có embedding — giữ nguyên hành vi TF-IDF cũ.
            return self.search_relevant(query, top_k=top_k)

        combined: dict[int, float] = {}
        for pid in set(semantic) | set(lexical):
            combined[pid] = (
                HYBRID_ALPHA * semantic.get(pid, 0.0)
                + (1.0 - HYBRID_ALPHA) * lexical.get(pid, 0.0)
            )

        ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)
        results = [
            self._by_id[pid]
            for pid, score in ranked[:top_k]
            if score >= min_score and pid in self._by_id
        ]
        if results:
            return results

        # Không món nào vượt ngưỡng: nếu là câu xin gợi ý thì trả món bán chạy.
        if any(kw in query.lower() for kw in RECOMMEND_KEYWORDS):
            return self._hot_items[:top_k] or self._items[:top_k]
        return []

    async def hybrid_context(self, db: Session, query: str, top_k: int = 6) -> str:
        """Context cho system prompt — luôn có nội dung để LLM không bị bí.

        Ngưỡng nới lỏng so với product card, và khi không khớp gì thì đưa
        toàn bộ menu (30 món vẫn vừa context window).
        """
        matched = await self.hybrid_search(db, query, top_k=top_k, min_score=0.0)
        return self.format_context(matched or self._items)

    def all_items_context(self) -> str:
        """Toàn bộ menu dạng compact để nhúng vào system prompt."""
        return self.format_context(self._items)

    @property
    def total(self) -> int:
        return len(self._items)


def compute_hot_items(db: Session, top_k: int = 8) -> list[dict]:
    """Tính top sản phẩm bán chạy từ OrderItem (import lazy để tránh circular)."""
    from sqlalchemy import func
    from highlands import models

    rows = (
        db.query(models.OrderItem.product_id, func.sum(models.OrderItem.quantity).label("total"))
        .group_by(models.OrderItem.product_id)
        .order_by(func.sum(models.OrderItem.quantity).desc())
        .limit(top_k)
        .all()
    )
    if not rows:
        return []
    hot_ids = {r.product_id for r in rows}
    products = (
        db.query(models.Product)
        .filter(models.Product.id.in_(hot_ids), models.Product.is_active == 1)
        .all()
    )
    id_order = {r.product_id: i for i, r in enumerate(rows)}
    products.sort(key=lambda p: id_order.get(p.id, 999))
    return [
        {"id": p.id, "name": p.name, "category": p.category,
         "price": p.price, "description": p.description or "",
         "image_url": p.image_url or ""}
        for p in products
    ]


def ensure_index_loaded(db: Session) -> None:
    """Dựng index nếu process này chưa có (cold start serverless).

    Trên Vercel mỗi instance là một process riêng và không có gì bảo đảm
    startup event đã chạy, nên request đầu tiên phải tự lo.
    """
    if menu_rag.total > 0:
        return
    from highlands import models

    try:
        products = db.query(models.Product).filter(models.Product.is_active == 1).all()
        if products:
            menu_rag.build_index(products)
            menu_rag.set_hot_items(compute_hot_items(db))
    except Exception as e:
        logger.warning(f"Không dựng được menu index: {e}")


async def sync_product_embedding(db: Session, product) -> bool:
    """Sinh lại vector cho một sản phẩm và lưu vào DB.

    Gọi sau mỗi lần admin thêm/sửa sản phẩm để chatbot không tư vấn menu cũ.
    Trả False khi embedding không khả dụng — sản phẩm vẫn tìm được qua TF-IDF.
    """
    text = embedding_service.build_product_text(
        product.name, product.category, product.description or ""
    )
    vector = await embedding_service.embed_document(text)
    if vector is None:
        logger.warning(f"Không sinh được embedding cho sản phẩm #{product.id}")
        return False

    product.embedding = vector
    db.commit()
    return True


async def backfill_embeddings(db: Session, only_missing: bool = True) -> int:
    """Nhúng các sản phẩm đang thiếu vector. Trả về số sản phẩm đã cập nhật."""
    from highlands import models

    query = db.query(models.Product).filter(models.Product.is_active == 1)
    if only_missing:
        query = query.filter(models.Product.embedding.is_(None))
    products = query.all()
    if not products:
        return 0

    texts = [
        embedding_service.build_product_text(p.name, p.category, p.description or "")
        for p in products
    ]
    vectors = await embedding_service.embed_texts(texts, embedding_service.TASK_DOCUMENT)
    if vectors is None:
        logger.warning("Backfill embedding thất bại — giữ nguyên dữ liệu cũ.")
        return 0

    for product, vector in zip(products, vectors):
        product.embedding = vector
    db.commit()
    return len(products)


# Singleton dùng chung toàn app
menu_rag = MenuRAGService()
