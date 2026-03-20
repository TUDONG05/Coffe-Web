# Highlands Coffee — Web Application

Ứng dụng web thương mại điện tử cho chuỗi cà phê Highlands Coffee, xây dựng bằng **FastAPI** (backend) và **HTML/CSS/Vanilla JavaScript** (frontend). Hệ thống gồm hai giao diện: trang dành cho khách hàng và trang quản trị dành cho admin.

---

## Tính năng

### Giao diện khách hàng (`/`)
- Xem menu sản phẩm, lọc theo danh mục (cà phê, trà, freeze, thức ăn, combo)
- Xem tin tức và khuyến mãi đang áp dụng
- Tìm kiếm cửa hàng theo thành phố
- Đặt hàng online (không cần đăng nhập)

### Giao diện admin (`/admin`)
- Đăng nhập bảo mật bằng JWT
- Dashboard thống kê tổng quan (sản phẩm, đơn hàng, khách hàng, doanh thu)
- CRUD đầy đủ: Sản phẩm, Tin tức, Khách hàng, Đơn hàng
- Kích hoạt/vô hiệu hoá từng bản ghi
- Thông báo xác nhận cho mọi thao tác

---

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Backend | FastAPI 0.104, Python 3.10+ |
| ORM | SQLAlchemy 2.0 |
| Database | MySQL 5.7+ |
| Xác thực | JWT (HS256) + Bcrypt |
| Validation | Pydantic v2 |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Server | Uvicorn |

---

## Cấu trúc source code

```
web-prj/
│
├── highlands_app.py          # Entry point — khởi tạo FastAPI, mount routers, serve HTML
├── requirements.txt          # Danh sách thư viện Python
├── setup.sh                  # Script cài đặt (Linux/macOS)
├── setup.bat                 # Script cài đặt (Windows)
├── create_admin.py           # Tạo tài khoản admin lần đầu
├── migrate_db.py             # Tạo / cập nhật bảng trong database
│
├── highlands-coffee.html     # Giao diện người dùng (SPA)
├── admin-panel.html          # Giao diện quản trị (SPA)
│
├── highlands/                # Package backend chính
│   ├── config.py             # Cấu hình: DATABASE_URL, SECRET_KEY, JWT expiry
│   ├── database.py           # SQLAlchemy engine + session + get_db()
│   ├── models.py             # ORM models: User, Product, Order, OrderItem, Store, News, Promotion
│   ├── auth_utils.py         # Tạo/xác minh JWT, hash password, dependency require_admin
│   ├── seed_db.py            # Seed dữ liệu mẫu vào database
│   │
│   └── routers/              # Các router API
│       │
│       ├── ── Public API (không cần xác thực) ──
│       ├── auth_router.py          # POST /api/auth/login
│       ├── products_router.py      # GET  /api/products
│       ├── news_router.py          # GET  /api/news
│       ├── stores_router.py        # GET  /api/stores
│       ├── promotions_router.py    # GET  /api/promotions
│       ├── orders_router.py        # POST /api/orders
│       │
│       └── ── Admin API (yêu cầu JWT admin) ──
│           ├── admin_dashboard_router.py   # GET  /api/admin/dashboard
│           ├── admin_products_router.py    # CRUD /api/admin/products
│           ├── admin_news_router.py        # CRUD /api/admin/news
│           ├── admin_customers_router.py   # CRUD /api/admin/customers
│           ├── admin_orders_router.py      # CRUD /api/admin/orders
│           ├── admin_stores_router.py      # CRUD /api/admin/stores
│           ├── admin_categories_router.py  # GET  /api/admin/categories
│           └── admin_users_router.py       # Quản lý tài khoản admin
│
├── .env                      # Biến môi trường (KHÔNG commit lên git)
├── .env.example              # File mẫu .env
├── .gitignore
└── README.md
```

---

## Schema database

| Bảng | Mô tả |
|------|-------|
| `users` | Tài khoản khách hàng và admin |
| `products` | Sản phẩm (tên, danh mục, giá, emoji) |
| `orders` | Đơn hàng (tên khách, SĐT, tổng tiền, trạng thái) |
| `order_items` | Chi tiết từng sản phẩm trong đơn hàng |
| `stores` | Danh sách cửa hàng (địa chỉ, quận, thành phố, giờ mở cửa) |
| `news` | Tin tức và bài viết (tiêu đề, nội dung, thẻ) |
| `promotions` | Khuyến mãi đang áp dụng |
| `categories` | Danh mục sản phẩm |

---

## Cài đặt

### Yêu cầu môi trường

- Python **3.10+**
- MySQL **5.7+** (hoặc MySQL 8.x)
- pip

### Bước 1 — Tạo môi trường ảo

```bash
# Tạo venv
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

Hoặc chạy script setup tự động:

```bash
# Linux/macOS
bash setup.sh

# Windows
setup.bat
```

### Bước 3 — Cấu hình môi trường

Sao chép file mẫu và điền thông tin:

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=highlands_coffee
SECRET_KEY=your-secret-key-min-32-chars
```

> **Lưu ý:** Đổi `SECRET_KEY` thành chuỗi ngẫu nhiên dài ít nhất 32 ký tự khi chạy production.

### Bước 4 — Tạo database và bảng

Tạo database MySQL trước:

```sql
CREATE DATABASE highlands_coffee CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Sau đó chạy migrate để tạo bảng:

```bash
python migrate_db.py
```

### Bước 5 — Seed dữ liệu mẫu

```bash
python highlands/seed_db.py
```

Lệnh này tạo dữ liệu mẫu: sản phẩm, cửa hàng, tin tức, khuyến mãi.

### Bước 6 — Tạo tài khoản admin

```bash
python create_admin.py
```

Làm theo hướng dẫn để nhập email và mật khẩu admin.

---

## Chạy ứng dụng

### Chế độ phát triển (có auto-reload)

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
| http://localhost:8000 | Giao diện khách hàng |
| http://localhost:8000/admin | Giao diện quản trị |
| http://localhost:8000/docs | Swagger UI — tài liệu API tương tác |
| http://localhost:8000/health | Kiểm tra trạng thái server |

---

## API Endpoints

### Public

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/auth/login` | Đăng nhập, nhận JWT token |
| GET | `/api/products` | Danh sách sản phẩm (filter: `category`) |
| GET | `/api/news` | Danh sách tin tức (filter: `tag`) |
| GET | `/api/stores` | Danh sách cửa hàng (filter: `city`) |
| GET | `/api/promotions` | Khuyến mãi đang áp dụng |
| POST | `/api/orders` | Đặt hàng (gửi `customer_name`, `phone`, `items[]`) |

### Admin (Header: `Authorization: Bearer <token>`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/admin/dashboard` | Thống kê tổng quan |
| GET/POST | `/api/admin/products` | Danh sách / tạo sản phẩm |
| PUT/PATCH/DELETE | `/api/admin/products/{id}` | Sửa / toggle / xoá sản phẩm |
| GET/POST | `/api/admin/news` | Danh sách / tạo tin tức |
| PUT/PATCH/DELETE | `/api/admin/news/{id}` | Sửa / toggle / xoá tin tức |
| GET/POST | `/api/admin/customers` | Danh sách / tạo khách hàng |
| PUT/PATCH/DELETE | `/api/admin/customers/{id}` | Sửa / toggle / xoá khách hàng |
| GET/POST | `/api/admin/orders` | Danh sách / tạo đơn hàng |
| PATCH/DELETE | `/api/admin/orders/{id}` | Cập nhật trạng thái / xoá đơn hàng |

---

## Checklist trước khi deploy production

- [ ] Đổi `SECRET_KEY` thành chuỗi ngẫu nhiên an toàn
- [ ] Đặt mật khẩu MySQL mạnh
- [ ] Giới hạn `allow_origins` trong CORS (thay `"*"` bằng domain thực)
- [ ] Bật HTTPS (dùng Nginx + Let's Encrypt hoặc Cloudflare)
- [ ] Sao lưu database định kỳ
- [ ] Bật logging và giám sát lỗi

---

## License

Proprietary — Highlands Coffee
