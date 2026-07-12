# ☕ Tu's Coffee — Web Application

Ứng dụng web thương mại điện tử cho chuỗi cà phê **Tu's Coffee**, xây dựng bằng **FastAPI** (backend) và **HTML/CSS/Vanilla JavaScript** (frontend SPA). Hệ thống gồm hai giao diện riêng biệt: trang khách hàng và trang quản trị.

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-5.7+-4479A1?logo=mysql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?logo=javascript&logoColor=black)
![JWT](https://img.shields.io/badge/JWT-HS256-000000?logo=jsonwebtokens&logoColor=white)
![Google OAuth](https://img.shields.io/badge/Google_OAuth-2.0-4285F4?logo=google&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-TF--IDF-F7931E?logo=scikitlearn&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-499848?logo=gunicorn&logoColor=white)

---

## ✨ Tính năng

### 👤 Giao diện khách hàng (`/`)

**🔐 Tài khoản & Xác thực**
- Đăng ký tài khoản với xác thực **OTP qua email** (Gmail SMTP), tặng 50 điểm Rewards
- Đăng nhập bằng **email/mật khẩu** hoặc **Google OAuth** (Sign in with Google)
- **Quên mật khẩu** — luồng 3 bước: nhập email → nhận OTP reset → đặt mật khẩu mới
- Đăng xuất, xem & cập nhật hồ sơ cá nhân (tên, số điện thoại, địa chỉ)
- Đổi mật khẩu
- Validation số điện thoại Việt Nam (10 chữ số, bắt đầu 03/05/07/08/09)

**☕ Menu & Tìm kiếm**
- Duyệt 30+ sản phẩm, lọc theo danh mục (Cà phê, Trà, Freeze, Thức ăn, Combo)
- Tìm kiếm sản phẩm theo tên hoặc danh mục (thanh tìm kiếm menu & nút tìm kiếm navbar)
- Xem ảnh sản phẩm thực tế

**🛒 Giỏ hàng & Đặt hàng**
- Thêm sản phẩm vào giỏ hàng, điều chỉnh số lượng
- Đặt hàng online — **yêu cầu đăng nhập** (điểm Rewards được tích ngay sau mỗi đơn)
- Chọn phương thức thanh toán: **Tiền mặt** hoặc **Chuyển khoản QR** (VietQR)
- Quét mã QR thanh toán ngay sau khi đặt (MB Bank — 010320058686 DONG VAN TU)
- Đơn QR tự động chuyển trạng thái `payment_status = paid`
- Xem lịch sử đơn hàng (trạng thái, phương thức thanh toán, chi tiết items)
- Huỷ đơn hàng đang chờ xử lý

**⭐ Đánh giá sản phẩm**
- Gửi đánh giá (1–5 sao + bình luận) cho sản phẩm đã mua
- Chỉ tài khoản có đơn hàng `done` / `confirmed` chứa sản phẩm mới được đánh giá
- Xem danh sách đánh giá và điểm trung bình của từng sản phẩm

**🎁 Tu's Coffee Rewards**
- Trang Rewards riêng biệt với 3 tầng: Bronze / Silver / Gold
- Tích điểm khi đặt hàng: 10.000đ = 1 điểm
- Hiển thị điểm hiện tại, toast thông báo điểm tích sau mỗi đơn
- Catalog đổi thưởng (đồ uống miễn phí, voucher, quà tặng)

**📰 Nội dung**
- Xem khuyến mãi đang áp dụng (kèm ảnh minh hoạ)
- Đọc tin tức & bài viết mới nhất (kèm ảnh bìa)
- Tìm kiếm cửa hàng theo thành phố, lọc theo từ khóa
- Trang Giới thiệu (About) — ban lãnh đạo, câu chuyện thương hiệu

---

### 🛡️ Giao diện quản trị (`/admin`)

**📊 Dashboard**
- Thống kê tổng quan: tổng sản phẩm, đơn hàng, tài khoản, doanh thu
- Bảng đơn hàng gần đây

**📦 Quản lý nội dung (CRUD đầy đủ)**
- **Sản phẩm** — tìm kiếm, lọc theo danh mục/giá, phân trang, toggle kích hoạt, **upload ảnh sản phẩm** (JPEG/PNG/WebP, tối đa 5MB)
- **Đơn hàng** — cập nhật trạng thái, xem chi tiết items, cột Thanh Toán (paid/unpaid + phương thức)
- **Tài khoản** — hiển thị role, điểm Rewards; lọc theo role (`admin` / `user`) và trạng thái
- **Tin tức** — tìm kiếm, lọc theo thẻ, **upload ảnh bìa bài viết**
- **Cửa hàng** — quản lý địa điểm toàn hệ thống
- **Danh mục** — quản lý danh mục sản phẩm
- **Tài khoản Admin** — tạo, phân quyền, khóa/mở tài khoản nội bộ

**⚙️ Tính năng chung**
- Xác thực JWT, phân quyền role `admin`
- Soft delete — không xoá vật lý
- Toast thông báo sau mỗi thao tác
- Phân trang cho danh sách lớn

---

## 🖥️ Giao diện ứng dụng

| Trang | URL | Mô tả |
|-------|-----|-------|
| Khách hàng | `http://localhost:8000/` | SPA: menu, giỏ hàng, rewards, tin tức, cửa hàng |
| Quản trị | `http://localhost:8000/admin` | Dashboard CRUD đầy đủ |
| Giới thiệu | `http://localhost:8000/about` | Thông tin thương hiệu Tu's Coffee |
| Swagger UI | `http://localhost:8000/docs` | Tài liệu API tương tác |
| Health check | `http://localhost:8000/health` | Kiểm tra trạng thái server |

---

## 📦 Công nghệ sử dụng

| Thành phần | Công nghệ | Phiên bản |
|------------|-----------|-----------|
| ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white&style=flat-square) Backend framework | FastAPI | 0.104.1 |
| ![Uvicorn](https://img.shields.io/badge/-Uvicorn-499848?logo=gunicorn&logoColor=white&style=flat-square) ASGI server | Uvicorn | 0.24.0 |
| ![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white&style=flat-square) ORM | SQLAlchemy | 2.0.23 |
| ![MySQL](https://img.shields.io/badge/-MySQL-4479A1?logo=mysql&logoColor=white&style=flat-square) Database | MySQL | 5.7+ |
| 🔌 DB driver | PyMySQL | 1.1.0 |
| ![Pydantic](https://img.shields.io/badge/-Pydantic-E92063?logo=pydantic&logoColor=white&style=flat-square) Validation | Pydantic | v2.5.0 |
| ![JWT](https://img.shields.io/badge/-JWT-000000?logo=jsonwebtokens&logoColor=white&style=flat-square) Xác thực | JWT (HS256) + Bcrypt | python-jose 3.3.0 / bcrypt 4.1.1 |
| ![Google](https://img.shields.io/badge/-Google_OAuth-4285F4?logo=google&logoColor=white&style=flat-square) Google OAuth | google-auth | 2.29.0 |
| 📧 Email OTP | Gmail SMTP (smtplib) | — |
| 📁 File upload | python-multipart | ≥0.0.9 |
| ⚙️ Config | python-dotenv | 1.0.0 |
| 🗂️ File tĩnh | aiofiles | ≥23.0.0 |
| ![scikit-learn](https://img.shields.io/badge/-scikit--learn-F7931E?logo=scikitlearn&logoColor=white&style=flat-square) AI / Chatbot | scikit-learn | ≥1.3.0 |
| 🌐 HTTP client | httpx | ≥0.27.0 |
| 📊 Export | openpyxl | ≥3.1.0 |
| ![HTML5](https://img.shields.io/badge/-HTML5-E34F26?logo=html5&logoColor=white&style=flat-square) ![CSS3](https://img.shields.io/badge/-CSS3-1572B6?logo=css3&logoColor=white&style=flat-square) ![JS](https://img.shields.io/badge/-JavaScript-F7DF1E?logo=javascript&logoColor=black&style=flat-square) Frontend | HTML5, CSS3, Vanilla JavaScript (SPA) | — |
| 💳 Thanh toán QR | VietQR free API | — |
| ![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white&style=flat-square) Runtime | Python | 3.10+ |

---

## 📁 Cấu trúc source code

```
Coffe-Web/
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
│   ├── config.py             # Cấu hình: DATABASE_URL, SECRET_KEY, JWT expiry, Google/Gmail keys
│   ├── database.py           # SQLAlchemy engine + SessionLocal + get_db()
│   ├── models.py             # ORM models: User, Category, Product, Order, OrderItem,
│   │                         #             ProductReview, Store, News, Promotion
│   ├── auth_utils.py         # Hash mật khẩu, tạo/xác minh JWT, require_admin
│   ├── seed_db.py            # Seed dữ liệu mẫu
│   │
│   ├── routers/
│   │   │
│   │   ├── ── Public API (không cần xác thực) ──
│   │   ├── auth_router.py          # /api/auth — OTP, đăng ký, đăng nhập, Google OAuth, hồ sơ
│   │   ├── products_router.py      # /api/products — danh sách, tìm kiếm
│   │   ├── orders_router.py        # /api/orders — tạo đơn, lịch sử, huỷ
│   │   ├── reviews_router.py       # /api/reviews — đánh giá sản phẩm
│   │   ├── stores_router.py        # /api/stores
│   │   ├── news_router.py          # /api/news
│   │   ├── promotions_router.py    # /api/promotions
│   │   ├── chatbot_router.py       # /api/chat — AI tư vấn + đặt hàng qua chat
│   │   │
│   │   └── ── Admin API (yêu cầu JWT role=admin) ──
│   │       ├── admin_dashboard_router.py   # /api/admin/dashboard
│   │       ├── admin_products_router.py    # /api/admin/products (+ image upload)
│   │       ├── admin_orders_router.py      # /api/admin/orders
│   │       ├── admin_customers_router.py   # /api/admin/customers
│   │       ├── admin_news_router.py        # /api/admin/news (+ image upload)
│   │       ├── admin_stores_router.py      # /api/admin/stores
│   │       ├── admin_categories_router.py  # /api/admin/categories
│   │       └── admin_users_router.py       # /api/admin/users
│   │
│   └── services/
│       ├── email_service.py        # Gmail SMTP: OTP đăng ký & reset mật khẩu (TTL 10 phút, tách key theo purpose)
│       └── menu_rag_service.py     # RAG service cho chatbot gợi ý menu (TF-IDF)
│
├── templates/
│   ├── highlands-coffee.html # Trang khách hàng (SPA)
│   ├── admin-panel.html      # Trang quản trị
│   └── about.html            # Trang giới thiệu
│
└── static/
    ├── css/
    │   ├── main.css          # Style trang khách hàng (responsive)
    │   ├── admin.css         # Style trang quản trị
    │   └── about.css         # Style trang giới thiệu (responsive)
    └── images/
        ├── logo/             # Logo thương hiệu
        ├── products/         # Ảnh sản phẩm (upload qua admin)
        └── news/             # Ảnh bài viết (upload qua admin)
```

---

## 🗄️ Schema Database

### Các bảng

| Bảng | Mô tả |
|------|-------|
| `users` | Tài khoản người dùng (role: admin / user, hỗ trợ Google OAuth) |
| `categories` | Danh mục sản phẩm |
| `products` | Sản phẩm (tên, danh mục, giá, mô tả, emoji, ảnh) |
| `product_reviews` | Đánh giá sản phẩm (sao + bình luận, chỉ khách đã mua) |
| `orders` | Đơn hàng (tên khách, SĐT, địa chỉ, tổng tiền, trạng thái, thanh toán) |
| `order_items` | Chi tiết từng sản phẩm trong đơn hàng |
| `stores` | Cửa hàng (địa chỉ, quận, thành phố, giờ mở cửa) |
| `news` | Tin tức & bài viết (kèm ảnh bìa) |
| `promotions` | Khuyến mãi đang áp dụng (kèm ảnh minh hoạ) |

### Chi tiết các model

**`users`**
```
id            INT          PK, auto-increment
name          VARCHAR(100) NOT NULL
email         VARCHAR(150) UNIQUE, NOT NULL
phone         VARCHAR(20)
hashed_pwd    VARCHAR(255) NOT NULL
google_id     VARCHAR(255) UNIQUE (NULL nếu đăng nhập thường)
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
image_url   VARCHAR(300)            -- đường dẫn ảnh upload
is_active   INT          DEFAULT 1
```

**`product_reviews`**
```
id          INT          PK
product_id  INT          FK → products.id
user_id     INT          FK → users.id
stars       INT          NOT NULL   -- 1-5
comment     TEXT
created_at  DATETIME     DEFAULT now()
```

**`orders`**
```
id             INT          PK
user_id        INT          FK → users.id NOT NULL (yêu cầu đăng nhập)
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
image_url    VARCHAR(300)            -- ảnh bìa bài viết
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
image_url   VARCHAR(300)            -- ảnh minh hoạ
tag         VARCHAR(50)  -- 'HOT' | 'NEW' | 'SALE'
valid_until VARCHAR(50)
is_active   INT          DEFAULT 1
```

### Quan hệ

```
users ──────────────────── orders            (1 : nhiều)
users ──────────────────── product_reviews   (1 : nhiều)
orders ─────────────────── order_items       (1 : nhiều)
order_items ────────────── products          (nhiều : 1)
product_reviews ─────────── products         (nhiều : 1)
```

> Soft delete qua cờ `is_active` — không xoá vật lý dữ liệu.

---

## 🚀 Cài đặt

### Yêu cầu

- ![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white&style=flat-square)
- ![MySQL](https://img.shields.io/badge/MySQL-5.7+-4479A1?logo=mysql&logoColor=white&style=flat-square)
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
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=highlands_coffee

# JWT
SECRET_KEY=your-random-secret-key-min-32-chars

# Google OAuth (tuỳ chọn — bỏ trống nếu không dùng)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# Gmail SMTP — xác thực OTP khi đăng ký (tuỳ chọn)
GMAIL_USER=your-gmail@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password

# Chatbot (tuỳ chọn — bỏ trống nếu không dùng Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

> ⚠️ Bắt buộc đổi `SECRET_KEY` thành chuỗi ngẫu nhiên trước khi deploy production.

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

> ⚠️ Đổi mật khẩu ngay sau khi đăng nhập lần đầu.

---

## ▶️ Chạy ứng dụng

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

## ⏹️ Dừng ứng dụng

```bash
# Nhấn Ctrl+C nếu chạy foreground

# Windows
taskkill /F /IM python.exe

# Linux/macOS
pkill -f "uvicorn highlands_app"
# hoặc
lsof -i :8000 && kill -9 <PID>
```

---

## 🤖 AI Chatbot

Tu's Coffee tích hợp chatbot AI tư vấn thực đơn và hỗ trợ đặt hàng trực tiếp trên giao diện khách hàng.

### Kiến trúc

```
Người dùng
   │  nhập câu hỏi
   ▼
Frontend (SSE stream)
   │  POST /api/chat/stream
   ▼
ChatbotRouter
   │  1. Phát hiện intent đặt hàng (từ khoá: "đặt", "mua", "gọi món", …)
   │  2. Tìm món liên quan (RAG)
   │  3. Build system prompt với context
   ▼
MenuRAGService (TF-IDF)          ←── DB sản phẩm
   │  trả top-4 món phù hợp
   ▼
Ollama (local LLM)               ←── model qwen2.5:3b
   │  stream token
   ▼
Frontend render từng token (streaming)
   │
   └── Nếu có intent đặt hàng: phát SSE event `order_form`
       → Frontend hiển thị form đặt hàng ngay trong khung chat
```

### Cách hoạt động

1. **RAG**: Câu hỏi được vector hoá bằng **TF-IDF** (char n-gram 2–4, tốt với tiếng Việt), tìm top-4 sản phẩm liên quan nhất qua cosine similarity
2. **Intent đặt hàng**: Nếu phát hiện từ khoá đặt hàng, chatbot song song trích xuất tên món → inject SSE event `order_form` kèm danh sách items vào stream
3. **Streaming**: Dùng **SSE (Server-Sent Events)** — response hiển thị từng token ngay khi Ollama trả về
4. **History**: Giữ 6 lượt hội thoại gần nhất để chatbot nhớ ngữ cảnh

### Yêu cầu để chạy chatbot

```bash
# Cài Ollama (ollama.com)
ollama pull qwen2.5:3b
ollama serve
```

Mặc định Ollama chạy tại `http://localhost:11434`. Có thể override qua `.env` với `OLLAMA_BASE_URL` và `OLLAMA_MODEL`.

> Nếu không cài Ollama, các tính năng khác vẫn hoạt động bình thường.

### API chatbot

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/chat/stream` | Chat, trả về SSE token stream |
| POST | `/api/chat/reload-menu` | Reload TF-IDF index sau khi admin sửa sản phẩm |
| GET | `/api/chat/status` | Kiểm tra trạng thái (số món đã index, model đang dùng) |

---

## 🔌 API Endpoints

### Public API

#### 🔐 Xác thực (`/api/auth`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/auth/send-otp` | Gửi mã OTP 6 số về email để xác thực đăng ký (TTL 10 phút) |
| POST | `/api/auth/register` | Đăng ký — cần xác thực OTP, tặng 50 điểm Rewards |
| POST | `/api/auth/login` | Đăng nhập email/mật khẩu, trả JWT |
| POST | `/api/auth/google/verify` | Đăng nhập / đăng ký qua Google OAuth |
| POST | `/api/auth/forgot-password` | Gửi OTP reset mật khẩu về email (TTL 10 phút) |
| POST | `/api/auth/reset-password` | Xác thực OTP và đặt lại mật khẩu mới |
| GET | `/api/auth/me` | Thông tin tài khoản hiện tại |
| PUT | `/api/auth/profile` | Cập nhật hồ sơ (validate SĐT Việt Nam) |
| PUT | `/api/auth/change-password` | Đổi mật khẩu |

#### ☕ Sản phẩm (`/api/products`)

| Method | Endpoint | Query Params |
|--------|----------|--------------|
| GET | `/api/products` | `category`, `q` (tìm theo tên / danh mục) |
| GET | `/api/products/{id}` | — |

#### 🛒 Đơn hàng (`/api/orders`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/orders` | Tạo đơn — **yêu cầu đăng nhập**, `payment_method: cash \| qr_transfer` |
| GET | `/api/orders/mine` | Lịch sử đơn (cần đăng nhập) |
| PATCH | `/api/orders/{id}/cancel` | Huỷ đơn `pending` |

#### ⭐ Đánh giá (`/api/reviews`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/reviews/product/{id}` | Lấy danh sách đánh giá + điểm trung bình sản phẩm |
| GET | `/api/reviews/can-review/{id}` | Kiểm tra user có được phép đánh giá không |
| POST | `/api/reviews` | Gửi đánh giá (cần đăng nhập, phải có đơn `done`/`confirmed`) |

#### 📰 Nội dung

| Method | Endpoint | Query Params |
|--------|----------|--------------|
| GET | `/api/stores` | `city`, `q` |
| GET | `/api/stores/cities` | — |
| GET | `/api/news` | `tag` |
| GET | `/api/promotions` | — |

---

### 🛡️ Admin API

> Header bắt buộc: `Authorization: Bearer <jwt_token>` — role `admin`

| Resource | Endpoints | Thao tác |
|----------|-----------|---------|
| Dashboard | `/api/admin/dashboard` | GET |
| Sản phẩm | `/api/admin/products` | GET (filter: category, search, price), POST, PUT, PATCH, DELETE |
| Ảnh sản phẩm | `/api/admin/products/{id}/image` | POST (multipart/form-data) |
| Đơn hàng | `/api/admin/orders` | GET (filter: status, date, price), GET/{id}, PATCH, DELETE |
| Tài khoản | `/api/admin/customers` | GET (filter: `role`, `status`, `search`), POST, PUT, PATCH, DELETE |
| Tin tức | `/api/admin/news` | GET (filter: tag), POST, PUT, PATCH, DELETE |
| Ảnh tin tức | `/api/admin/news/{id}/image` | POST (multipart/form-data) |
| Cửa hàng | `/api/admin/stores` | GET, POST, PUT, DELETE |
| Danh mục | `/api/admin/categories` | GET, POST, PUT, DELETE |
| Admin users | `/api/admin/users` | GET, POST, PUT, PATCH, DELETE |

---

## 🔒 Bảo mật

**✅ Đã triển khai:**
- Bcrypt hashing cho mật khẩu
- JWT HS256 với thời hạn 24 giờ
- Phân quyền theo role: `admin` / `user`
- OTP 6 số qua Gmail SMTP — TTL 10 phút, tách biệt mục đích (`register` / `reset`) qua key `purpose:email`
- Luồng quên mật khẩu 3 bước an toàn — OTP reset độc lập với OTP đăng ký
- Google OAuth — xác thực token phía server qua `google-auth`; tài khoản Google không có `reset-password`
- Đặt hàng yêu cầu đăng nhập — loại bỏ khách vãng lai
- Validation số điện thoại Việt Nam (regex `^0[35789]\d{8}$`)
- Soft delete — không xoá dữ liệu vật lý
- Kiểm tra email duy nhất khi đăng ký
- Mật khẩu tối thiểu 6 ký tự
- Giới hạn loại file upload (JPEG/PNG/WebP) và kích thước (5MB)

**⚠️ Cần cấu hình trước khi deploy production:**

- [ ] Đổi `SECRET_KEY` thành chuỗi ngẫu nhiên (≥32 ký tự)
- [ ] Đặt mật khẩu MySQL mạnh
- [ ] Giới hạn `allow_origins` trong CORS (thay `"*"` bằng domain thực)
- [ ] Bật HTTPS (Nginx + Let's Encrypt hoặc Cloudflare)
- [ ] Đổi mật khẩu tài khoản admin mặc định
- [ ] Cấu hình `GMAIL_APP_PASSWORD` bằng Google App Password (không dùng mật khẩu Gmail thường)
- [ ] Sao lưu database định kỳ

---

## 📄 License

Proprietary — Tu's Coffee © 2026
