# Tu's Coffee — Web Application

Ứng dụng web thương mại điện tử cho chuỗi cà phê **Tu's Coffee**, xây dựng bằng **FastAPI** (backend) và **HTML/CSS/Vanilla JavaScript** (frontend SPA). Hệ thống gồm hai giao diện riêng biệt: trang khách hàng và trang quản trị.

---

## Tính năng

### Giao diện khách hàng (`/`)

[![Xem video](https://img.youtube.com/vi/Iw8Dd8FMvbE/0.jpg)](https://youtu.be/Iw8Dd8FMvbE)

**Tài khoản & Xác thực**
- Đăng ký tài khoản (mặc định role `user`, tặng 50 điểm Rewards)
- Đăng nhập / đăng xuất bằng JWT
- Xem & cập nhật hồ sơ cá nhân (tên, số điện thoại, địa chỉ)
- Đổi mật khẩu

**Menu & Tìm kiếm**
- Duyệt 30+ sản phẩm, lọc theo danh mục (Cà phê, Trà, Freeze, Thức ăn, Combo)
- Tìm kiếm sản phẩm theo tên hoặc danh mục (thanh tìm kiếm menu & nút 🔍 navbar)

**Giỏ hàng & Đặt hàng**
- Thêm sản phẩm vào giỏ hàng, điều chỉnh số lượng
- Đặt hàng online (hỗ trợ cả khách vãng lai và tài khoản đăng nhập)
- Chọn phương thức thanh toán: **Tiền mặt** hoặc **Chuyển khoản QR** (VietQR)
- Quét mã QR thanh toán ngay sau khi đặt (MB Bank — 010320058686 DONG VAN TU)
- Đơn QR tự động chuyển trạng thái `payment_status = paid`
- Xem lịch sử đơn hàng (trạng thái, phương thức thanh toán, chi tiết items)
- Huỷ đơn hàng đang chờ xử lý

**Tu's Coffee Rewards**
- Trang Rewards riêng biệt với 3 tầng: Bronze / Silver / Gold
- Tích điểm khi đặt hàng: 10.000đ = 1 điểm
- Hiển thị điểm hiện tại, toast thông báo điểm tích sau mỗi đơn
- Catalog đổi thưởng (đồ uống miễn phí, voucher, quà tặng)

**Nội dung**
- Xem khuyến mãi đang áp dụng
- Đọc tin tức & bài viết mới nhất
- Tìm kiếm cửa hàng theo thành phố, lọc theo từ khóa
- Trang Giới thiệu (About) — ban lãnh đạo, câu chuyện thương hiệu

---

### Giao diện quản trị (`/admin`)

[![Xem video](https://img.youtube.com/vi/H9Vw_seuFYQ/0.jpg)](https://youtu.be/H9Vw_seuFYQ)

**Dashboard**
- Thống kê tổng quan: tổng sản phẩm, đơn hàng, tài khoản, doanh thu
- Bảng đơn hàng gần đây

**Quản lý nội dung (CRUD đầy đủ)**
- **Sản phẩm** — tìm kiếm, lọc theo danh mục/giá, phân trang, toggle kích hoạt
- **Đơn hàng** — cập nhật trạng thái, xem chi tiết items, cột Thanh Toán (paid/unpaid + phương thức)
- **Tài khoản** — hiển thị role, điểm Rewards; lọc theo role (`admin` / `user`) và trạng thái
- **Tin tức** — tìm kiếm, lọc theo thẻ
- **Cửa hàng** — quản lý địa điểm toàn hệ thống
- **Danh mục** — quản lý danh mục sản phẩm
- **Tài khoản Admin** — tạo, phân quyền, khóa/mở tài khoản nội bộ

**Tính năng chung**
- Xác thực JWT, phân quyền role `admin`
- Soft delete — không xoá vật lý
- Toast thông báo sau mỗi thao tác
- Phân trang cho danh sách lớn

---

## Giao diện ứng dụng

| Trang | URL | Mô tả |
|-------|-----|-------|
| Khách hàng | `http://localhost:8000/` | SPA: menu, giỏ hàng, rewards, tin tức, cửa hàng |
| Quản trị | `http://localhost:8000/admin` | Dashboard CRUD đầy đủ |
| Giới thiệu | `http://localhost:8000/about` | Thông tin thương hiệu Tu's Coffee |
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
| AI / Chatbot | scikit-learn | ≥1.3.0 |
| HTTP client | httpx | ≥0.27.0 |
| Frontend | HTML5, CSS3, Vanilla JavaScript (SPA) | — |
| Thanh toán QR | VietQR free API | — |
| Runtime | Python | 3.10+ |

---

## Cấu trúc source code

```
web-prj/
│
├── highlands_app.py          # Entry point — khởi tạo FastAPI, mount routers, serve HTML
├── requirements.txt          # Danh sách thư viện Python
├── migrate_db.py             # Migration an toàn (ALTER TABLE, không mất dữ liệu)
├── create_admin.py           # Tạo tài khoản admin mặc định lần đầu
├── setup.sh                  # Script cài đặt tự động (Linux/macOS)
├── setup.bat                 # Script cài đặt tự động (Windows)
├── .env                      # Biến môi trường (KHÔNG commit lên git)
├── .env.example              # File mẫu .env
│
├── highlands/                # Package backend chính
│   ├── config.py             # Cấu hình: DATABASE_URL, SECRET_KEY, JWT expiry
│   ├── database.py           # SQLAlchemy engine + SessionLocal + get_db()
│   ├── models.py             # ORM models: User, Category, Product, Order, OrderItem,
│   │                         #             Store, News, Promotion
│   ├── auth_utils.py         # Hash mật khẩu, tạo/xác minh JWT, require_admin
│   ├── seed_db.py            # Seed dữ liệu mẫu
│   │
│   ├── routers/
│   │   │
│   │   ├── ── Public API (không cần xác thực) ──
│   │   ├── auth_router.py          # /api/auth — đăng ký, đăng nhập, hồ sơ
│   │   ├── products_router.py      # /api/products — danh sách, tìm kiếm
│   │   ├── orders_router.py        # /api/orders — tạo đơn, lịch sử, huỷ
│   │   ├── stores_router.py        # /api/stores
│   │   ├── news_router.py          # /api/news
│   │   ├── promotions_router.py    # /api/promotions
│   │   ├── chatbot_router.py       # /api/chatbot — AI tư vấn menu
│   │   │
│   │   └── ── Admin API (yêu cầu JWT role=admin) ──
│   │       ├── admin_dashboard_router.py   # /api/admin/dashboard
│   │       ├── admin_products_router.py    # /api/admin/products
│   │       ├── admin_orders_router.py      # /api/admin/orders
│   │       ├── admin_customers_router.py   # /api/admin/customers
│   │       ├── admin_news_router.py        # /api/admin/news
│   │       ├── admin_stores_router.py      # /api/admin/stores
│   │       ├── admin_categories_router.py  # /api/admin/categories
│   │       └── admin_users_router.py       # /api/admin/users
│   │
│   └── services/
│       └── menu_rag_service.py     # RAG service cho chatbot gợi ý menu
│
├── templates/
│   ├── highlands-coffee.html # Trang khách hàng (SPA)
│   ├── admin-panel.html      # Trang quản trị
│   └── about.html            # Trang giới thiệu
│
└── static/
    └── css/
        ├── main.css          # Style trang khách hàng (responsive)
        ├── admin.css         # Style trang quản trị
        └── about.css         # Style trang giới thiệu (responsive)
```

---

## Schema Database

### Các bảng

| Bảng | Mô tả |
|------|-------|
| `users` | Tài khoản người dùng (role: admin / user) |
| `categories` | Danh mục sản phẩm |
| `products` | Sản phẩm (tên, danh mục, giá, mô tả, emoji) |
| `orders` | Đơn hàng (tên khách, SĐT, địa chỉ, tổng tiền, trạng thái, thanh toán) |
| `order_items` | Chi tiết từng sản phẩm trong đơn hàng |
| `stores` | Cửa hàng (địa chỉ, quận, thành phố, giờ mở cửa) |
| `news` | Tin tức & bài viết |
| `promotions` | Khuyến mãi đang áp dụng |

### Chi tiết các model

**`users`**
```
id            INT          PK, auto-increment
name          VARCHAR(100) NOT NULL
email         VARCHAR(150) UNIQUE, NOT NULL
phone         VARCHAR(20)
hashed_pwd    VARCHAR(255) NOT NULL
role          VARCHAR(20)  DEFAULT 'user'   -- admin | user
address       VARCHAR(300)
points        INT          DEFAULT 0        -- điểm Rewards
is_active     INT          DEFAULT 1        -- 1=hoạt động, 0=bị khóa
created_at    DATETIME     DEFAULT now()
```

**`categories`**
```
id        INT          PK
name      VARCHAR(100) UNIQUE, NOT NULL
emoji     VARCHAR(10)  DEFAULT '☕'
is_active INT          DEFAULT 1
```

**`products`**
```
id          INT          PK
name        VARCHAR(150) NOT NULL
category    VARCHAR(50)  NOT NULL
price       INT          NOT NULL   -- VND
description TEXT
emoji       VARCHAR(10)  DEFAULT '☕'
is_active   INT          DEFAULT 1
```

**`orders`**
```
id             INT          PK
user_id        INT          FK → users.id (NULL cho khách vãng lai)
customer_name  VARCHAR(100) NOT NULL
phone          VARCHAR(20)  NOT NULL
address        VARCHAR(300)
total          INT          NOT NULL   -- VND
note           TEXT
status         VARCHAR(30)  DEFAULT 'pending'
               -- pending | confirmed | done | cancelled
payment_method VARCHAR(20)  DEFAULT 'cash'
               -- cash | qr_transfer
payment_status VARCHAR(20)  DEFAULT 'unpaid'
               -- unpaid | paid
is_active      INT          DEFAULT 1
created_at     DATETIME     DEFAULT now()
```

**`order_items`**
```
id         INT          PK
order_id   INT          FK → orders.id
product_id INT          FK → products.id
name       VARCHAR(150) NOT NULL   -- snapshot tên sản phẩm lúc đặt
price      INT          NOT NULL
quantity   INT          NOT NULL
subtotal   INT          NOT NULL
```

**`stores`**
```
id        INT          PK
name      VARCHAR(200) NOT NULL
address   VARCHAR(300) NOT NULL
district  VARCHAR(100) NOT NULL
city      VARCHAR(100) DEFAULT 'Hà Nội'
phone     VARCHAR(30)
hours     VARCHAR(100) DEFAULT '06:00 – 23:00'
is_active INT          DEFAULT 1
```

**`news`**
```
id           INT          PK
title        VARCHAR(300) NOT NULL
excerpt      TEXT
content      TEXT
tag          VARCHAR(50)   -- 'Tin Tức' | 'Sự Kiện' | 'Khuyến Mãi'
emoji        VARCHAR(10)  DEFAULT '📰'
published_at VARCHAR(50)
is_active    INT          DEFAULT 1
```

**`promotions`**
```
id          INT          PK
title       VARCHAR(200) NOT NULL
description TEXT
discount    VARCHAR(50)  -- '20%', 'Mua 1 tặng 1'
emoji       VARCHAR(10)  DEFAULT '🎁'
tag         VARCHAR(50)  -- 'HOT' | 'NEW' | 'SALE'
valid_until VARCHAR(50)
is_active   INT          DEFAULT 1
```

### Quan hệ

```
users ──────────────────── orders          (1 : nhiều)
orders ─────────────────── order_items     (1 : nhiều)
order_items ────────────── products        (nhiều : 1)
```

> Soft delete qua cờ `is_active` — không xoá vật lý dữ liệu.

---

## Cài đặt

### Yêu cầu

- Python **3.10+**
- MySQL **5.7+** (hoặc 8.x)
- pip

### Bước 1 — Tạo môi trường ảo

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
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
# Linux/macOS
cp .env.example .env

# Windows
copy .env.example .env
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

> Bắt buộc đổi `SECRET_KEY` thành chuỗi ngẫu nhiên trước khi deploy production.

### Bước 4 — Tạo database MySQL

```sql
CREATE DATABASE highlands_coffee
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### Bước 5 — Tạo bảng & migrate

```bash
python migrate_db.py
```

Lệnh này tạo tất cả bảng và thêm các cột còn thiếu mà không làm mất dữ liệu hiện có.

### Bước 6 — Seed dữ liệu mẫu

```bash
python highlands/seed_db.py
```

Tạo:
- 30 sản phẩm (10 cà phê, 8 trà, 5 freeze, 5 thức ăn, 2 combo)
- 12 cửa hàng (5 Hà Nội, 4 TP.HCM, 3 Đà Nẵng)
- 6 khuyến mãi, 6 bài viết tin tức

### Bước 7 — Tạo tài khoản admin

```bash
python create_admin.py
```

Tài khoản mặc định:
- Email: `admin@highlands.com`
- Mật khẩu: `admin123`

> Đổi mật khẩu ngay sau khi đăng nhập lần đầu.

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

### Truy cập

| Địa chỉ | Mô tả |
|---------|-------|
| `http://localhost:8000` | Giao diện khách hàng |
| `http://localhost:8000/admin` | Giao diện quản trị |
| `http://localhost:8000/about` | Trang giới thiệu |
| `http://localhost:8000/docs` | Swagger UI — tài liệu API |
| `http://localhost:8000/health` | Kiểm tra trạng thái server |

---

## Dừng ứng dụng

### Nếu chạy foreground (Ctrl+C)

```bash
# Nhấn Ctrl+C trong terminal đang chạy uvicorn
```

### Nếu chạy background

```bash
# Windows — dừng toàn bộ process Python
taskkill /F /IM python.exe

# Linux/macOS — tìm và kill process uvicorn
pkill -f "uvicorn highlands_app"

# Hoặc tìm PID rồi kill
lsof -i :8000
kill -9 <PID>
```

---

## AI Chatbot

Tu's Coffee tích hợp chatbot AI tư vấn thực đơn trực tiếp trên giao diện khách hàng.

### Kiến trúc

```
Người dùng
   │  nhập câu hỏi
   ▼
Frontend (SSE stream)
   │  POST /api/chat/stream
   ▼
ChatbotRouter
   │  1. Tìm món liên quan (RAG)
   │  2. Build system prompt với context
   ▼
MenuRAGService (TF-IDF)          ←── DB sản phẩm
   │  trả top-4 món phù hợp
   ▼
Ollama (local LLM)               ←── model qwen2.5:3b
   │  stream token
   ▼
Frontend render từng token (streaming)
```

### Cách hoạt động

1. **RAG (Retrieval-Augmented Generation)**: Mỗi câu hỏi được vector hoá bằng **TF-IDF** (char n-gram 2–4, tốt với tiếng Việt), tìm top-4 sản phẩm liên quan nhất qua cosine similarity
2. **System prompt**: Inject context sản phẩm vào prompt → LLM chỉ tư vấn đúng menu thực tế
3. **Streaming**: Dùng **SSE (Server-Sent Events)** — response hiển thị từng token ngay khi Ollama trả về
4. **History**: Giữ 6 lượt hội thoại gần nhất để chatbot nhớ ngữ cảnh

### Yêu cầu để chạy chatbot

Cần cài **Ollama** và pull model:

```bash
# Cài Ollama (ollama.com)
# Sau đó pull model
ollama pull qwen2.5:3b

# Chạy Ollama
ollama serve
```

Mặc định Ollama chạy tại `http://localhost:11434`. Có thể override qua `.env`:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

> Nếu không cài Ollama, các tính năng khác vẫn hoạt động bình thường. Chatbot sẽ hiển thị lỗi "Không kết nối được Ollama".

### API chatbot

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/chat/stream` | Chat, trả về SSE token stream |
| POST | `/api/chat/reload-menu` | Reload TF-IDF index sau khi admin sửa sản phẩm |
| GET | `/api/chat/status` | Kiểm tra trạng thái (số món đã index, model đang dùng) |

---

## API Endpoints

### Public API

#### Xác thực (`/api/auth`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/auth/register` | Đăng ký — tặng 50 điểm Rewards, role mặc định `user` |
| POST | `/api/auth/login` | Đăng nhập, trả JWT |
| GET | `/api/auth/me` | Thông tin tài khoản hiện tại |
| PUT | `/api/auth/profile` | Cập nhật hồ sơ |
| PUT | `/api/auth/change-password` | Đổi mật khẩu |

#### Sản phẩm (`/api/products`)

| Method | Endpoint | Query Params |
|--------|----------|--------------|
| GET | `/api/products` | `category`, `q` (tìm theo tên / danh mục) |
| GET | `/api/products/{id}` | — |

#### Đơn hàng (`/api/orders`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/orders` | Tạo đơn — hỗ trợ `payment_method: cash | qr_transfer` |
| GET | `/api/orders/mine` | Lịch sử đơn (cần đăng nhập) |
| PATCH | `/api/orders/{id}/cancel` | Huỷ đơn `pending` |

#### Nội dung

| Method | Endpoint | Query Params |
|--------|----------|--------------|
| GET | `/api/stores` | `city`, `q` |
| GET | `/api/stores/cities` | — |
| GET | `/api/news` | `tag` |
| GET | `/api/promotions` | — |

---

### Admin API

> Header bắt buộc: `Authorization: Bearer <jwt_token>` — role `admin`

| Resource | Endpoints | Thao tác |
|----------|-----------|---------|
| Dashboard | `/api/admin/dashboard` | GET |
| Sản phẩm | `/api/admin/products` | GET (filter: category, search, price), POST, PUT, PATCH, DELETE |
| Đơn hàng | `/api/admin/orders` | GET (filter: status, date, price), POST, GET/{id}, PATCH, DELETE |
| Tài khoản | `/api/admin/customers` | GET (filter: `role`, `status`, `search`), POST, PUT, PATCH, DELETE |
| Tin tức | `/api/admin/news` | GET (filter: tag), POST, PUT, PATCH, DELETE |
| Cửa hàng | `/api/admin/stores` | GET, POST, PUT, DELETE |
| Danh mục | `/api/admin/categories` | GET, POST, PUT, DELETE |
| Admin users | `/api/admin/users` | GET, POST, PUT, PATCH, DELETE |

---

## Bảo mật

**Đã triển khai:**
- Bcrypt hashing cho mật khẩu
- JWT HS256 với thời hạn 24 giờ
- Phân quyền theo role: `admin` / `user`
- Soft delete — không xoá dữ liệu vật lý
- Kiểm tra email duy nhất khi đăng ký
- Mật khẩu tối thiểu 6 ký tự

**Cần cấu hình trước khi deploy production:**

- [ ] Đổi `SECRET_KEY` thành chuỗi ngẫu nhiên (≥32 ký tự)
- [ ] Đặt mật khẩu MySQL mạnh
- [ ] Giới hạn `allow_origins` trong CORS (thay `"*"` bằng domain thực)
- [ ] Bật HTTPS (Nginx + Let's Encrypt hoặc Cloudflare)
- [ ] Đổi mật khẩu tài khoản admin mặc định
- [ ] Sao lưu database định kỳ

---

## License

Proprietary — Tu's Coffee © 2026
