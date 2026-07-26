"""
DDL idempotent cho cột vector.

Tách riêng vì `Base.metadata.create_all()` chỉ tạo bảng còn thiếu, không
ALTER bảng đã tồn tại — nên DB đang chạy sẽ không tự có cột `embedding`.
Serverless không chạy được script CLI, do đó startup phải tự lo phần này.

Mọi câu lệnh ở đây đều IF NOT EXISTS nên gọi lại bao nhiêu lần cũng an toàn.
"""
import logging

from sqlalchemy import text

from highlands.services.embedding_service import EMBED_DIM

logger = logging.getLogger(__name__)


def ensure_vector_schema(engine, verbose: bool = False) -> bool:
    """Bật extension, thêm cột embedding và tạo index HNSW nếu chưa có.

    Trả False khi Postgres không có pgvector — ứng dụng vẫn chạy được,
    chỉ là chatbot rơi về thuần TF-IDF.
    """
    def log(msg: str) -> None:
        if verbose:
            print(msg)
        else:
            logger.info(msg)

    def run(label: str, sql: str) -> bool:
        """Mỗi câu chạy trong transaction riêng để một lỗi không kéo đổ phần còn lại."""
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            log(f"[OK] {label}")
            return True
        except Exception as e:
            msg = f"bỏ qua {label}: {e}"
            if verbose:
                print(f"[WARN] {msg}")
            else:
                logger.warning(msg)
            return False

    # Extension là điều kiện cần; hai câu sau sẽ trượt nếu bảng products
    # chưa được tạo (gọi trước create_all) và điều đó chấp nhận được.
    has_extension = run("extension pgvector", "CREATE EXTENSION IF NOT EXISTS vector")
    if not has_extension:
        return False

    run(
        f"cột products.embedding vector({EMBED_DIM})",
        f"ALTER TABLE products ADD COLUMN IF NOT EXISTS embedding vector({EMBED_DIM})",
    )
    run(
        "index HNSW",
        "CREATE INDEX IF NOT EXISTS ix_products_embedding_hnsw "
        "ON products USING hnsw (embedding vector_cosine_ops)",
    )
    return True
