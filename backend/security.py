import os
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

import models
from database import get_db

load_dotenv()

ENV = os.getenv("ENV", "development")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")

if not SECRET_KEY:
    if ENV == "production":
        raise RuntimeError("КРИТИЧЕСКАЯ ОШИБКА: Не задан JWT_SECRET_KEY в .env!")
    SECRET_KEY = "dev_only_fallback_secret_key_change_me"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

security_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> models.User | None:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (jwt.PyJWTError, ValueError, TypeError):
        return None

    return db.query(models.User).filter(models.User.id == user_id).first()


def get_current_user_required(
    user: models.User | None = Depends(get_current_user_optional)
) -> models.User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла или вы не авторизованы. Войдите в аккаунт заново."
        )
    return user


def get_current_admin_required(
    current_user: models.User = Depends(get_current_user_required)
) -> models.User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещён: требуются права администратора"
        )
    return current_user
