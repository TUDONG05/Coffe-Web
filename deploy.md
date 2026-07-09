# Hướng Dẫn Triển Khai — Highlands Coffee FastAPI trên CentOS 7

## Yêu Cầu Hệ Thống

| Thành phần | Phiên bản tối thiểu |
|---|---|
| CentOS | 7.x |
| Python | 3.9+ |
| MySQL | 5.7+ |
| Nginx | 1.16+ |
| Certbot | mới nhất |

---

## 1. Chuẩn Bị Server

### 1.1 Cập nhật hệ thống

```bash
sudo yum update -y
sudo yum install -y epel-release
sudo yum install -y git curl wget vim unzip
```

### 1.2 Cài Python 3.9+

CentOS 7 mặc định chỉ có Python 3.6. Cài từ SCL hoặc build từ nguồn:

```bash
# Cài từ IUS repository
sudo yum install -y https://repo.ius.io/ius-release-el7.rpm
sudo yum install -y python39 python39-pip python39-devel

# Kiểm tra
python3.9 --version
```

### 1.3 Cài MySQL 5.7

```bash
sudo rpm -ivh https://dev.mysql.com/get/mysql57-community-release-el7-11.noarch.rpm
sudo yum install -y mysql-community-server mysql-community-devel

# Khởi động MySQL
sudo systemctl start mysqld
sudo systemctl enable mysqld

# Lấy mật khẩu tạm thời
sudo grep 'temporary password' /var/log/mysqld.log

# Đặt lại mật khẩu root
sudo mysql_secure_installation
```

### 1.4 Tạo database và user

```sql
-- Đăng nhập MySQL
mysql -u root -p

-- Tạo database
CREATE DATABASE highlands_coffee CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Tạo user riêng (không dùng root)
CREATE USER 'highlands_user'@'localhost' IDENTIFIED BY 'StrongPass@2026!';
GRANT ALL PRIVILEGES ON highlands_coffee.* TO 'highlands_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 2. Triển Khai Ứng Dụng

### 2.1 Tạo user hệ thống

```bash
sudo useradd -m -s /bin/bash highlands
sudo passwd highlands
```

### 2.2 Clone code lên server

```bash
sudo su - highlands
git clone <your-repo-url> /home/highlands/app
cd /home/highlands/app/web-prj
```

> Hoặc upload thủ công qua SCP:
> ```bash
> scp -r ./web-prj highlands@<server-ip>:/home/highlands/app/
> ```

### 2.3 Tạo virtual environment và cài dependencies

```bash
cd /home/highlands/app/web-prj
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # production WSGI runner
```

### 2.4 Cấu hình biến môi trường

```bash
cp .env.example .env
vim .env
```

Nội dung `.env` trên production:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=highlands_user
MYSQL_PASSWORD=StrongPass@2026!
MYSQL_DB=highlands_coffee
SECRET_KEY=<random-64-char-string>   # openssl rand -hex 32
```

> Tạo SECRET_KEY mạnh:
> ```bash
> openssl rand -hex 32
> ```

### 2.5 Khởi tạo database

```bash
source venv/bin/activate
python migrate_db.py
python create_admin.py
```

---

## 3. Cấu Hình Systemd Service

Tạo file service để tự khởi động khi reboot:

```bash
sudo vim /etc/systemd/system/highlands.service
```

```ini
[Unit]
Description=Highlands Coffee FastAPI App
After=network.target mysqld.service

[Service]
Type=exec
User=highlands
Group=highlands
WorkingDirectory=/home/highlands/app/web-prj
EnvironmentFile=/home/highlands/app/web-prj/.env
ExecStart=/home/highlands/app/web-prj/venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/highlands/access.log \
    --error-logfile /var/log/highlands/error.log \
    highlands_app:app
Restart=always
RestartSec=5
StandardOutput=append:/var/log/highlands/stdout.log
StandardError=append:/var/log/highlands/stderr.log

[Install]
WantedBy=multi-user.target
```

Tạo thư mục log và kích hoạt service:

```bash
sudo mkdir -p /var/log/highlands
sudo chown highlands:highlands /var/log/highlands

sudo systemctl daemon-reload
sudo systemctl enable highlands
sudo systemctl start highlands
sudo systemctl status highlands
```

Kiểm tra app đang chạy:

```bash
curl http://127.0.0.1:8000/health
```

---

## 4. Cài và Cấu Hình Nginx

### 4.1 Cài Nginx

```bash
sudo yum install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 4.2 Cấu hình Nginx (HTTP trước, HTTPS sau)

```bash
sudo vim /etc/nginx/conf.d/highlands.conf
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Tạm thời serve HTTP để Certbot xác thực
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL — sẽ được Certbot tự điền
    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Static files phục vụ trực tiếp qua Nginx (nhanh hơn FastAPI)
    location /static/ {
        alias /home/highlands/app/web-prj/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy đến FastAPI
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
        client_max_body_size 20M;
    }

    # Log
    access_log /var/log/nginx/highlands_access.log;
    error_log  /var/log/nginx/highlands_error.log;
}
```

Kiểm tra cấu hình và reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 5. Cài SSL với Let's Encrypt (Certbot)

### 5.1 Cài Certbot

```bash
sudo yum install -y certbot python2-certbot-nginx
```

> Nếu lỗi do Python 2, dùng pip3:
> ```bash
> sudo pip3 install certbot certbot-nginx
> ```

### 5.2 Mở firewall

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 5.3 Xin chứng chỉ SSL

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com \
    --non-interactive --agree-tos --email admin@yourdomain.com
```

Certbot sẽ tự động chỉnh sửa file `highlands.conf` để điền đường dẫn SSL.

### 5.4 Kiểm tra tự động renew

```bash
# Chạy thử dry-run
sudo certbot renew --dry-run

# Certbot tự cài cron job, kiểm tra:
sudo crontab -l
# Hoặc kiểm tra systemd timer
sudo systemctl list-timers | grep certbot
```

---

## 6. Cấu Hình Tường Lửa (Firewalld)

```bash
# Chỉ mở 80, 443 ra ngoài. Port 8000 chỉ nội bộ
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload

# Xác nhận
sudo firewall-cmd --list-all
```

---

## 7. Kiểm Tra Sau Triển Khai

```bash
# App service
sudo systemctl status highlands

# Nginx
sudo systemctl status nginx

# MySQL
sudo systemctl status mysqld

# HTTP redirect
curl -I http://yourdomain.com

# HTTPS
curl -I https://yourdomain.com

# API health check
curl https://yourdomain.com/health

# Logs ứng dụng
sudo tail -f /var/log/highlands/stderr.log

# Logs Nginx
sudo tail -f /var/log/nginx/highlands_error.log
```

---

## 8. Cập Nhật Code (Zero-downtime)

```bash
sudo su - highlands
cd /home/highlands/app/web-prj

# Pull code mới
git pull origin main

# Cài thêm dependency nếu có thay đổi requirements.txt
source venv/bin/activate
pip install -r requirements.txt

# Chạy migration nếu có thay đổi schema
python migrate_db.py

# Restart app
sudo systemctl restart highlands

# Kiểm tra
sudo systemctl status highlands
```

---

## 9. Cấu Hình SELinux (Nếu Bật)

CentOS 7 bật SELinux theo mặc định, cần cho phép Nginx kết nối upstream:

```bash
# Kiểm tra SELinux status
sestatus

# Cho phép Nginx proxy đến backend
sudo setsebool -P httpd_can_network_connect 1

# Nếu gặp lỗi permission với static files
sudo chcon -Rt httpd_sys_content_t /home/highlands/app/web-prj/static/
```

---

## 10. Backup Database

Tạo cron job backup tự động hàng ngày:

```bash
sudo vim /etc/cron.d/highlands-backup
```

```cron
0 2 * * * highlands mysqldump -u highlands_user -pStrongPass@2026! highlands_coffee | gzip > /home/highlands/backups/db_$(date +\%Y\%m\%d).sql.gz
```

```bash
mkdir -p /home/highlands/backups
```

---

## Cấu Trúc Thư Mục Trên Server

```
/home/highlands/
├── app/
│   └── web-prj/
│       ├── .env                  # biến môi trường (không commit git)
│       ├── highlands_app.py
│       ├── requirements.txt
│       ├── venv/
│       ├── static/
│       └── templates/
├── backups/                      # backup database
└── ...

/var/log/highlands/               # app logs
/var/log/nginx/                   # nginx logs
/etc/nginx/conf.d/highlands.conf  # nginx config
/etc/systemd/system/highlands.service
/etc/letsencrypt/                 # SSL certificates
```

---

## Troubleshooting

| Vấn đề | Kiểm tra |
|---|---|
| App không khởi động | `journalctl -u highlands -n 50` |
| Nginx lỗi 502 Bad Gateway | App chưa chạy: `systemctl status highlands` |
| SSL không hoạt động | `certbot certificates` — kiểm tra cert còn hạn |
| Database connection refused | `systemctl status mysqld`, kiểm tra `.env` |
| SELinux block | `audit2why < /var/log/audit/audit.log` |
| Static files 404 | Kiểm tra `alias` trong nginx config và quyền thư mục |
