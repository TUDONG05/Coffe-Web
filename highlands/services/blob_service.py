"""
Vercel Blob upload service.
Falls back to local filesystem when BLOB_READ_WRITE_TOKEN is not set (dev mode).
"""
import os
import httpx

BLOB_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN", "")
BLOB_API   = "https://blob.vercel-storage.com"


async def upload_image(content: bytes, filename: str, folder: str) -> str:
    """
    Upload image bytes to Vercel Blob (production) or local /static (dev).
    Returns the public URL of the uploaded image.
    """
    if BLOB_TOKEN:
        return await _upload_to_blob(content, f"{folder}/{filename}")
    else:
        return await _upload_to_local(content, filename, folder)


async def _upload_to_blob(content: bytes, pathname: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{BLOB_API}/{pathname}",
            content=content,
            headers={
                "Authorization": f"Bearer {BLOB_TOKEN}",
                "x-api-version": "7",
                "content-type": "application/octet-stream",
                "x-add-random-suffix": "1",
            },
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Blob upload failed: {resp.status_code} {resp.text[:200]}")
        return resp.json()["url"]


async def _upload_to_local(content: bytes, filename: str, folder: str) -> str:
    import aiofiles
    base = os.path.join(os.path.dirname(__file__), "..", "..", "static", "images", folder)
    os.makedirs(base, exist_ok=True)
    dest = os.path.join(base, filename)
    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)
    return f"/static/images/{folder}/{filename}"
