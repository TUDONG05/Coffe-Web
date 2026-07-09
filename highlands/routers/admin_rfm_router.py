"""
Admin RFM + K-Means customer segmentation.

Flow:
  1. Aggregate completed orders per user → Recency / Frequency / Monetary
  2. Min-max normalise RFM to [0, 1]
  3. Run K-Means clustering
  4. Map each cluster to a business label based on centroid position
  5. Return per-customer segment info + cluster summary
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from highlands import models
from highlands.auth_utils import require_admin
from highlands.database import get_db
from highlands.ml.kmeans import KMeans

router = APIRouter(prefix="/api/admin/rfm", tags=["admin-rfm"])


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class CustomerRFM(BaseModel):
    user_id: int
    name: str
    email: str
    recency_days: int
    frequency: int
    monetary: int
    cluster: int
    segment_label: str


class ClusterSummary(BaseModel):
    cluster: int
    segment_label: str
    count: int
    avg_recency_days: float
    avg_frequency: float
    avg_monetary: float


class RFMResult(BaseModel):
    n_clusters: int
    n_iter: int
    elapsed_ms: float
    customers: list[CustomerRFM]
    clusters: list[ClusterSummary]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _minmax(arr: np.ndarray) -> np.ndarray:
    lo = arr.min(axis=0)
    hi = arr.max(axis=0)
    rng = hi - lo
    rng[rng == 0] = 1.0
    return (arr - lo) / rng


_SEGMENT_PRIORITY = [
    # rules applied to normalised centroid (r_inv, f, m) — higher = better
    ("Champions",       lambda r, f, m: r >= 0.7 and f >= 0.6 and m >= 0.6),
    ("Loyal Customers", lambda r, f, m: r >= 0.5 and f >= 0.5),
    ("At-Risk",         lambda r, f, m: r < 0.5 and f >= 0.3),
    ("Lost Customers",  lambda r, f, m: True),
]


def _label_clusters(centroids_norm: np.ndarray) -> dict[int, str]:
    """
    Map normalised centroid (R_norm, F_norm, M_norm) → business label.
    R is inverted so low recency (recent buyer) scores high.
    """
    scored = []
    for i, c in enumerate(centroids_norm):
        r_inv = 1.0 - c[0]
        f, m  = c[1], c[2]
        scored.append((i, r_inv, f, m))

    # best overall score first
    order = sorted(scored, key=lambda x: x[1] + x[2] + x[3], reverse=True)

    assigned: dict[int, str] = {}
    used: set[str] = set()
    for idx, r_inv, f, m in order:
        for label, rule in _SEGMENT_PRIORITY:
            if label not in used and rule(r_inv, f, m):
                assigned[idx] = label
                used.add(label)
                break
        else:
            assigned[idx] = f"Cluster {idx}"

    return assigned


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.get("", response_model=RFMResult)
def get_rfm_segments(
    n_clusters: int = Query(4, ge=2, le=10, description="Số cụm K-Means"),
    max_iter: int = Query(300, ge=10, le=2000),
    epsilon: float = Query(1e-5, ge=1e-10),
    seed: int = Query(42),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Tính RFM từ đơn hàng hoàn thành, phân nhóm khách hàng bằng K-Means.

    - **Recency**  : số ngày kể từ lần mua gần nhất (thấp = tốt)
    - **Frequency**: tổng số đơn hàng đã hoàn thành
    - **Monetary** : tổng chi tiêu (VND)
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    orders = (
        db.query(models.Order, models.User)
        .join(models.User, models.Order.user_id == models.User.id)
        .filter(
            models.Order.user_id.isnot(None),
            models.Order.status == "done",
            models.Order.is_active == 1,
        )
        .all()
    )

    rfm_map: dict[int, dict] = {}
    for order, user in orders:
        uid = user.id
        if uid not in rfm_map:
            rfm_map[uid] = {"user": user, "last_order_date": order.created_at, "frequency": 0, "monetary": 0}
        e = rfm_map[uid]
        e["frequency"] += 1
        e["monetary"]  += order.total
        if order.created_at and (e["last_order_date"] is None or order.created_at > e["last_order_date"]):
            e["last_order_date"] = order.created_at

    if len(rfm_map) < n_clusters:
        raise HTTPException(
            status_code=422,
            detail=f"Cần ít nhất {n_clusters} khách hàng có đơn hoàn thành. Hiện có {len(rfm_map)}.",
        )

    user_ids = list(rfm_map.keys())
    raw_R = np.array([(now - rfm_map[uid]["last_order_date"]).days for uid in user_ids], dtype=float)
    raw_F = np.array([rfm_map[uid]["frequency"] for uid in user_ids], dtype=float)
    raw_M = np.array([rfm_map[uid]["monetary"]  for uid in user_ids], dtype=float)

    X_norm = _minmax(np.column_stack([raw_R, raw_F, raw_M]))

    km = KMeans(X_norm, n_clusters=n_clusters, max_iter=max_iter, epsilon=epsilon, seed=seed)
    labels, centroids_norm, n_iter = km.fit()

    segment_map = _label_clusters(centroids_norm)

    customers: list[CustomerRFM] = []
    for i, uid in enumerate(user_ids):
        cid = int(labels[i])
        customers.append(CustomerRFM(
            user_id=uid,
            name=rfm_map[uid]["user"].name,
            email=rfm_map[uid]["user"].email,
            recency_days=int(raw_R[i]),
            frequency=int(raw_F[i]),
            monetary=int(raw_M[i]),
            cluster=cid,
            segment_label=segment_map[cid],
        ))

    cluster_groups: dict[int, list[CustomerRFM]] = {c: [] for c in range(n_clusters)}
    for cust in customers:
        cluster_groups[cust.cluster].append(cust)

    cluster_summaries = []
    for cid in range(n_clusters):
        g = cluster_groups[cid]
        cluster_summaries.append(ClusterSummary(
            cluster=cid,
            segment_label=segment_map[cid],
            count=len(g),
            avg_recency_days=round(sum(c.recency_days for c in g) / len(g), 1) if g else 0.0,
            avg_frequency=round(sum(c.frequency for c in g) / len(g), 2) if g else 0.0,
            avg_monetary=round(sum(c.monetary for c in g) / len(g), 0) if g else 0.0,
        ))

    return RFMResult(
        n_clusters=n_clusters,
        n_iter=n_iter,
        elapsed_ms=round(km.elapsed * 1000, 2),
        customers=sorted(customers, key=lambda c: c.cluster),
        clusters=cluster_summaries,
    )
