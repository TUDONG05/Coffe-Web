"""
Auth endpoints: POST /api/auth/register, POST /api/auth/login, GET /api/auth/me
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import hash_password, verify_password, create_access_token, require_login
from highlands.config import GOOGLE_CLIENT_ID
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""
    address: str | None = None
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str

class GoogleTokenIn(BaseModel):
    credential: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    address: str | None = None
    role: str = "user"
    points: int = 0
    is_google_user: bool = False

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, obj, **kwargs):
        instance = super().model_validate(obj, **kwargs)
        instance.is_google_user = bool(getattr(obj, "google_id", None))
        return instance


# ── Routes ────────────────────────────────────────────────

@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")
    user = models.User(
        name=body.name,
        email=body.email,
        phone=body.phone,
        address=body.address,
        hashed_pwd=hash_password(body.password),
        points=50,  # welcome bonus
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": UserOut.model_validate(user)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not user.hashed_pwd or not verify_password(body.password, user.hashed_pwd):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": UserOut.model_validate(user)}


@router.post("/google/verify")
def google_verify(body: GoogleTokenIn, db: Session = Depends(get_db)):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth chưa được cấu hình")
    try:
        idinfo = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Google token không hợp lệ: {e}")

    google_id = idinfo["sub"]
    email     = idinfo.get("email", "")
    name      = idinfo.get("name", "") or email.split("@")[0]

    if not email:
        raise HTTPException(status_code=400, detail="Tài khoản Google không có email")

    user = (
        db.query(models.User).filter(models.User.google_id == google_id).first()
        or db.query(models.User).filter(models.User.email == email).first()
    )

    if user:
        if not user.google_id:
            user.google_id = google_id
            db.commit()
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa")
    else:
        user = models.User(
            name=name,
            email=email,
            google_id=google_id,
            hashed_pwd=None,
            points=50,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": UserOut.model_validate(user)}


@router.get("/me", response_model=UserOut)
def me(current_user: models.User = Depends(require_login)):
    return current_user


@router.put("/profile", response_model=UserOut)
def update_profile(
    body: ProfileUpdate,
    current_user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    if body.name is not None:
        current_user.name = body.name
    if body.phone is not None:
        current_user.phone = body.phone
    if body.address is not None:
        current_user.address = body.address
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/change-password")
def change_password(
    body: ChangePasswordIn,
    current_user: models.User = Depends(require_login),
    db: Session = Depends(get_db),
):
    if not verify_password(body.old_password, current_user.hashed_pwd):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải tối thiểu 6 ký tự")
    current_user.hashed_pwd = hash_password(body.new_password)
    db.commit()
    return {"success": True, "message": "Đổi mật khẩu thành công"}
