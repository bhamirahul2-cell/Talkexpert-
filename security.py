from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("TALKEXPERT_SECRET", "CHANGE_THIS_DEVELOPMENT_SECRET_BEFORE_DEPLOY")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def make_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id), "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
