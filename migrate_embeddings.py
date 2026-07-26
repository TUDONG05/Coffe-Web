"""
Migration pgvector: bật extension, thêm cột embedding, tạo index HNSW và
nhúng toàn bộ sản phẩm đang bán.

Chạy một lần sau khi cấu hình GOOGLE_API_KEY:

    python migrate_embeddings.py            # chỉ nhúng sản phẩm còn thiếu vector
    python migrate_embeddings.py --rebuild  # nhúng lại tất cả (khi đổi model/số chiều)

Đổi GEMINI_EMBED_DIM thì phải xoá cột cũ trước, vì kiểu vector(N) cố định
số chiều và không tự ép kiểu được.
"""
import asyncio
import sys

from sqlalchemy import inspect, text

from highlands.database import SessionLocal, engine
from highlands.services.embedding_service import EMBED_DIM, GEMINI_EMBED_MODEL, is_enabled
from highlands.services.menu_rag_service import backfill_embeddings

REBUILD = "--rebuild" in sys.argv


def enable_extension() -> None:
    print("Bật extension pgvector...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    print("[OK] pgvector sẵn sàng")


def add_embedding_column() -> None:
    existing = {c["name"] for c in inspect(engine).get_columns("products")}
    if "embedding" in existing:
        print("[OK] products.embedding đã tồn tại, bỏ qua")
        return
    print(f"Thêm cột products.embedding vector({EMBED_DIM})...")
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE products ADD COLUMN embedding vector({EMBED_DIM})"))
        conn.commit()
    print("[OK] Đã thêm cột embedding")


def create_index() -> None:
    """Index HNSW cho cosine distance.

    Với vài chục sản phẩm thì Postgres vẫn quét tuần tự vì rẻ hơn; index chỉ
    phát huy khi menu lớn dần, nhưng tạo sẵn thì không phải migrate lại.
    """
    print("Tạo index HNSW (vector_cosine_ops)...")
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_products_embedding_hnsw "
            "ON products USING hnsw (embedding vector_cosine_ops)"
        ))
        conn.commit()
    print("[OK] Index sẵn sàng")


def backfill() -> None:
    if not is_enabled():
        print("[BỎ QUA] Chưa có GOOGLE_API_KEY — không nhúng được.")
        print("         Chatbot vẫn chạy bằng TF-IDF cho tới khi cấu hình key.")
        return

    scope = "toàn bộ" if REBUILD else "các sản phẩm còn thiếu vector"
    print(f"Nhúng {scope} bằng {GEMINI_EMBED_MODEL} ({EMBED_DIM} chiều)...")
    db = SessionLocal()
    try:
        count = asyncio.run(backfill_embeddings(db, only_missing=not REBUILD))
    finally:
        db.close()
    print(f"[OK] Đã nhúng {count} sản phẩm")


if __name__ == "__main__":
    enable_extension()
    add_embedding_column()
    create_index()
    backfill()
    print("[OK] Migration embedding hoàn tất")
