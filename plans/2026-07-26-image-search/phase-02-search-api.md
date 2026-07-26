# Phase 02 — Search API

Mục tiêu: hai endpoint dùng được, và ảnh admin upload tự sinh embedding.

Phụ thuộc: Phase 01 xong, sanity check đạt.

## Files

| File | Loại |
|---|---|
| `highlands/rate_limit.py` | **mới** |
| `highlands/routers/products_router.py` | sửa |
| `highlands/routers/admin_products_router.py` | sửa |
| `highlands/routers/chatbot_router.py` | sửa (tuỳ chọn, dọn trùng lặp) |

---

## Bước 1 — Tách rate limiter dùng chung

`chatbot_router.py:91-103` đang có rate limiter in-memory. Endpoint mới cần đúng logic đó → tách ra `highlands/rate_limit.py` thay vì copy:

```python
def enforce_rate_limit(request: Request, *, key: str, max_hits: int, window: int = 60) -> None
```

`key` để tách quota theo từng endpoint (chat và tìm-bằng-ảnh không dùng chung bộ đếm).

Sau đó `chatbot_router.py` gọi hàm chung, xoá `_rate_store` / `_enforce_rate_limit` cục bộ. Đổi 3 dòng, rủi ro thấp, hết trùng lặp.

> ⚠️ Rate limiter in-memory **gần như vô dụng trên Vercel serverless** — mỗi lần gọi có thể rơi vào instance mới, bộ đếm reset. Hiện trạng của chatbot đã vậy rồi. Giữ nguyên cách làm cho nhất quán; coi đây là chặn nhầm lẫn chứ không phải chống lạm dụng. Muốn chặn thật thì cần Redis/Upstash — **ngoài phạm vi**.

## Bước 2 — Endpoint tìm bằng ảnh

`products_router.py`:

```
POST /api/products/search-by-image
  Content-Type: multipart/form-data
  file: UploadFile
```

Trình tự xử lý:

1. `enforce_rate_limit(request, key="img-search", max_hits=10)`
2. Nếu `not image_search_service.is_configured()` → **503** `"Tính năng tìm bằng ảnh chưa được cấu hình"`
3. Validate mime `{image/jpeg, image/png, image/webp}` → **400** (bám đúng danh sách ở `admin_products_router.py:206`)
4. Đọc bytes, chặn **> 2MB** → **400**. Client đã resize còn ~80KB; 2MB là biên an toàn, nằm dưới hẳn giới hạn body ~4.5MB của Vercel
5. Index chưa sẵn sàng → rebuild lazy từ DB (bọc cold start hụt); vẫn rỗng → **503**
6. `embed_image_bytes()` → lỗi/timeout Jina → **502** `"Không kết nối được dịch vụ nhận diện ảnh, vui lòng thử lại"`
7. `image_search.search(vec, top_k=5)` → lấy Product theo id, **tái dụng `_with_ratings()`** đã có trong file để kết quả có `avg_rating`/`review_count` giống mọi API sản phẩm khác
8. Trả về, mỗi phần tử thêm `"score": float`

Giữ nguyên thứ tự do `search()` trả về — **`query(...).filter(id.in_(...))` không bảo toàn thứ tự**, phải sắp lại theo score ở phía Python.

## Bước 3 — Endpoint món tương tự

```
GET /api/products/{product_id}/similar?limit=4
```

- Sản phẩm không có embedding → trả **`[]`** (200, không phải lỗi) → frontend tự ẩn khối
- Loại chính nó khỏi kết quả
- Chỉ lấy sản phẩm `is_active == 1`
- Cùng shape response với endpoint trên
- **Không gọi Jina** — chỉ tra ma trận có sẵn, nên miễn phí và nhanh

⚠️ Đặt route **sau** `GET /{product_id}` hoặc dùng đường dẫn không nhập nhằng. FastAPI khớp theo thứ tự khai báo — `/{product_id}` khai trước sẽ nuốt luôn `/similar` nếu đặt sai chỗ.

## Bước 4 — Tự sinh embedding khi admin upload

`admin_products_router.py`, trong `upload_product_image` sau dòng ~221 (`product.image_url = await upload_image(...)`):

```python
try:
    vec = await embed_image_url_or_bytes(product.image_url, content)
    product.image_embedding        = json.dumps([round(x, 6) for x in vec])
    product.image_embedding_source = product.image_url
except Exception as e:
    logger.warning("Không sinh được embedding cho sản phẩm %s: %s", product_id, e)
```

**Bắt buộc bọc try/except**: Jina lỗi thì upload ảnh vẫn phải thành công. Ảnh quan trọng hơn embedding — chạy backfill sau là bù được.

Vì đã có sẵn `content` (bytes) trong hàm, dùng luôn base64 thay vì bắt Jina đi tải URL — nhanh hơn và né được trường hợp Blob chưa kịp lan truyền (propagation).

Sau khi commit → `image_search.build_index()` lại. Instance khác vẫn giữ index cũ tới cold start kế tiếp — chấp nhận được, ảnh mới sẽ xuất hiện trễ chút.

## Validation

```bash
curl -F "file=@test.jpg" localhost:8000/api/products/search-by-image     # 200, 5 kết quả, score giảm dần
curl localhost:8000/api/products/1/similar                                # 200, 4 món, không có id=1
curl -F "file=@doc.pdf" localhost:8000/api/products/search-by-image       # 400
```

- Gửi ảnh của chính sản phẩm đã index → sản phẩm đó **phải đứng top-1**
- Bỏ `JINA_API_KEY` → 503, `/api/products` vẫn chạy bình thường
- Upload ảnh mới qua admin → tìm bằng chính ảnh đó ra đúng sản phẩm
- Ngắt mạng giả lập lỗi Jina → 502 với thông điệp tiếng Việt, không phải stack trace

## Rủi ro

| Rủi ro | Xử lý |
|---|---|
| Route `/similar` bị `/{product_id}` nuốt | Khai báo đúng thứ tự, có test curl |
| Thứ tự kết quả sai do SQL `IN` | Sắp lại theo score ở Python |
| Jina chậm → treo request | `timeout=20s` trên httpx, trả 502 khi quá hạn |
| Upload ảnh fail vì Jina lỗi | try/except quanh phần embedding, upload vẫn commit |
