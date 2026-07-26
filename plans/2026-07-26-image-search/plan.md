---
title: Tìm kiếm sản phẩm bằng hình ảnh — Phase 1
status: pending
created: 2026-07-26
brainstorm: ./brainstorm-product-image-search.md
---

# Plan — Tìm kiếm sản phẩm bằng hình ảnh (Phase 1)

Triển khai Phase 1 của lộ trình trong [brainstorm](./brainstorm-product-image-search.md). Ba phase dưới đây là **các bước bên trong Phase 1 đó**, không phải Phase 1/2/3 của lộ trình.

## Tóm tắt kỹ thuật

CLIP embedding + cosine similarity numpy. Jina CLIP v2, 512 chiều, `normalized: true` → cosine rút gọn thành tích vô hướng. 30 sản phẩm × 512 float ≈ 61KB. **Bundle Vercel tăng 0MB** (numpy đã có sẵn qua sklearn).

## Các phase

| # | Phase | File | Phụ thuộc |
|---|---|---|---|
| 01 | Embedding pipeline (schema, service, backfill) | [phase-01-embedding-pipeline.md](./phase-01-embedding-pipeline.md) | JINA_API_KEY |
| 02 | Search API (endpoint, rate limit, auto-embed) | [phase-02-search-api.md](./phase-02-search-api.md) | Phase 01 |
| 03 | Frontend (modal, camera, resize, lưới kết quả) | [phase-03-frontend-image-search.md](./phase-03-frontend-image-search.md) | Phase 02 |

## Phụ thuộc ngoài

- **`JINA_API_KEY`** — đăng ký tại jina.ai, không cần thẻ, 10M token free. Thêm vào `.env` local **và** Vercel env vars.
- **Bộ test 20 ảnh chụp thật** bằng điện thoại, mỗi ảnh gán nhãn `product_id` đúng. **Chuẩn bị trước khi code Phase 03** — không có nó thì không đo được gì.

## Tiêu chí nghiệm thu

| Tiêu chí | Ngưỡng | Cách đo |
|---|---|---|
| Recall top-3 | ≥80% | `scripts/eval_image_search.py` trên bộ 20 ảnh |
| Độ trễ p95 | ≤3s | Đo end-to-end từ lúc chọn ảnh tới lúc hiện kết quả |
| Bundle Vercel | không tăng | So sánh build output trước/sau |
| Thiếu `JINA_API_KEY` | tính năng tự ẩn, trang không sập | Xoá biến môi trường rồi tải lại trang |
| Admin upload ảnh mới | embedding tự sinh, không cần chạy script tay | Upload ảnh trong admin → tìm bằng chính ảnh đó |
| Mobile | nút 📷 mở được camera sau | Test trên điện thoại thật |

## Ranh giới phạm vi

**Trong phạm vi**: luồng tìm bằng ảnh, camera capture, nút "Món tương tự" ở PDP, script backfill, script eval.

**Ngoài phạm vi**: tích hợp chatbot (Phase 2 lộ trình), VLM re-rank (Phase 3 lộ trình), sửa bug upload 5MB vượt giới hạn Vercel ở `admin_products_router.py:211` (đã ghi nhận, xử lý riêng).

## Rollback

Toàn bộ thay đổi là **cộng thêm**: cột nullable, endpoint mới, nút UI mới. Rollback = gỡ nút 📷 khỏi navbar. Không có rủi ro mất dữ liệu, không đụng schema cũ, không đổi contract API hiện có.

## Câu hỏi chưa chốt

1. **Tham số `task` của Jina cho cặp ảnh-ảnh**: quy ước là `retrieval.query` cho ảnh truy vấn, `retrieval.passage` cho ảnh đã index. Với image-image có thể dùng chung một task lại tốt hơn. **Cần đo cả hai cách trên bộ test rồi mới chốt** (Phase 01, bước 5).
2. **Ngưỡng score để gán nhãn độ tin cậy** ("Rất khớp" / "Có thể là"): các con số trong Phase 03 là tạm, **phải hiệu chỉnh lại bằng số đo thật** sau khi chạy eval. Không hardcode theo cảm tính.
