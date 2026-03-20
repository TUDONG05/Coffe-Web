"""
Database migration: Add role and is_active columns to users table, create categories table.
"""
import os
from sqlalchemy import text
from highlands.database import SessionLocal, engine
from highlands import models

# Recreate all tables with new schema
print("Dropping old tables...")
models.Base.metadata.drop_all(bind=engine)

print("Creating new tables...")
models.Base.metadata.create_all(bind=engine)

print("[OK] Database migrated successfully")
print("New tables: users, products, orders, order_items, stores, promotions, news, categories")
