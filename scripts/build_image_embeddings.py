"""
Sinh CLIP embedding cho ảnh sản phẩm, lưu vào cột products.image_embedding.

Chạy một lần sau khi migrate, hoặc chạy lại khi có nhiều ảnh mới.
Ảnh upload qua trang admin đã tự sinh embedding nên bình thường không cần chạy lại.

Cách dùng:
    python scripts/build_image_embeddings.py           # chỉ xử lý ảnh mới/đã đổi
    python scripts/build_image_embeddings.py --force   # sinh lại toàn bộ
"""
import asyncio
import os
import sys

# Cho phép chạy trực tiếp từ thư mục gốc dự án
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from highlands.database import SessionLocal
from highlands import models
from highlands.services import image_search_service as svc

# Jina free tier: 100 RPM, 2 request đồng thời. Gộp nhiều ảnh mỗi request
# để 30 sản phẩm chỉ tốn 2 request thay vì 30.
BATCH_SIZE = 16

STATIC_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"
)


def _is_local_path(url: str) -> bool:
    """Ở dev, blob_service trả về '/static/images/...' — Jina không tải được
    đường dẫn này, phải đọc file từ đĩa rồi gửi base64."""
    return url.startswith("/")


def _read_local(url: str) -> bytes:
    # '/static/images/products/1_abc.webp' -> '<project>/static/images/products/1_abc.webp'
    rel = url[len("/static/"):] if url.startswith("/static/") else url.lstrip("/")
    with open(os.path.join(STATIC_ROOT, rel), "rb") as f:
        return f.read()


async def _embed_product(product) -> list[float]:
    """Embed ảnh của một sản phẩm, tự chọn đường URL hay đường file local."""
    if _is_local_path(product.image_url):
        data = _read_local(product.image_url)
        return await svc.embed_image_bytes(data)
    vectors = await svc.embed_image_urls([product.image_url])
    return vectors[0]


async def main(force: bool = False) -> int:
    if not svc.is_configured():
        print("[LỖI] Thiếu JINA_API_KEY. Thêm vào .env rồi chạy lại.")
        return 1

    db = SessionLocal()
    try:
        products = db.query(models.Product).filter(
            models.Product.image_url.isnot(None),
            models.Product.image_url != "",
        ).all()

        no_image = db.query(models.Product).filter(
            (models.Product.image_url.is_(None)) | (models.Product.image_url == "")
        ).all()

        # Idempotent: bỏ qua sản phẩm mà ảnh không đổi kể từ lần sinh trước
        todo = products if force else [
            p for p in products
            if not p.image_embedding or p.image_embedding_source != p.image_url
        ]
        skipped = len(products) - len(todo)

        if not todo:
            print(f"Không có gì để làm. Đã bỏ qua {skipped} sản phẩm (ảnh không đổi).")
            _report_missing(no_image)
            return 0

        print(f"Đang sinh embedding cho {len(todo)} sản phẩm (bỏ qua {skipped})...")

        done = 0
        failed: list[tuple[int, str]] = []

        for start in range(0, len(todo), BATCH_SIZE):
            batch = todo[start:start + BATCH_SIZE]

            # Ảnh URL công khai gộp chung một request; ảnh local phải gửi lẻ.
            remote = [p for p in batch if not _is_local_path(p.image_url)]
            local  = [p for p in batch if _is_local_path(p.image_url)]

            if remote:
                try:
                    vectors = await svc.embed_image_urls([p.image_url for p in remote])
                    for p, vec in zip(remote, vectors):
                        p.image_embedding = svc.serialize(vec)
                        p.image_embedding_source = p.image_url
                        done += 1
                except Exception as e:
                    # Cả lô hỏng thì thử lại từng ảnh — một URL 404 không nên
                    # làm mất embedding của những ảnh còn lại trong lô.
                    print(f"  Lô lỗi ({e}), thử lại từng ảnh...")
                    for p in remote:
                        try:
                            p.image_embedding = svc.serialize(await _embed_product(p))
                            p.image_embedding_source = p.image_url
                            done += 1
                        except Exception as e2:
                            failed.append((p.id, str(e2)[:80]))

            for p in local:
                try:
                    p.image_embedding = svc.serialize(await _embed_product(p))
                    p.image_embedding_source = p.image_url
                    done += 1
                except Exception as e:
                    failed.append((p.id, str(e)[:80]))

            db.commit()
            print(f"  ...{min(start + BATCH_SIZE, len(todo))}/{len(todo)}")

        print(f"\n[OK] Đã sinh {done} embedding, bỏ qua {skipped}, lỗi {len(failed)}")
        for pid, err in failed:
            print(f"  [LỖI] sản phẩm {pid}: {err}")

        _report_missing(no_image)
        return 0
    finally:
        db.close()


def _report_missing(products: list) -> None:
    """Sản phẩm chưa có ảnh sẽ không bao giờ xuất hiện trong kết quả tìm bằng ảnh."""
    if not products:
        return
    print(f"\n[CẢNH BÁO] {len(products)} sản phẩm chưa có ảnh, sẽ không tìm được bằng ảnh:")
    for p in products:
        print(f"  - #{p.id} {p.name}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main(force="--force" in sys.argv)))
