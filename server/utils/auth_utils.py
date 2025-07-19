import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

SECRET = "tu_secreto_super_seguro"


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user):
    payload = {
        "user_id": user["id"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=2),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")
