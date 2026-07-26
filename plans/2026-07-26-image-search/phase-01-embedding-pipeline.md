# Phase 01 — Embedding pipeline

Mục tiêu: mỗi sản phẩm có ảnh → có một vector 512 chiều trong DB, nạp được thành ma trận numpy để so khớp.

## Files

| File | Loại |
|---|---|
| `highlands/models.py` | sửa |
| `migrate_db.py` | sửa |
| `highlands/services/image_search_service.py` | **mới** |
| `scripts/build_image_embeddings.py` | **mới** |
| `highlands_app.py` | sửa |
| `.env.example` | sửa |

---

## Bước 1 — Schema

`highlands/models.py`, class `Product` (dòng ~43):

```python
image_embedding        = Column(Text, nullable=True)         # JSON array 512 float
image_embedding_source = Column(String(300), nullable=True)  # image_url lúc sinh embedding
```

`image_embedding_source` để backfill **idempotent**: bỏ qua sản phẩm mà ảnh không đổi → không đốt token vô ích khi chạy lại script.

`migrate_db.py`, thêm cạnh các dòng `add_column_if_missing` có sẵn:

```python
add_column_if_missing("products", "image_embedding",        "TEXT NULL")
add_column_if_missing("products", "image_embedding_source", "VARCHAR(300) NULL")
```

## Bước 2 — Service

`highlands/services/image_search_service.py` — soi gương cấu trúc `menu_rag_service.py` (singleton module-level, `build_index()`, `search()`).

**Hằng số**

```python
JINA_URL   = "https://api.jina.ai/v1/embeddings"
JINA_MODEL = "jina-clip-v2"
EMBED_DIM  = 512          # Matryoshka truncate từ 1024
TIMEOUT    = 20.0
```

**Hàm gọi API** (dùng `httpx.AsyncClient`, đã có trong requirements)

```python
def is_configured() -> bool          # bool(JINA_API_KEY)
async def _embed(inputs: list[dict], task: str) -> list[list[float]]
async def embed_image_url(url: str) -> list[float]              # task="retrieval.passage"
async def embed_image_bytes(data: bytes, mime: str) -> list[float]  # base64, task="retrieval.query"
```

Body gửi Jina:

```json
{
  "model": "jina-clip-v2",
  "dimensions": 512,
  "normalized": true,
  "embedding_type": "float",
  "task": "retrieval.passage",
  "input": [{"image": "<url hoặc base64>"}]
}
```

Header: `Authorization: Bearer $JINA_API_KEY`. Response OpenAI-compatible: `{"data":[{"index":0,"embedding":[...]}]}` — **sắp xếp lại theo `index`**, đừng tin thứ tự trả về.

`normalized: true` → vector đã chuẩn hoá L2, cosine rút gọn thành tích vô hướng. Vẫn chuẩn hoá lại một lần ở phía mình cho chắc (rẻ, và tránh phụ thuộc hành vi API).

**Lớp index**

```python
class ImageSearchService:
    _ids: list[int]              # product_id theo đúng thứ tự hàng ma trận
    _matrix: np.ndarray | None   # (N, 512) float32, đã chuẩn hoá

    def build_index(self, products) -> None    # ORM objects có image_embedding
    def is_ready(self) -> bool
    def search(self, vec, top_k=5) -> list[tuple[int, float]]
    def search_similar(self, product_id, top_k=4) -> list[tuple[int, float]]  # loại chính nó

image_search = ImageSearchService()
```

`search()` = `self._matrix @ vec` rồi `argsort` giảm dần. Với N=30 tốn dưới 1ms — **không cần thư viện nào khác**.

`build_index` bỏ qua sản phẩm có `image_embedding` null hoặc parse JSON lỗi, ghi log cảnh báo, **không raise**.

## Bước 3 — Nạp index lúc khởi động

`highlands_app.py`, trong startup hook có sẵn (dòng ~51, ngay cạnh `menu_rag.build_index`):

```python
image_search.build_index(products)
```

Dùng chung danh sách `products` đã query cho `menu_rag` — **không query lại DB**.

Startup hook đã bọc try/except sẵn (dòng ~56). Serverless cold start chạy lại hook này mỗi lần: 30 hàng, parse JSON ≈ vài chục ms, chấp nhận được.

Phòng khi index rỗng lúc request tới (DB chưa sẵn sàng lúc startup), router ở Phase 02 phải tự rebuild lazy — xem Phase 02.

## Bước 4 — Script backfill

`scripts/build_image_embeddings.py`:

1. Query sản phẩm `image_url IS NOT NULL`
2. Bỏ qua nếu `image_embedding_source == image_url` (đã có, ảnh không đổi) — trừ khi chạy với `--force`
3. **Batch 16 ảnh mỗi request** (Jina nhận nhiều input một lượt; free tier 100 RPM / 2 concurrent)
4. Truyền **thẳng `image_url`** cho Jina — ảnh đã ở trên Vercel Blob là URL công khai, không cần tải về base64
5. Ghi `image_embedding = json.dumps([round(x, 6) for x in vec])` và `image_embedding_source = image_url`
6. In tổng kết: đã sinh / bỏ qua / lỗi, và **liệt kê sản phẩm chưa có ảnh**

Làm tròn 6 chữ số thập phân giữ nguyên độ chính xác cosine mà giảm ~40% dung lượng TEXT (≈4.6KB/sản phẩm).

⚠️ Ở môi trường dev, `blob_service.py` trả về đường dẫn local `/static/images/...` — **không phải URL công khai, Jina không tải được**. Script phải phát hiện đường dẫn bắt đầu bằng `/` → đọc file từ đĩa rồi gửi base64.

## Bước 5 — Kiểm chứng và hiệu chỉnh

Trước khi sang Phase 02, chạy tay và xác nhận:

1. **Base64 đúng định dạng chưa** — Jina nhận base64 trần hay cần tiền tố data URI? Thử cả hai, chốt cái chạy được.
2. **`task` nào tốt hơn cho cặp ảnh-ảnh** — so `retrieval.query`+`retrieval.passage` (bất đối xứng) với dùng chung một task, đo trên vài ảnh test. Chốt rồi ghi lại lý do.
3. **Phân bố score thực tế** — cosine giữa ảnh chụp thật và ảnh sản phẩm đúng vs sản phẩm sai. Số này là đầu vào để đặt ngưỡng độ tin cậy ở Phase 03.
4. **Sanity check**: embed ảnh sản phẩm A rồi search → chính A phải đứng top-1 với score ≈ 1.0. Nếu không, pipeline sai.

## Validation

- `python migrate_db.py` chạy sạch, chạy lại lần hai vẫn sạch (idempotent)
- `python scripts/build_image_embeddings.py` → mọi sản phẩm có ảnh đều có embedding
- Chạy lại lần hai → báo "bỏ qua" toàn bộ, **không tốn token**
- Sanity check ở bước 5 đạt

## Rủi ro

| Rủi ro | Xử lý |
|---|---|
| Thiếu `JINA_API_KEY` | `is_configured()` trả False; script thoát sớm với thông báo rõ; app vẫn chạy bình thường |
| Jina rate limit (100 RPM) | Batch 16/request + tối đa 2 request đồng thời → 30 sản phẩm chỉ tốn 2 request |
| Ảnh dev là đường dẫn local | Phát hiện tiền tố `/` → đọc đĩa, gửi base64 (bước 4) |
| Ảnh trên Blob bị 404 | Bắt lỗi từng sản phẩm, ghi log, tiếp tục — **không dừng cả script** |
