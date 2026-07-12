"""
Webhook endpoints for third-party payment notifications.
  POST /api/webhooks/casso  — Casso.vn bank transfer webhook
"""
import os
import re
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from highlands.database import get_db
from highlands import models

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

CASSO_SECURE_TOKEN = os.getenv("CASSO_SECURE_TOKEN", "")

# Pattern: TUSCOFFEE DH5, TUSCOFFEE-DH5, DH5, etc.
_ORDER_REF_RE = re.compile(r"DH\s*(\d+)", re.IGNORECASE)


@router.post("/casso")
async def casso_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Casso.vn sends a POST when a bank transfer arrives.
    We match the description against TUSCOFFEE DH{id} and mark the order paid.
    """
    try:
        body = await request.json()
    except Exception:
        return {"success": False, "error": "invalid json"}

    # Verify secure token (header takes priority, fallback to body field)
    if CASSO_SECURE_TOKEN:
        received = (
            request.headers.get("secure-token")
            or request.headers.get("x-casso-secret")
            or (body.get("secure_token", "") if isinstance(body, dict) else "")
        )
        if received != CASSO_SECURE_TOKEN:
            # Return 200 so Casso doesn't retry, but do nothing
            logger.warning("Casso webhook: invalid secure token received")
            return {"success": False, "error": "unauthorized"}

    # Normalize to list — Casso sends {error:0, data:[...]} or a flat object
    if isinstance(body, dict):
        transactions = body.get("data") or []
        if not transactions and "id" in body:
            transactions = [body]
    elif isinstance(body, list):
        transactions = body
    else:
        transactions = []

    matched = 0
    for txn in transactions:
        desc   = str(txn.get("description", "")).upper()
        amount = int(txn.get("amount", 0))

        m = _ORDER_REF_RE.search(desc)
        if not m:
            continue

        order_id = int(m.group(1))
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order or order.payment_status == "paid":
            continue

        if amount != order.total:
            logger.warning(
                "Casso: order #%d amount mismatch — expected %d got %d",
                order_id, order.total, amount,
            )

        order.payment_status = "paid"
        db.commit()
        matched += 1
        logger.info("Casso: order #%d marked paid (amount=%d)", order_id, amount)

    return {"success": True, "matched": matched}
