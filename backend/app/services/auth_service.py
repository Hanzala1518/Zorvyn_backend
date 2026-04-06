import logging
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from app.config import Settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, settings: Settings) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def authenticate_user(email: str, password: str, client) -> dict | None:
    """
    Fetch user by email and verify password.
    Returns user dict on success, None on any failure.
    Uses supabase-py v2: response.data is a list, never raises on 0 rows.
    """
    try:
        response = (
            client.table("users")
            .select("id, email, full_name, role, status, password_hash")
            .eq("email", email.lower().strip())
            .eq("is_deleted", False)
            .execute()
        )
        if not response.data:
            logger.warning(f"Login attempt for non-existent email: {email}")
            return None

        user = response.data[0]

        if user["status"] != "active":
            logger.warning(f"Login attempt for inactive user: {email}")
            return None

        if not verify_password(password, user["password_hash"]):
            logger.warning(f"Invalid password for user: {email}")
            return None

        return {k: v for k, v in user.items() if k != "password_hash"}

    except Exception as e:
        logger.error(f"authenticate_user error for {email}: {e}")
        return None


