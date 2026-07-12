"""
App configuration — reads from .env or environment variables.
"""
import os
from urllib.parse import quote_plus
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── PostgreSQL ───────────────────────────────────────────
PG_HOST     = os.getenv("PG_HOST",     "localhost")
PG_PORT     = os.getenv("PG_PORT",     "5432")
PG_USER     = os.getenv("PG_USER",     "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")
PG_DB       = os.getenv("PG_DB",       "highlands_coffee")

# Vercel Postgres sets POSTGRES_URL; fallback to manual PG_* vars
_raw_url = (
    os.getenv("POSTGRES_URL")
    or os.getenv("DATABASE_URL")
    or f"postgresql+psycopg2://{PG_USER}:{quote_plus(PG_PASSWORD)}@{PG_HOST}:{PG_PORT}/{PG_DB}"
)
# psycopg2 requires postgresql:// not postgres://
DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)

# ── JWT ──────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set. Add it to your .env file.")
ALGORITHM       = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# ── Google OAuth ─────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# ── Gmail SMTP (Google App Password) ─────────────────────
GMAIL_USER         = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
