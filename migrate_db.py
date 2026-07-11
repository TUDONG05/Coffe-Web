"""
Database migration: safe ALTER TABLE for missing columns (no data loss).
"""
import os
from sqlalchemy import text, inspect
from highlands.database import SessionLocal, engine
from highlands import models

# Create any missing tables
print("Creating new tables if not exist...")
models.Base.metadata.create_all(bind=engine)

inspector = inspect(engine)

def add_column_if_missing(table, column, col_type):
    existing = [c["name"] for c in inspector.get_columns(table)]
    if column not in existing:
        print(f"Adding column: {table}.{column} ...")
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            conn.commit()
        print(f"[OK] Column '{column}' added to {table}")
    else:
        print(f"[OK] {table}.{column} already exists, skipping")

add_column_if_missing("users",  "address", "VARCHAR(300) NULL")
add_column_if_missing("orders", "address", "VARCHAR(300) NULL")
add_column_if_missing("users",  "points",  "INT NOT NULL DEFAULT 0")
add_column_if_missing("orders", "payment_method",  "VARCHAR(20) NOT NULL DEFAULT 'cash'")
add_column_if_missing("orders", "payment_status",  "VARCHAR(20) NOT NULL DEFAULT 'unpaid'")
add_column_if_missing("orders", "cancel_token",    "VARCHAR(32) NULL")
add_column_if_missing("users",  "google_id", "VARCHAR(255) NULL")
add_column_if_missing("products", "image_url", "VARCHAR(300) NULL")
add_column_if_missing("products", "video_url", "VARCHAR(500) NULL")
add_column_if_missing("news",     "video_url", "VARCHAR(500) NULL")
add_column_if_missing("news",     "view_count", "INT NOT NULL DEFAULT 0")
add_column_if_missing("news",     "unique_view_count", "INT NOT NULL DEFAULT 0")

# product_reviews table is created via Base.metadata.create_all above

# Make hashed_pwd nullable for Google-only users
print("Ensuring hashed_pwd is nullable...")
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE users MODIFY COLUMN hashed_pwd VARCHAR(255) NULL"))
    conn.commit()
print("[OK] hashed_pwd is now nullable")

# Add unique index on google_id if not already there
print("Ensuring unique index on users.google_id...")
with engine.connect() as conn:
    # row[2] = Key_name (index name), row[4] = Column_name
    index_rows = conn.execute(text("SHOW INDEX FROM users")).fetchall()
    indexed_columns = {row[4] for row in index_rows}  # check by column name
    if "google_id" not in indexed_columns:
        conn.execute(text("ALTER TABLE users ADD UNIQUE INDEX ix_users_google_id (google_id)"))
        conn.commit()
        print("[OK] Unique index on google_id created")
    else:
        print("[OK] Index on google_id already exists, skipping")

print("[OK] Migration complete")
