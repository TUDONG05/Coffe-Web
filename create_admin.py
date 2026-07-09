"""
Quick script to create an admin user for testing.
"""
import os
from sqlalchemy.orm import Session
from highlands.database import SessionLocal, engine
from highlands import models
from highlands.auth_utils import hash_password

# Create all tables
models.Base.metadata.create_all(bind=engine)

# Create session
db = SessionLocal()

# Check if admin already exists
admin = db.query(models.User).filter(models.User.email == "admin@highlands.com").first()

if admin:
    # Update existing user to be admin
    admin.role = "admin"
    admin.is_active = 1
    db.commit()
    print("✓ Admin user updated")
else:
    # Create new admin user
    admin = models.User(
        name="Admin",
        email="admin@highlands.com",
        phone="0123456789",
        hashed_pwd=hash_password("admin123"),
        role="admin",
        is_active=1,
    )
    db.add(admin)
    db.commit()
    print("[OK] Admin user created")

print(f"Email: admin@highlands.com")
print(f"Password: admin123")
print(f"\nLogin at: http://localhost:8000/admin")

db.close()
