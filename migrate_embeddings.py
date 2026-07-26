"""
Migration pgvector: bật extension, thêm cột embedding, tạo index HNSW và
nhúng toàn bộ sản phẩm đang bán.

TUỲ CHỌN — app tự làm đúng những việc này lúc khởi động, kể cả trên Vercel.
Script tồn tại để migrate chủ động trước khi deploy, hoặc để nhúng lại toàn bộ:

    python migrate_embeddings.py            # chỉ nhúng sản phẩm còn thiếu vector
    python migrate_embeddings.py --rebuild  # nhúng lại tất cả (khi đổi model/số chiều)

Đổi GEMINI_EMBED_DIM thì phải xoá cột cũ trước, vì kiểu vector(N) cố định
số chiều và không tự ép kiểu được.
"""
import asyncio
import sys

from highlands.database import SessionLocal, engine
from highlands.services.embedding_service import EMBED_DIM, GEMINI_EMBED_MODEL, is_enabled
from highlands.services.menu_rag_service import backfill_embeddings
from highlands.vector_schema import ensure_vector_schema

REBUILD = "--rebuild" in sys.argv


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
    if not ensure_vector_schema(engine, verbose=True):
        sys.exit(1)
    backfill()
    print("[OK] Migration embedding hoàn tất")
