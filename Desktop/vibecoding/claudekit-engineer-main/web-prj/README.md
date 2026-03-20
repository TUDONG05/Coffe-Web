# Highlands Coffee — Web Application

Ứng dụng web thương mại điện tử cho chuỗi cà phê **Highlands Coffee**, xây dựng bằng **FastAPI** (backend) và **HTML/CSS/Vanilla JavaScript** (frontend). Hệ thống gồm hai giao diện riêng biệt: trang dành cho khách hàng và trang quản trị dành cho admin.

---

## Tính năng

### Giao diện khách hàng (`/`)

**Tài khoản & Xác thực**
- Đăng ký tài khoản khách hàng
- Đăng nhập / đăng xuất bằng JWT
- Xem & cập nhật hồ sơ cá nhân (tên, số điện thoại, địa chỉ)
- Đổi mật khẩu

**Menu & Đặt hàng**
- Duyệt 30+ sản phẩm, lọc theo danh mục (Cà phê, Trà, Freeze, Thức ăn, Combo)
- Thêm sản phẩm vào giỏ hàng, điều chỉnh số lượng
- Đặt hàng online (hỗ trợ cả khách vãng lai và tài khoản đăng nhập)
- Xem lịch sử đơn hàng
- Huỷ đơn hàng đang chờ xử lý

**Nội dung**
- Xem khuyến mãi đang áp dụng
- Đọc tin tức & bài viết mới nhất
- Tìm kiếm cửa hàng theo thành phố, lọc theo từ khóa

---

### Giao diện quản trị (`/admin`)

**Tổng quan**
- Dashboard thống kê: tổng số sản phẩm, đơn hàng, khách hàng, doanh thu

**Quản lý nội dung (CRUD đầy đủ)**
- **Sản phẩm** — tìm kiếm, lọc theo danh mục/giá, phân trang
- **Đơn hàng** — cập nhật trạng thái, lọc theo ngày/trạng thái/giá
- **Khách hàng** — tìm kiếm, lọc theo trạng thái kích hoạt
- **Tin tức** — tìm kiếm, lọc theo thẻ
- **Cửa hàng** — quản lý địa điểm toàn hệ thống
- **Danh mục** — quản lý danh mục sản phẩm
- **Tài khoản Admin/Staff** — phân quyền, quản lý người dùng nội bộ

**Tính năng chung**
- Xác thực JWT bảo mật, phân quyền theo role
- Kích hoạt / vô hiệu hoá bản ghi (soft delete, không xoá vật lý)
- Thông báo toast sau mỗi thao tác
- Phân trang cho danh sách lớn

---

## Giao diện ứng dụng

| Trang | URL | Mô tả |
|-------|-----|-------|
| Trang khách hàng | `http://localhost:8000/` | SPA nhiều trang: menu, giỏ hàng, tài khoản, tin tức, cửa hàng |
| Trang quản trị | `http://localhost:8000/admin` | Dashboard admin với bảng dữ liệu CRUD |
| Giới thiệu | `http://localhost:8000/about` | Trang thông tin tĩnh về công ty |
| Swagger UI | `http://localhost:8000/docs` | Tài liệu API tương tác |
| Health check | `http://localhost:8000/health` | Kiểm tra trạng thái server |

---

## Công nghệ sử dụng

| Thành phần | Công nghệ | Phiên bản |
|------------|-----------|-----------|
| Backend framework | FastAPI | 0.104.1 |
| ASGI server | Uvicorn | 0.24.0 |
| ORM | SQLAlchemy | 2.0.23 |
| Database | MySQL | 5.7+ |
| DB driver | PyMySQL | 1.1.0 |
| Validation | Pydantic | v2.5.0 |
| Xác thực | JWT (HS256) + Bcrypt | python-jose 3.3.0 / bcrypt 4.1.1 |
| Config | python-dotenv | 1.0.0 |
| File tĩnh | aiofiles | ≥23.0.0 |
| Frontend | HTML5, CSS3, Vanilla JavaScript | — |
| Runtime | Python | 3.10+ |

---

## Cấu trúc source code

```
web-prj/
│
├── highlands_app.py          # Entry point — khởi tạo FastAPI, mount routers, serve HTML
├── requirements.txt          # Danh sách thư viện Python (11 packages)
├── migrate_db.py             # Tạo / cập nhật bảng an toàn (không mất dữ liệu)
├── create_admin.py           # Tạo tài khoản admin mặc định lần đầu
├── setup.sh                  # Script cài đặt tự động (Linux/macOS)
├── setup.bat                 # Script cài đặt tự động (Windows)
├── .env                      # Biến môi trường (KHÔNG commit lên git)
├── .env.example              # File mẫu .env
│
├── highlands/                # Package backend chính
│   ├── config.py             # Cấu hình: DATABASE_URL, SECRET_KEY, JWT expiry
│   ├── database.py           # SQLAlchemy engine + SessionLocal + get_db()
│   ├── models.py             # 8 ORM models: User, Category, Product, Order, OrderItem,
│   │                         #               Store, News, Promotion
│   ├── auth_utils.py         # Hash mật khẩu, tạo/xác minh JWT, dependency require_admin
│   ├── seed_db.py            # Seed dữ liệu mẫu (30 sản phẩm, 12 cửa hàng, ...)
│   │
│   └── routers/
│       │
│       ├── ── Public API (không cần xác thực) ──
│       ├── auth_router.py          # /api/auth — đăng ký, đăng nhập, hồ sơ
│       ├── products_router.py      # /api/products
│       ├── orders_router.py        # /api/orders
│       ├── stores_router.py        # /api/stores
│       ├── news_router.py          # /api/news
│       ├── promotions_router.py    # /api/promotions
│       │
│       └── ── Admin API (yêu cầu JWT role=admin) ──
│           ├── admin_dashboard_router.py   # /api/admin/dashboard
│           ├── admin_products_router.py    # /api/admin/products
│           ├── admin_orders_router.py      # /api/admin/orders
│           ├── admin_customers_router.py   # /api/admin/customers
│           ├── admin_news_router.py        # /api/admin/news
│           ├── admin_stores_router.py      # /api/admin/stores
│           ├── admin_categories_router.py  # /api/admin/categories
│           └── admin_users_router.py       # /api/admin/users
│
├── templates/                # Giao diện HTML (SPA)
│   ├── highlands-coffee.html # Trang khách hàng (~1360 dòng)
│   ├── admin-panel.html      # Trang quản trị (~1118 dòng)
│   └── about.html            # Trang giới thiệu (~257 dòng)
│
└── static/
    └── css/
        ├── main.css          # Style trang khách hàng (801 dòng)
        ├── admin.css         # Style trang quản trị (600 dòng)
        └── about.css         # Style trang giới thiệu (217 dòng)
```

---

## Schema Database

### Tổng quan các bảng

| Bảng | Mô tả |
|------|-------|
| `users` | Tài khoản khách hàng, staff và admin |
| `categories` | Danh mục sản phẩm |
| `products` | Sản phẩm (tên, danh mục, giá, mô tả, emoji) |
| `orders` | Đơn hàng (tên khách, SĐT, địa chỉ, tổng tiền, trạng thái) |
| `order_items` | Chi tiết từng sản phẩm trong đơn hàng |
| `stores` | Cửa hàng (địa chỉ, quận, thành phố, giờ mở cửa) |
| `news` | Tin tức & bài viết |
| `promotions` | Khuyến mãi đang áp dụng |

### Chi tiết các model

**`users`**
```
id, name, email (unique), phone, hashed_password,
role (admin | staff | customer), address,
is_active (bool), created_at
```

**`categories`**
```
id, name (unique), emoji, is_active
```

**`products`**
```
id, name, category, price (VND), description, emoji, is_active
```

**`orders`**
```
id, user_id (FK → users), customer_name, phone, total,
address, note, status (pending | confirmed | done | cancelled),
is_active, created_at
```

**`order_items`**
```
id, order_id (FK → orders), product_id (FK → products),
name (snapshot tên SP lúc đặt), price, quantity, subtotal
```

**`stores`**
```
id, name, address, district, city, phone, hours, is_active
```

**`news`**
```
id, title, excerpt, content, tag, emoji, published_at, is_active
```

**`promotions`**
```
id, title, description, discount, emoji,
tag (HOT | NEW | SALE), valid_until, is_active
```

**Quan hệ:**
- `users` → `orders` (1:nhiều)
- `orders` → `order_items` (1:nhiều)
- `order_items` → `products` (nhiều:1)
- Xoá mềm (soft delete) qua cờ `is_active` — không xoá vật lý

---

## Cài đặt

### Yêu cầu môi trường

- Python **3.10+**
- MySQL **5.7+** (hoặc 8.x)
- pip

### Bước 1 — Clone & tạo môi trường ảo

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt (Windows)
venv\Scripts\activate

# Kích hoạt (Linux/macOS)
source venv/bin/activate
```

### Bước 2 — Cài thư viện

```bash
pip install -r requirements.txt
```

Hoặc dùng script tự động:

```bash
# Linux/macOS
bash setup.sh

# Windows
setup.bat
```

### Bước 3 — Cấu hình môi trường

```bash
# Sao chép file mẫu
cp .env.example .env   # Linux/macOS
copy .env.example .env # Windows
```

Chỉnh sửa `.env`:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=highlands_coffee
SECRET_KEY=your-random-secret-key-min-32-chars
```

> **Lưu ý:** Bắt buộc đổi `SECRET_KEY` thành chuỗi ngẫu nhiên khi chạy production.

### Bước 4 — Tạo database

Tạo database MySQL:

```sql
CREATE DATABASE highlands_coffee
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Chạy migrate để tạo bảng:

```bash
python migrate_db.py
```

### Bước 5 — Seed dữ liệu mẫu

```bash
python highlands/seed_db.py
```

Tạo dữ liệu mẫu:
- 30 sản phẩm (10 cà phê, 8 trà, 5 freeze, 5 thức ăn, 2 combo)
- 12 cửa hàng (5 Hà Nội, 4 TP.HCM, 3 Đà Nẵng)
- 6 khuyến mãi
- 6 bài viết tin tức

### Bước 6 — Tạo tài khoản admin

```bash
python create_admin.py
```

Tài khoản mặc định được tạo:
- Email: `admin@highlands.com`
- Mật khẩu: `admin123`

> **Lưu ý:** Đổi mật khẩu ngay sau khi đăng nhập lần đầu.

---

## Chạy ứng dụng

### Chế độ phát triển (auto-reload)

```bash
uvicorn highlands_app:app --host 0.0.0.0 --port 8000 --reload
```

### Chế độ production

```bash
uvicorn highlands_app:app --host 0.0.0.0 --port 8000 --workers 4
```

Sau khi khởi động, truy cập:

| Địa chỉ | Mô tả |
|---------|-------|
| `http://localhost:8000` | Giao diện khách hàng |
| `http://localhost:8000/admin` | Giao diện quản trị |
| `http://localhost:8000/about` | Trang giới thiệu |
| `http://localhost:8000/docs` | Swagger UI — tài liệu API tương tác |
| `http://localhost:8000/health` | Kiểm tra trạng thái server |

---

## API Endpoints

### Public API

#### Xác thực (`/api/auth`)

| Method | Endpoint | Mô tả | Body |
|--------|----------|-------|------|
| POST | `/api/auth/register` | Đăng ký tài khoản | `name, email, password` |
| POST | `/api/auth/login` | Đăng nhập, nhận JWT | `email, password` |
| GET | `/api/auth/me` | Lấy thông tin tài khoản hiện tại | — |
| PUT | `/api/auth/profile` | Cập nhật hồ sơ | `name, phone, address` |
| PUT | `/api/auth/change-password` | Đổi mật khẩu | `old_password, new_password` |

#### Sản phẩm (`/api/products`)

| Method | Endpoint | Mô tả | Query Params |
|--------|----------|-------|--------------|
| GET | `/api/products` | Danh sách sản phẩm | `category` |
| GET | `/api/products/{id}` | Chi tiết sản phẩm | — |

#### Đơn hàng (`/api/orders`)

| Method | Endpoint | Mô tả | Ghi chú |
|--------|----------|-------|---------|
| POST | `/api/orders` | Tạo đơn hàng | `customer_name, phone, address, items[]` |
| GET | `/api/orders/mine` | Lịch sử đơn của tôi | Cần đăng nhập |
| PATCH | `/api/orders/{id}/cancel` | Huỷ đơn hàng | Chỉ huỷ được đơn `pending` |

#### Cửa hàng (`/api/stores`)

| Method | Endpoint | Mô tả | Query Params |
|--------|----------|-------|--------------|
| GET | `/api/stores` | Danh sách cửa hàng | `city, q` (tìm kiếm) |
| GET | `/api/stores/cities` | Danh sách thành phố | — |
| GET | `/api/stores/{id}` | Chi tiết cửa hàng | — |

#### Tin tức & Khuyến mãi

| Method | Endpoint | Mô tả | Query Params |
|--------|----------|-------|--------------|
| GET | `/api/news` | Danh sách tin tức | `tag` |
| GET | `/api/news/{id}` | Chi tiết bài viết | — |
| GET | `/api/promotions` | Khuyến mãi đang áp dụng | — |

---

### Admin API

> Tất cả yêu cầu header: `Authorization: Bearer <jwt_token>`
> Role bắt buộc: `admin`

#### Dashboard

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/admin/dashboard` | Thống kê tổng quan |

#### Sản phẩm (`/api/admin/products`)

| Method | Endpoint | Mô tả | Query Params |
|--------|----------|-------|--------------|
| GET | `/api/admin/products` | Danh sách có phân trang | `skip, limit, category, search, min_price, max_price, is_active` |
| POST | `/api/admin/products` | Tạo sản phẩm mới | — |
| GET | `/api/admin/products/{id}` | Chi tiết sản phẩm | — |
| PUT | `/api/admin/products/{id}` | Cập nhật sản phẩm | — |
| PATCH | `/api/admin/products/{id}` | Toggle kích hoạt | — |
| DELETE | `/api/admin/products/{id}` | Xoá mềm | — |

#### Đơn hàng (`/api/admin/orders`)

| Method | Endpoint | Mô tả | Query Params |
|--------|----------|-------|--------------|
| GET | `/api/admin/orders` | Danh sách có phân trang | `status, search, date_from, date_to, min_price, max_price` |
| POST | `/api/admin/orders` | Tạo đơn hàng thủ công | — |
| GET | `/api/admin/orders/{id}` | Chi tiết đơn + items | — |
| PATCH | `/api/admin/orders/{id}` | Cập nhật trạng thái | — |
| DELETE | `/api/admin/orders/{id}` | Xoá mềm | — |

#### Khách hàng (`/api/admin/customers`)

| Method | Endpoint | Mô tả | Query Params |
|--------|----------|-------|--------------|
| GET | `/api/admin/customers` | Danh sách có phân trang | `search, is_active` |
| POST | `/api/admin/customers` | Tạo khách hàng | — |
| GET | `/api/admin/customers/{id}` | Chi tiết khách hàng | — |
| PUT | `/api/admin/customers/{id}` | Cập nhật thông tin | — |
| PATCH | `/api/admin/customers/{id}` | Toggle kích hoạt | — |
| DELETE | `/api/admin/customers/{id}` | Xoá mềm | — |

#### Tin tức (`/api/admin/news`)

| Method | Endpoint | Mô tả | Query Params |
|--------|----------|-------|--------------|
| GET | `/api/admin/news` | Danh sách có phân trang | `search, tag, is_active` |
| POST | `/api/admin/news` | Tạo bài viết | — |
| GET | `/api/admin/news/{id}` | Chi tiết bài viết | — |
| PUT | `/api/admin/news/{id}` | Cập nhật bài viết | — |
| PATCH | `/api/admin/news/{id}` | Toggle kích hoạt | — |
| DELETE | `/api/admin/news/{id}` | Xoá mềm | — |

#### Cửa hàng, Danh mục, Tài khoản Admin

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET/POST | `/api/admin/stores` | Danh sách / tạo cửa hàng |
| GET/PUT/DELETE | `/api/admin/stores/{id}` | Chi tiết / sửa / xoá |
| GET/POST | `/api/admin/categories` | Danh sách / tạo danh mục |
| GET/PUT/DELETE | `/api/admin/categories/{id}` | Chi tiết / sửa / xoá |
| GET/POST | `/api/admin/users` | Danh sách / tạo tài khoản admin/staff |
| GET/PUT/DELETE | `/api/admin/users/{id}` | Chi tiết / sửa / xoá |

---

## Bảo mật

**Đã triển khai:**
- Bcrypt hashing cho mật khẩu
- JWT HS256 với thời hạn 24 giờ
- Phân quyền theo role: `admin`, `staff`, `customer`
- Soft delete — không xoá dữ liệu vật lý
- Kiểm tra email duy nhất khi đăng ký
- Mật khẩu tối thiểu 6 ký tự

**Cần cấu hình trước khi deploy production:**

- [ ] Đổi `SECRET_KEY` thành chuỗi ngẫu nhiên an toàn (≥32 ký tự)
- [ ] Đặt mật khẩu MySQL mạnh
- [ ] Giới hạn `allow_origins` trong CORS (thay `"*"` bằng domain thực)
- [ ] Bật HTTPS (Nginx + Let's Encrypt hoặc Cloudflare)
- [ ] Đổi mật khẩu tài khoản admin mặc định
- [ ] Sao lưu database định kỳ
- [ ] Bật logging và giám sát lỗi

---

## License

Proprietary — Highlands Coffee
