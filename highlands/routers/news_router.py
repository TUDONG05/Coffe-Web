"""
News endpoints:
  GET /api/news           — list all news (optional ?tag= filter)
  GET /api/news/{id}      — news detail
  POST /api/news/{id}/view — record a view (total + optionally unique)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from highlands.database import get_db
from highlands import models

router = APIRouter(prefix="/api/news", tags=["news"])


class NewsOut(BaseModel):
    id: int
    title: str
    excerpt: Optional[str]
    content: Optional[str]
    tag: Optional[str]
    image_url: Optional[str]
    video_url: Optional[str]
    published_at: Optional[str]
    view_count: int = 0
    unique_view_count: int = 0


class ViewPayload(BaseModel):
    is_new_viewer: bool = False

    class Config:
        from_attributes = True


@router.get("", response_model=list[NewsOut])
def list_news(
    tag: Optional[str] = Query(None, description="Filter by tag"),
    db: Session = Depends(get_db),
):
    query = db.query(models.News).filter(models.News.is_active == 1)
    if tag:
        query = query.filter(models.News.tag == tag)
    return query.order_by(models.News.id.desc()).all()


@router.get("/{news_id}", response_model=NewsOut)
def get_news(news_id: int, db: Session = Depends(get_db)):
    article = db.query(models.News).filter(
        models.News.id == news_id,
        models.News.is_active == 1,
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")
    return article


@router.post("/{news_id}/view", status_code=204)
def record_view(news_id: int, payload: ViewPayload, db: Session = Depends(get_db)):
    article = db.query(models.News).filter(
        models.News.id == news_id,
        models.News.is_active == 1,
    ).first()
    if not article:
        return
    article.view_count = (article.view_count or 0) + 1
    if payload.is_new_viewer:
        article.unique_view_count = (article.unique_view_count or 0) + 1
    db.commit()
