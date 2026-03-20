"""
Admin News Management endpoints:
  GET /api/admin/news          — List news (paginated, filterable)
  POST /api/admin/news         — Create news
  GET /api/admin/news/{id}     — Get news details
  PUT /api/admin/news/{id}     — Update news
  DELETE /api/admin/news/{id}  — Delete news (soft delete)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin

router = APIRouter(prefix="/api/admin/news", tags=["admin-news"])


class NewsCreate(BaseModel):
    title: str
    excerpt: Optional[str] = None
    content: str
    tag: Optional[str] = None
    emoji: Optional[str] = "📰"


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    tag: Optional[str] = None
    emoji: Optional[str] = None
    is_active: Optional[int] = None


class NewsOut(BaseModel):
    id: int
    title: str
    excerpt: Optional[str]
    content: str
    tag: Optional[str]
    emoji: str
    published_at: Optional[str]
    is_active: int

    class Config:
        from_attributes = True


class PaginatedNews(BaseModel):
    items: list[NewsOut]
    total: int
    skip: int
    limit: int
    has_next: bool


@router.get("", response_model=PaginatedNews)
def list_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    tag: Optional[str] = None,
    is_active: Optional[int] = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(models.News)

    if tag:
        query = query.filter(models.News.tag == tag)

    if search:
        query = query.filter(
            models.News.title.ilike(f"%{search}%") |
            models.News.content.ilike(f"%{search}%")
        )

    if is_active is not None:
        query = query.filter(models.News.is_active == is_active)

    total = query.count()
    items = query.order_by(models.News.id.desc()).offset(skip).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": skip + limit < total
    }


@router.post("", response_model=NewsOut, status_code=201)
def create_news(
    body: NewsCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    news = models.News(
        title=body.title,
        excerpt=body.excerpt,
        content=body.content,
        tag=body.tag or "Tin Tuc",
        emoji=body.emoji,
        published_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        is_active=1
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    return news


@router.get("/{news_id}", response_model=NewsOut)
def get_news(
    news_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Tin tuc khong ton tai")
    return news


@router.put("/{news_id}", response_model=NewsOut)
def update_news(
    news_id: int,
    body: NewsUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Tin tuc khong ton tai")

    if body.title is not None:
        news.title = body.title
    if body.excerpt is not None:
        news.excerpt = body.excerpt
    if body.content is not None:
        news.content = body.content
    if body.tag is not None:
        news.tag = body.tag
    if body.emoji is not None:
        news.emoji = body.emoji

    db.commit()
    db.refresh(news)
    return news


@router.patch("/{news_id}", response_model=NewsOut)
def update_news_status(
    news_id: int,
    body: NewsUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update news status (is_active field only)."""
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Tin tuc khong ton tai")

    if body.is_active is not None:
        news.is_active = body.is_active

    db.commit()
    db.refresh(news)
    return news


@router.delete("/{news_id}")
def delete_news(
    news_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Tin tuc khong ton tai")

    # Soft delete
    news.is_active = 0
    db.commit()

    return {"detail": "Tin tuc da xoa"}
