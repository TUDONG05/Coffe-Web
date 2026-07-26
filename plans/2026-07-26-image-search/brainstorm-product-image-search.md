# Brainstorm — Tìm kiếm sản phẩm bằng hình ảnh

- **Ngày**: 2026-07-26
- **Dự án**: Tu's Coffee Web (FastAPI + Vanilla JS SPA, PostgreSQL, Vercel serverless)
- **Trạng thái**: Đã chốt thiết kế, chờ lập kế hoạch triển khai
- **Chế độ**: brainstorm mặc định (không `--html`, không `--wiki`)

---

## 1. Bài toán

Khách muốn **nhận diện món trong menu từ ảnh**: chụp/upload ảnh một ly đồ uống → hệ thống tìm đúng món đó trong 30 sản phẩm để đặt hàng nhanh. Đây là bài toán *recognition trên tập đóng*, không phải gợi ý ngữ nghĩa mở.

### Ràng buộc đã xác định

| Ràng buộc | Giá trị | Hệ quả |
|---|---|---|
| Hạ tầng | Vercel serverless Python (`@vercel/python`) | Giới hạn cứng 250MB bundle → **loại bỏ torch/transformers/CLIP local** |
| Bundle hiện tại | sklearn + numpy + scipy ≈ 100MB | Không còn dư địa cho model nặng |
| Quy mô dữ liệu | ~30 sản phẩm, 5 danh mục | **Không cần vector DB** — cosine 30 vector bằng numpy <1ms |
| Ảnh sản phẩm | >80% sản phẩm có `image_url` | Mở khoá hướng so khớp ảnh-với-ảnh (CLIP) |
| API bên thứ ba | Chấp nhận, ưu tiên free tier | Query embedding gọi API ngoài |
| Body limit Vercel | ~4.5MB/request | Bắt buộc resize ảnh phía client |

---

## 2. Các hướng đã đánh giá

### A. VLM đọc ảnh + inject menu (Groq llama-4-scout / Gemini Flash)
- **+** 0MB bundle, tái dụng `chatbot_router.py`, không cần ảnh sản phẩm nào
- **+** Effort thấp nhất: 1 endpoint + 1 modal
- **−** Không phải "tìm kiếm bằng hình ảnh" đúng nghĩa — là VLM đoán tên món
- **−** Kết quả không định danh, có thể hallucinate, khó giải thích trong báo cáo
- → **Loại làm giải pháp chính** (giữ lại làm tầng re-rank tuỳ chọn ở Phase 3)

### B. CLIP embedding + cosine similarity ✅ **ĐƯỢC CHỌN**
- **+** Đúng bản chất image retrieval: ảnh và ảnh so khớp trong cùng không gian vector
- **+** 0MB bundle (numpy đã có), deterministic, giải thích được
- **+** Ma trận embedding tái dụng được cho "món tương tự" mà không tốn thêm API call
- **−** Phụ thuộc API ngoài cho query embedding
- **−** Cần migration + script backfill + hook reindex khi admin đổi ảnh

### C. Self-host CLIP qua onnxruntime
- **−** onnxruntime ~50MB + CLIP ViT-B/32 quantized ~90MB + sklearn stack ~100MB → **vượt 250MB, bất khả thi trên Vercel**
- **−** Cold start 5-10s, cần tách microservice riêng
- → Loại theo ràng buộc hạ tầng

### D. Color histogram / classic CV thuần numpy
- **−** Độ chính xác thực tế rất kém: ảnh chụp trong quán khác hẳn ảnh studio về ánh sáng và nền
- → Loại. Không dùng cả làm fallback (thà báo lỗi rõ ràng còn hơn trả kết quả sai)

---

## 3. So sánh provider embedding (verify ngày 2026-07-26)

| Provider | Free tier | Chiều | Đánh giá |
|---|---|---|---|
| **Jina CLIP v2** ✅ | 10M tokens, không cần thẻ, 100 RPM / 100K TPM, 2 concurrent | 64–1024 (Matryoshka) | Ảnh 512×512 ≈ 1K tokens → **~10.000 lượt tìm miễn phí**. Token free ghi rõ **phi thương mại** |
| Cohere Embed v4 | Trial key **1.000 calls/tháng**, 2.000 inputs/min | 1536 | Trần tháng quá chật cho traffic thật |
| Groq Vision | 14.400 req/ngày, key đã có sẵn | — | Không phải embedding; llama-4-scout còn ở trạng thái Preview |

**Chốt: Jina CLIP v2, cắt xuống 512 chiều.** Matryoshka cho phép truncate mà gần như không mất chất lượng — giảm nửa dung lượng lưu trữ và nửa chi phí tính toán.

> ⚠️ **Lưu ý license**: 10M token miễn phí của Jina dành cho mục đích phi thương mại. Phù hợp đồ án/portfolio. Nếu vận hành bán hàng thật cần mua token trả phí.

---

## 4. Thiết kế được chốt

### Luồng dữ liệu

```
[User chụp/chọn ảnh]
      ↓ resize canvas 512×512 phía client  (~80KB thay vì 4MB)
[POST /api/products/search-by-image]
      ↓ validate mime + size, rate-limit theo IP
[embed_image() → Jina CLIP v2]  → vector 512 chiều đã chuẩn hoá
      ↓
[cosine vs ma trận 30×512 nạp từ DB]  → <1ms numpy
      ↓
[top-5 kèm score] → lưới sản phẩm, user tự chọn
```

### Thay đổi theo file

| File | Thay đổi |
|---|---|
| `highlands/models.py` | `Product.image_embedding = Column(Text, nullable=True)` — JSON array |
| `migrate_db.py` | `add_column_if_missing("products", "image_embedding", "TEXT NULL")` |
| `highlands/services/image_search_service.py` | **Mới** — soi gương `menu_rag_service.py`: singleton, `build_index()`, `search()`, lazy-load |
| `highlands/routers/products_router.py` | Thêm `POST /api/products/search-by-image` + `GET /{id}/similar` |
| `highlands/routers/admin_products_router.py` | Sau `upload_product_image` (dòng ~221) → tự sinh embedding cho ảnh mới |
| `scripts/build_image_embeddings.py` | **Mới** — backfill toàn bộ sản phẩm, chạy một lần |
| `templates/highlands-coffee.html` | Nút 📷 cạnh 🔍 trong `nav-search-wrap` (dòng 34-43), modal, resize canvas, lưới kết quả; nút "Món tương tự" trong PDP |
| `static/css/main.css` | Style modal upload + lưới kết quả |
| `.env.example` | `JINA_API_KEY=` |

### Quyết định kỹ thuật và lý do

- **Lưu embedding ở cột `TEXT` trên bảng `products`**, không dùng pgvector, không tách bảng riêng. Mỗi sản phẩm một ảnh → quan hệ 1-1, cột là đủ. 30×512 float ≈ 61KB toàn bộ.
- **Nạp ma trận theo pattern singleton của `menu_rag_service.py`** để đồng nhất với code có sẵn. Cold start serverless chỉ tốn 1 query + parse JSON ≈ vài chục ms.
- **Resize phía client bằng canvas**, không resize ở server. Ba lợi ích cùng lúc: né giới hạn body ~4.5MB của Vercel, giảm payload ~50 lần, và Jina đằng nào cũng xử lý ở 512×512.
- **Không lưu ảnh user lên Blob** — chỉ giữ trong RAM rồi bỏ. Tốt cho quyền riêng tư và không phát sinh chi phí lưu trữ.
- **Chuẩn hoá vector tường minh** trước khi lưu và trước khi so khớp, để cosine rút gọn thành tích vô hướng.

---

## 5. Rủi ro

**1. Domain gap — rủi ro lớn nhất.** Ảnh sản phẩm là ảnh marketing/studio; user chụp bằng điện thoại trong quán với ánh sáng và nền hoàn toàn khác. CLIP tương đối bền với biến thiên này nhưng kỳ vọng thực tế nên đặt ở **top-1 ~50-65%, top-3 ~80-85%**.

**2. Các món gần như bất khả phân biệt qua ảnh.** Latte / Cappuccino / Cà Phê Sữa Đá đều là ly chất lỏng nâu-trắng. Đây là giới hạn vật lý của bài toán, không phải lỗi kỹ thuật. Không có giải pháp nào khắc phục được hoàn toàn.

**3. Hệ quả UX bắt buộc từ (1) và (2).** Không auto-nhảy vào một sản phẩm. Phải hiện **lưới top-5 để user tự chọn**. Với recall top-3 ~85%, thiết kế này biến điểm yếu độ chính xác thành trải nghiệm bình thường.

**4. Phụ thuộc API ngoài.** Khi Jina lỗi hoặc hết quota: báo lỗi rõ ràng bằng tiếng Việt và hướng người dùng sang tìm kiếm text. Tuyệt đối không trả kết quả rác im lặng.

**5. Sản phẩm chưa có ảnh sẽ vắng mặt khỏi kết quả.** Cần thể hiện rõ trong trang quản trị để admin biết món nào chưa được index.

**6. Bug tiềm ẩn phát hiện khi scout** (ngoài phạm vi, nhưng nên biết): `admin_products_router.py:211` cho phép upload ảnh tới 5MB, **vượt giới hạn body ~4.5MB của Vercel serverless** — upload ảnh lớn nhiều khả năng đang fail trên production.

---

## 6. Tiêu chí nghiệm thu

- Upload ảnh một món có trong menu → sản phẩm đúng nằm trong **top-3** ở ≥80% trường hợp, đo trên bộ test **20 ảnh chụp thật bằng điện thoại**
- Độ trễ p95 từ lúc bấm chọn ảnh tới lúc hiện kết quả ≤ **3 giây**
- Bundle Vercel **không tăng** (kiểm tra bằng build output)
- Thiếu `JINA_API_KEY` → tính năng tự ẩn hoặc báo lỗi rõ ràng, **không làm sập** phần còn lại của trang
- Admin upload ảnh mới → embedding tự sinh, sản phẩm xuất hiện trong kết quả tìm kiếm mà không cần chạy script thủ công
- Mở trên mobile → nút 📷 mở thẳng camera sau

---

## 7. Phân kỳ

### Phase 1 — Luồng tìm kiếm bằng ảnh (phạm vi đã chốt)
- Migration cột `image_embedding` + script backfill
- `image_search_service.py` + endpoint `POST /api/products/search-by-image`
- Hook auto-embed vào luồng admin upload ảnh
- UI: nút 📷 navbar, modal upload, resize canvas, lưới kết quả top-5
- **Camera capture** (`capture="environment"`) — chi phí gần bằng 0
- **Nút "Món tương tự" ở PDP** (`GET /api/products/{id}/similar`) — tái dụng ma trận có sẵn, không tốn API call

### Phase 2 — Tích hợp chatbot
Đính kèm ảnh trong khung chat AI → bot nhận diện món rồi tư vấn/đặt hàng. Tách riêng vì đụng `chatbot_router.py`, luồng SSE streaming và intent đặt hàng — khối lượng công việc thật sự đáng kể.

### Phase 3 — VLM re-rank (tuỳ chọn, chỉ làm nếu số đo Phase 1 cho thấy cần)
CLIP lấy top-5 → gửi ảnh + 5 tên món cho Groq vision để xếp lại. Kỳ vọng đẩy top-1 từ ~55% lên ~75-85%, đổi lấy +1-2s latency và thêm một điểm hỏng. **Chỉ triển khai sau khi có số đo thực tế** — nếu top-3 đã đủ tốt thì không cần.

---

## 8. Bước tiếp theo

1. Đăng ký API key Jina (không cần thẻ) → thêm `JINA_API_KEY` vào `.env` và Vercel env vars
2. Chuẩn bị bộ test 20 ảnh chụp thật để đo độ chính xác — **làm trước khi code**, nếu không sẽ không có cách nào biết tính năng có hoạt động hay không
3. Lập kế hoạch triển khai Phase 1 theo từng bước

## Phụ lục — Nguồn tham khảo

- [Jina Embedding API](https://jina.ai/embeddings/) — free tier, rate limit
- [jina-clip-v2 model card](https://jina.ai/models/jina-clip-v2/) — Matryoshka, 512×512, 89 ngôn ngữ
- [Cohere rate limits](https://docs.cohere.com/docs/rate-limits) — trial key 1.000 calls/tháng
- [Groq Llama 4 Scout](https://console.groq.com/docs/model/meta-llama/llama-4-scout-17b-16e-instruct) — vision input, trạng thái Preview
