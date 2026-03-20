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

print("[OK] Migration complete")
