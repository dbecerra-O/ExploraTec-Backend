import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Parse database URL
    @property
    def database_config(self):
        url = urlparse(self.DATABASE_URL)
        return {
            "host": url.hostname,
            "port": url.port or 5432,
            "user": url.username,
            "password": url.password,
            "database": url.path[1:],
        }

settings = Settings()