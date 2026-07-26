"""
Đo độ chính xác tìm kiếm bằng hình ảnh trên bộ ảnh chụp thật.

Kết quả script này là căn cứ để:
  1. Xác nhận tiêu chí nghiệm thu (recall top-3 >= 80%)
  2. Chốt ngưỡng IMGS_SCORE_HIGH / IMGS_SCORE_MID trong templates/highlands-coffee.html
     (dựa trên score trung bình của khớp đúng vs khớp sai)

Chuẩn bị: tests/image-search-fixtures/manifest.csv
    image_path,expected_product_id
    photos/ca-phe-sua-da-01.jpg,1
    photos/latte-02.jpg,5

Đường dẫn ảnh tính tương đối so với vị trí file manifest.

Cách dùng:
    python scripts/eval_image_search.py
    python scripts/eval_image_search.py --manifest duong/dan/khac.csv
"""
import argparse
import asyncio
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from highlands.database import SessionLocal
from highlands import models
from highlands.services import image_search_service as svc
from highlands.services.image_search_service import image_search

DEFAULT_MANIFEST = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tests", "image-search-fixtures", "manifest.csv",
)


def _load_manifest(path: str) -> list[tuple[str, int]]:
    base = os.path.dirname(os.path.abspath(path))
    rows: list[tuple[str, int]] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            img = row["image_path"].strip()
            if not os.path.isabs(img):
                img = os.path.join(base, img)
            rows.append((img, int(row["expected_product_id"])))
    return rows


async def main(manifest_path: str) -> int:
    if not svc.is_configured():
        print("[LỖI] Thiếu JINA_API_KEY. Thêm vào .env rồi chạy lại.")
        return 1
    if not os.path.exists(manifest_path):
        print(f"[LỖI] Không tìm thấy manifest: {manifest_path}")
        print("Xem hướng dẫn định dạng ở docstring đầu file.")
        return 1

    cases = _load_manifest(manifest_path)
    if not cases:
        print("[LỖI] Manifest rỗng.")
        return 1

    db = SessionLocal()
    try:
        products = db.query(models.Product).filter(models.Product.is_active == 1).all()
        image_search.build_index(products)
        if not image_search.is_ready():
            print("[LỖI] Chưa có embedding nào. Chạy scripts/build_image_embeddings.py trước.")
            return 1

        names = {p.id: p.name for p in products}

        top1 = top3 = top5 = 0
        correct_scores: list[float] = []   # score của sản phẩm đúng
        wrong_scores: list[float] = []     # score của sản phẩm sai đứng đầu
        mistakes: list[str] = []
        errors: list[str] = []

        for path, expected in cases:
            label = os.path.basename(path)
            try:
                with open(path, "rb") as f:
                    vec = await svc.embed_image_bytes(f.read())
            except Exception as e:
                errors.append(f"{label}: {str(e)[:70]}")
                continue

            hits = image_search.search(vec, top_k=5)
            ranked = [pid for pid, _ in hits]
            by_id = dict(hits)

            if expected in ranked[:1]:
                top1 += 1
            if expected in ranked[:3]:
                top3 += 1
            if expected in ranked[:5]:
                top5 += 1

            if expected in by_id:
                correct_scores.append(by_id[expected])

            # Ghi lại trường hợp đoán sai để soi thủ công
            if ranked and ranked[0] != expected:
                wrong_scores.append(hits[0][1])
                got_name = names.get(ranked[0], f"#{ranked[0]}")
                exp_name = names.get(expected, f"#{expected}")
                exp_score = by_id.get(expected)
                exp_str = f"{exp_score:.2f}" if exp_score is not None else "ngoài top-5"
                mistakes.append(
                    f"  {label:30s} → đoán {got_name} ({hits[0][1]:.2f}), "
                    f"đúng là {exp_name} ({exp_str})"
                )

        n = len(cases) - len(errors)
        if n == 0:
            print("[LỖI] Không đánh giá được ảnh nào.")
            for e in errors:
                print(f"  {e}")
            return 1

        print(f"\nĐã đánh giá {n} ảnh")
        print(f"Top-1: {top1}/{n} ({top1 / n:.1%})")
        print(f"Top-3: {top3}/{n} ({top3 / n:.1%})   ← ngưỡng đạt là ≥80%")
        print(f"Top-5: {top5}/{n} ({top5 / n:.1%})")

        if correct_scores:
            avg_ok = sum(correct_scores) / len(correct_scores)
            print(f"\nScore trung bình khớp đúng: {avg_ok:.2f}")
        if wrong_scores:
            avg_bad = sum(wrong_scores) / len(wrong_scores)
            print(f"Score trung bình khớp sai:  {avg_bad:.2f}"
                  "     ← dùng để đặt IMGS_SCORE_HIGH / IMGS_SCORE_MID")

        if mistakes:
            print(f"\nSai {len(mistakes)} trường hợp:")
            for m in mistakes:
                print(m)

        if errors:
            print(f"\nLỗi đọc/embed {len(errors)} ảnh:")
            for e in errors:
                print(f"  {e}")

        return 0 if top3 / n >= 0.80 else 2
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.manifest)))
