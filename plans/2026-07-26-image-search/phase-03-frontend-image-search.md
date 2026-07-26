# Phase 03 — Frontend

Mục tiêu: nút 📷 trên navbar → chụp/chọn ảnh → lưới top-5 để user chọn. Kèm "Món tương tự" ở PDP.

Phụ thuộc: Phase 02 xong, curl chạy đúng.

## Files

| File | Loại |
|---|---|
| `templates/highlands-coffee.html` | sửa |
| `static/css/main.css` | sửa |
| `scripts/eval_image_search.py` | **mới** |

---

## Bước 1 — Nút và modal

`highlands-coffee.html` dòng ~35, thêm nút cạnh 🔍 trong `.nav-search-wrap`:

```html
<button class="icon-btn" id="nav-image-search" title="Tìm bằng hình ảnh"
        onclick="openImageSearch()">📷</button>
```

Modal đặt cạnh `pdp-modal` (dòng ~524), tái dụng đúng pattern overlay + modal có sẵn — **đừng phát minh cấu trúc mới**.

Hai lối vào ảnh, **hai input riêng**:

```html
<input type="file" id="img-search-camera" accept="image/*" capture="environment" hidden>
<input type="file" id="img-search-gallery" accept="image/*" hidden>
```

Lý do tách đôi: `capture="environment"` bắt mở thẳng camera sau trên mobile nhưng **một số trình duyệt sẽ mất luôn lựa chọn thư viện**. Hai nút "📸 Chụp ảnh" / "🖼️ Chọn từ thư viện" giải quyết gọn, desktop chỉ hiện nút thư viện.

## Bước 2 — Resize phía client

Đây là chi tiết quan trọng nhất của phase này. Trước khi upload:

```js
async function resizeImage(file, maxEdge = 512, quality = 0.85) {
  // createImageBitmap → canvas, giữ tỉ lệ, cạnh dài nhất = maxEdge
  // canvas.toBlob('image/jpeg', quality)
}
```

Ba lợi ích cùng lúc:
- Né giới hạn body ~4.5MB của Vercel serverless
- Payload 4MB → ~80KB, giảm ~50 lần, upload trên 4G nhanh hẳn
- Jina đằng nào cũng xử lý ở 512×512, gửi to hơn chỉ tốn token vô ích

Dùng `createImageBitmap` với fallback `Image` + `URL.createObjectURL`. **Nhớ `URL.revokeObjectURL`** sau khi xong, tránh rò bộ nhớ khi user thử nhiều ảnh liên tiếp.

Ảnh chụp từ điện thoại hay dính **EXIF orientation** → có thể bị xoay 90°. `createImageBitmap(file, { imageOrientation: 'from-image' })` xử lý được. Kiểm tra bằng ảnh chụp dọc thật.

## Bước 3 — Gọi API và hiện kết quả

```js
async function runImageSearch(file) {
  const blob = await resizeImage(file);
  const fd = new FormData();
  fd.append('file', blob, 'query.jpg');
  const res = await fetch('/api/products/search-by-image', { method: 'POST', body: fd });
  // ...
}
```

Bốn trạng thái UI, **cả bốn đều phải có**:

| Trạng thái | Hiển thị |
|---|---|
| Đang xử lý | Xem trước ảnh đã resize + spinner "🔍 Đang nhận diện..." |
| Có kết quả | Lưới top-5 + nhãn độ tin cậy |
| Rỗng / score thấp | "Không nhận ra món này. Thử chụp gần hơn hoặc tìm bằng tên." |
| Lỗi 502/503 | Thông điệp tiếng Việt rõ ràng + nút "Tìm bằng tên" mở lại ô search |

**Tái dụng `renderMenuGrid()`** đã có (dòng ~1181) để vẽ lưới, chỉ chèn thêm badge score. Click sản phẩm → `openPDP(id)` như mọi chỗ khác.

### Nhãn độ tin cậy — số tạm, phải hiệu chỉnh

| Score | Nhãn |
|---|---|
| ≥ 0.75 | ✅ Rất khớp |
| 0.60 – 0.75 | 🤔 Có thể là |
| < 0.60 | Vẫn hiện, ghi "Kết quả gần đúng" |

⚠️ **Ba con số này là phỏng đoán, chưa phải số đo.** Bắt buộc thay bằng số thật từ bước 5 (phân bố score của khớp đúng vs khớp sai). Đưa vào một hằng số duy nhất ở đầu file để sửa một chỗ.

**Không auto-nhảy vào top-1 dù score cao.** Với top-1 chỉ ~50-65%, tự động chuyển trang sẽ sai một nửa số lần — user phải bấm back liên tục, tệ hơn hẳn việc tự chọn từ 5 lựa chọn.

## Bước 4 — Món tương tự ở PDP

Trong `openPDP()` (dòng ~1244), sau khi render nội dung chính:

- Gọi `GET /api/products/{id}/similar?limit=4`
- Trả `[]` → **không render gì cả**, không hiện khối rỗng
- Render hàng ngang thumbnail nhỏ, click → `openPDP(id)` món mới

Gọi **sau** khi nội dung chính đã hiện, đừng chặn PDP chờ request này.

## Bước 5 — Script đo độ chính xác

`scripts/eval_image_search.py` — đây là thứ biến tiêu chí nghiệm thu từ cảm tính thành số đo.

Đầu vào: `tests/image-search-fixtures/manifest.csv`

```csv
image_path,expected_product_id
photos/ca-phe-sua-da-01.jpg,1
photos/latte-02.jpg,5
```

Đầu ra:

```
Đã đánh giá 20 ảnh
Top-1: 11/20 (55.0%)
Top-3: 17/20 (85.0%)   ← ngưỡng đạt là ≥80%
Top-5: 19/20 (95.0%)

Score trung bình khớp đúng: 0.81
Score trung bình khớp sai:  0.52     ← dùng để đặt ngưỡng ở bước 3

Sai nhiều nhất:
  latte-02.jpg     → đoán Cappuccino (0.79), đúng là Latte (0.77)
```

Cột "score trung bình" chính là dữ liệu để chốt ba ngưỡng ở bước 3. **Chạy script trước, sửa ngưỡng sau.**

Ảnh test không commit vào git (`.gitignore`), chỉ commit `manifest.csv`.

## Bước 6 — CSS

`main.css`: modal upload, khu vực xem trước ảnh, badge score, lưới kết quả, hàng "món tương tự". Bám theo biến màu và bo góc có sẵn (`#C8102E`, `#5C3D2E`, radius 12/24px). **Responsive** — luồng chính là mobile.

## Validation

- Desktop: chọn ảnh → kết quả dưới 3s
- **Điện thoại thật**: nút 📸 mở camera sau; ảnh chụp dọc **không bị xoay 90°**
- Ảnh 4MB → resize xong còn dưới 150KB (kiểm ở tab Network)
- Ảnh không liên quan (ví dụ ảnh con mèo) → có thông điệp tử tế, không phải lưới kết quả rác
- `JINA_API_KEY` bị bỏ → nút 📷 ẩn hoặc báo lỗi rõ, **phần còn lại của trang chạy bình thường**
- PDP sản phẩm chưa có embedding → không hiện khối "món tương tự" rỗng
- `eval_image_search.py` → **top-3 ≥ 80%**

## Rủi ro

| Rủi ro | Xử lý |
|---|---|
| EXIF xoay ảnh chụp dọc | `imageOrientation: 'from-image'`, test bằng ảnh dọc thật |
| Ngưỡng score đặt sai | Hiệu chỉnh bằng số đo bước 5, không đoán |
| User kỳ vọng độ chính xác tuyệt đối | Copy UI nói rõ "kết quả gợi ý", hiện 5 lựa chọn thay vì khẳng định 1 |
| Rò bộ nhớ khi thử nhiều ảnh | `revokeObjectURL` sau mỗi lần |
| File HTML đã 2856 dòng | Gom toàn bộ code mới vào một khối liền, có comment mở/đóng rõ ràng |
