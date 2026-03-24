"""
Highlands Coffee — FastAPI Application Entry Point
Serves the frontend HTML and mounts all API routers.
"""
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    chatbot_router,
)
from highlands.database import SessionLocal
from highlands import models
from highlands.services.menu_rag_service import menu_rag

app = FastAPI(title="Highlands Coffee", version="2.0.0", docs_url="/docs")


@app.on_event("startup")
def load_menu_index():
    """Build TF-IDF chatbot index từ DB khi app khởi động."""
    db = SessionLocal()
    try:
        products = db.query(models.Product).filter(models.Product.is_active == 1).all()
        menu_rag.build_index(products)
    finally:
        db.close()

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

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

# Chatbot API
app.include_router(chatbot_router.router)


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def render(filename: str) -> HTMLResponse:
    with open(os.path.join(TEMPLATES_DIR, filename), encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── Frontend ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    return render("highlands-coffee.html")


@app.get("/admin", response_class=HTMLResponse)
async def admin():
    return render("admin-panel.html")


@app.get("/about", response_class=HTMLResponse)
async def about():
    return render("about.html")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Highlands Coffee API v2"}
