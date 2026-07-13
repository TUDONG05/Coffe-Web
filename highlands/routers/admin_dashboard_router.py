"""Admin dashboard: revenue chart & top-selling products."""
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin
from highlands.models import vn_now

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])


def _date_range(period: str):
    now = vn_now()
    if period == "week":
        start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start = datetime(now.year, 1, 1)
    else:  # month (default)
        start = datetime(now.year, now.month, 1)
    return start, now


@router.get("/revenue")
def get_revenue(
    period: str = Query("month", pattern="^(week|month|year)$"),
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    start, now = _date_range(period)

    orders = (
        db.query(models.Order)
        .filter(models.Order.is_active == 1, models.Order.created_at >= start)
        .all()
    )

    if period == "week":
        # Last 7 days labelled Mon-Sun in Vietnamese
        day_names = ["CN", "T.Hai", "T.Ba", "T.Tư", "T.Năm", "T.Sáu", "T.Bảy"]
        rev_by_date: dict = defaultdict(int)
        cnt_by_date: dict = defaultdict(int)
        for o in orders:
            if o.created_at:
                d = o.created_at.date()
                rev_by_date[d] += o.total
                cnt_by_date[d] += 1

        labels, revenue, order_counts = [], [], []
        for i in range(7):
            d = (now - timedelta(days=6 - i)).date()
            name = day_names[d.isoweekday() % 7]
            labels.append(f"{name} {d.day}/{d.month}")
            revenue.append(rev_by_date.get(d, 0))
            order_counts.append(cnt_by_date.get(d, 0))

    elif period == "year":
        month_rev: dict = defaultdict(int)
        month_cnt: dict = defaultdict(int)
        for o in orders:
            if o.created_at:
                month_rev[o.created_at.month] += o.total
                month_cnt[o.created_at.month] += 1

        labels = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"]
        revenue = [month_rev.get(m, 0) for m in range(1, 13)]
        order_counts = [month_cnt.get(m, 0) for m in range(1, 13)]

    else:  # month — group by week within the month
        _, days_in_month = calendar.monthrange(now.year, now.month)
        num_weeks = (days_in_month - 1) // 7 + 1
        week_rev: dict = defaultdict(int)
        week_cnt: dict = defaultdict(int)
        for o in orders:
            if o.created_at and o.created_at.month == now.month:
                w = (o.created_at.day - 1) // 7
                week_rev[w] += o.total
                week_cnt[w] += 1

        labels, revenue, order_counts = [], [], []
        for w in range(num_weeks):
            d_start = w * 7 + 1
            d_end = min((w + 1) * 7, days_in_month)
            labels.append(f"Tuần {w + 1}\n({d_start}-{d_end}/{now.month})")
            revenue.append(week_rev.get(w, 0))
            order_counts.append(week_cnt.get(w, 0))

    return {"labels": labels, "revenue": revenue, "orders": order_counts}


@router.get("/top-products")
def get_top_products(
    period: str = Query("month", pattern="^(week|month|year)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    start, _ = _date_range(period)

    rows = (
        db.query(
            models.OrderItem.name,
            func.sum(models.OrderItem.quantity).label("total_qty"),
            func.sum(models.OrderItem.subtotal).label("total_revenue"),
        )
        .join(models.Order, models.OrderItem.order_id == models.Order.id)
        .filter(models.Order.is_active == 1, models.Order.created_at >= start)
        .group_by(models.OrderItem.name)
        .order_by(func.sum(models.OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "rank": i + 1,
            "name": row.name,
            "quantity": int(row.total_qty or 0),
            "revenue": int(row.total_revenue or 0),
        }
        for i, row in enumerate(rows)
    ]
