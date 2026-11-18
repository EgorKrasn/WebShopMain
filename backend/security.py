import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

import models
from database import get_db

# Секретный ключ для подписи токенов (при выкладке на сервер задаётся через переменную окружения)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sandrintime_super_secret_key_2026_change_in_prod")
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
