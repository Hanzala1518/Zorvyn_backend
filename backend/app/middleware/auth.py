from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

# Paths that skip token extraction (no bearer required)
EXCLUDED_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/auth/login",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Lightweight middleware that extracts JWT claims into request.state
    when a valid Bearer token is present. Actual enforcement is handled
    by FastAPI dependencies in each router.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        authorization: str = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                )
                request.state.user_id = payload.get("sub")
                request.state.user_email = payload.get("email")
                request.state.user_role = payload.get("role")
            except JWTError:
                # Invalid token — downstream dependency will reject if needed
                request.state.user_id = None
                request.state.user_email = None
                request.state.user_role = None
        else:
            request.state.user_id = None
            request.state.user_email = None
            request.state.user_role = None

        return await call_next(request)
