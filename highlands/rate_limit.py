"""
Rate limiter đơn giản, lưu trong bộ nhớ tiến trình, giới hạn theo IP.

LƯU Ý: trên Vercel serverless mỗi request có thể rơi vào một instance khác nhau,
bộ đếm reset theo instance. Đây là hàng rào chống gọi nhầm/gọi dồn, KHÔNG phải
cơ chế chống lạm dụng. Muốn chặn thật cần backend chia sẻ (Redis/Upstash).
"""
import time
from collections import defaultdict

from fastapi import HTTPException, Request

# Khoá gộp "<tên endpoint>:<ip>" để mỗi endpoint có quota riêng.
_hits: dict[str, list[float]] = defaultdict(list)


def enforce_rate_limit(
    request: Request,
    *,
    key: str,
    max_hits: int,
    window: int = 60,
) -> None:
    """Raise HTTP 429 khi IP vượt quá max_hits lần gọi trong window giây."""
    ip = request.client.host if request.client else "unknown"
    bucket = f"{key}:{ip}"
    now = time.time()

    recent = [t for t in _hits[bucket] if now - t < window]
    if len(recent) >= max_hits:
        raise HTTPException(
            status_code=429,
            detail="Quá nhiều yêu cầu, vui lòng thử lại sau 1 phút",
        )
    recent.append(now)
    _hits[bucket] = recent
