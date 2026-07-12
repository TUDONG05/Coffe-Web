"""
Webhook endpoints for third-party payment notifications.
  POST /api/webhooks/casso  — Casso.vn / Casso Flow webhook
  POST /api/webhooks/sepay  — SePay webhook
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
SEPAY_API_KEY      = os.getenv("SEPAY_API_KEY", "")

# Matches: DH5, DH 5, DH-5, TUSCOFFEE DH5, etc.
_ORDER_REF_RE = re.compile(r"DH\s*(\d+)", re.IGNORECASE)


def _find_and_mark_paid(txn: dict, db: Session, source: str) -> bool:
    """Parse a transaction dict, find the order, mark it paid. Returns True if matched."""
    desc   = str(txn.get("description", "")
                 or txn.get("content", "")          # SePay uses 'content'
                 or txn.get("transaction_content", "")).upper()
    amount = int(txn.get("amount", 0)
                 or txn.get("transferAmount", 0)    # SePay alternate key
                 or 0)

    m = _ORDER_REF_RE.search(desc)
    if not m:
        return False

    order_id = int(m.group(1))
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order or order.payment_status == "paid":
        return False

    if amount and amount != order.total:
        logger.warning("%s: order #%d amount mismatch — expected %d got %d",
                       source, order_id, order.total, amount)

    order.payment_status = "paid"
    db.commit()
    logger.info("%s: order #%d marked paid (amount=%d)", source, order_id, amount)
    return True


# ── Casso ────────────────────────────────────────────────────

@router.post("/casso")
async def casso_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Casso / Casso Flow sends POST on bank transfer.
    Supports both {error:0, data:[...]} and flat single-object format.
    """
    try:
        body = await request.json()
    except Exception:
        return {"success": False, "error": "invalid json"}

    if CASSO_SECURE_TOKEN:
        received = (
            request.headers.get("secure-token")
            or request.headers.get("x-casso-secret")
            or (body.get("secure_token", "") if isinstance(body, dict) else "")
        )
        if received != CASSO_SECURE_TOKEN:
            logger.warning("Casso webhook: invalid secure token")
            return {"success": False, "error": "unauthorized"}

    if isinstance(body, dict):
        transactions = body.get("data") or []
        if not transactions and "id" in body:
            transactions = [body]
    elif isinstance(body, list):
        transactions = body
    else:
        transactions = []

    matched = sum(_find_and_mark_paid(t, db, "Casso") for t in transactions)
    return {"success": True, "matched": matched}


# ── SePay ────────────────────────────────────────────────────

@router.post("/sepay")
async def sepay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    SePay sends POST on bank transfer.
    Header: Authorization: Apikey {SEPAY_API_KEY}
    Body: { id, gateway, transactionDate, accountNumber, content,
            transferType, transferAmount, accumulated, referenceCode, ... }
    """
    try:
        body = await request.json()
    except Exception:
        return {"success": False, "error": "invalid json"}

    if SEPAY_API_KEY:
        auth = request.headers.get("Authorization", "")
        expected = f"Apikey {SEPAY_API_KEY}"
        if auth != expected:
            logger.warning("SePay webhook: invalid API key")
            return {"success": False, "error": "unauthorized"}

    # SePay sends a single transaction object (not a list)
    transactions = [body] if isinstance(body, dict) else (body if isinstance(body, list) else [])

    matched = sum(_find_and_mark_paid(t, db, "SePay") for t in transactions)
    return {"success": True, "matched": matched}
