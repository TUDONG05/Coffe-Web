"""
Email service — gửi OTP xác thực qua Gmail SMTP (Google App Password).
"""
import smtplib
import random
import string
from datetime import timedelta
from highlands.models import vn_now
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from highlands.config import GMAIL_USER, GMAIL_APP_PASSWORD

# ── OTP store (in-memory): { "purpose:email": {otp, expires_at, attempts} } ──
_otp_store: dict[str, dict] = {}

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _otp_key(email: str, purpose: str) -> str:
    return f"{purpose}:{email}"


def create_otp(email: str, purpose: str = "register") -> str:
    otp = _generate_otp()
    _otp_store[_otp_key(email, purpose)] = {
        "otp": otp,
        "expires_at": vn_now() + timedelta(minutes=OTP_TTL_MINUTES),
        "attempts": 0,
    }
    return otp


def verify_otp(email: str, otp: str, purpose: str = "register") -> bool:
    key = _otp_key(email, purpose)
    record = _otp_store.get(key)
    if not record:
        return False
    if vn_now() > record["expires_at"]:
        _otp_store.pop(key, None)
        return False
    if record["attempts"] >= OTP_MAX_ATTEMPTS:
        _otp_store.pop(key, None)
        return False
    if record["otp"] != otp:
        record["attempts"] += 1
        return False
    _otp_store.pop(key, None)
    return True


def _send_email(to_email: str, subject: str, html: str) -> None:
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise RuntimeError("Chưa cấu hình GMAIL_USER / GMAIL_APP_PASSWORD trong .env")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Tu's Coffee <{GMAIL_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())


def send_otp_email(to_email: str, otp: str) -> None:
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;border:1px solid #e0e0e0">
      <div style="background:#111111;padding:28px 32px;text-align:center">
        <h1 style="color:#fff;font-size:1.4rem;margin:0;letter-spacing:-.01em">Tu's Coffee</h1>
        <p style="color:rgba(255,255,255,.6);font-size:.82rem;margin:6px 0 0">Xác thực tài khoản</p>
      </div>
      <div style="padding:32px">
        <p style="color:#333;font-size:.95rem;line-height:1.6;margin-top:0">
          Cảm ơn bạn đã đăng ký tài khoản tại <strong>Tu's Coffee</strong>!<br>
          Nhập mã OTP bên dưới để hoàn tất đăng ký:
        </p>
        <div style="background:#f5f5f5;border-radius:12px;padding:24px;text-align:center;margin:20px 0">
          <span style="font-size:2.4rem;font-weight:900;letter-spacing:.3em;color:#111111">{otp}</span>
        </div>
        <p style="color:#777;font-size:.82rem;line-height:1.6;margin-bottom:0">
          Mã có hiệu lực trong <strong>{OTP_TTL_MINUTES} phút</strong>.<br>
          Nếu bạn không yêu cầu, hãy bỏ qua email này.
        </p>
      </div>
    </div>
    """
    _send_email(to_email, "Mã xác thực đăng ký – Tu's Coffee", html)


def send_reset_otp_email(to_email: str, otp: str) -> None:
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;border:1px solid #e0e0e0">
      <div style="background:#C8102E;padding:28px 32px;text-align:center">
        <h1 style="color:#fff;font-size:1.4rem;margin:0;letter-spacing:-.01em">Tu's Coffee</h1>
        <p style="color:rgba(255,255,255,.75);font-size:.82rem;margin:6px 0 0">Đặt lại mật khẩu</p>
      </div>
      <div style="padding:32px">
        <p style="color:#333;font-size:.95rem;line-height:1.6;margin-top:0">
          Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản <strong>{to_email}</strong>.<br>
          Nhập mã OTP bên dưới để xác nhận:
        </p>
        <div style="background:#fff5f5;border:2px solid #C8102E;border-radius:12px;padding:24px;text-align:center;margin:20px 0">
          <span style="font-size:2.4rem;font-weight:900;letter-spacing:.3em;color:#C8102E">{otp}</span>
        </div>
        <p style="color:#777;font-size:.82rem;line-height:1.6;margin-bottom:0">
          Mã có hiệu lực trong <strong>{OTP_TTL_MINUTES} phút</strong>.<br>
          Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này.
        </p>
      </div>
    </div>
    """
    _send_email(to_email, "Đặt lại mật khẩu – Tu's Coffee", html)
