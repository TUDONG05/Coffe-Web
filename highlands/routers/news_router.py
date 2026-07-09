"""
News endpoints:
  GET /api/news       — list all news (optional ?tag= filter)
  GET /api/news/{id}  — news detail
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
    emoji: Optional[str]
    published_at: Optional[str]

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
