from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import json


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:3000"
    # Set as JSON array OR comma-separated string on Render:
    #   ["https://your-app.vercel.app"]
    #   https://your-app.vercel.app,https://other.com
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    def get_allowed_origins(self) -> List[str]:
        v = self.ALLOWED_ORIGINS.strip()
        if v.startswith("["):
            return json.loads(v)
        return [o.strip() for o in v.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
