"""
Highlands Coffee — FastAPI Application Entry Point
Serves the frontend HTML and mounts all API routers.
"""
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Load .env if present (dev convenience)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from highlands.routers import auth_router, products_router, orders_router
from highlands.routers import stores_router, news_router, promotions_router
from highlands.routers import (
    admin_products_router,
    admin_orders_router,
    admin_stores_router,
    admin_categories_router,
    admin_customers_router,
    admin_dashboard_router,
    admin_news_router,
    admin_users_router,
)

app = FastAPI(title="Highlands Coffee", version="2.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ─────────────────────────────────────────
# Customer API
app.include_router(auth_router.router)
app.include_router(products_router.router)
app.include_router(orders_router.router)
app.include_router(stores_router.router)
app.include_router(news_router.router)
app.include_router(promotions_router.router)

# Admin API
app.include_router(admin_products_router.router)
app.include_router(admin_orders_router.router)
app.include_router(admin_stores_router.router)
app.include_router(admin_categories_router.router)
app.include_router(admin_customers_router.router)
app.include_router(admin_news_router.router)
app.include_router(admin_users_router.router)
app.include_router(admin_dashboard_router.router)


# ── Frontend ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(os.path.dirname(__file__), "highlands-coffee.html")
    with open(html_path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/admin", response_class=HTMLResponse)
async def admin():
    html_path = os.path.join(os.path.dirname(__file__), "admin-panel.html")
    with open(html_path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Highlands Coffee API v2"}
