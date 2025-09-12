from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    app_name: str = Field(default="Cycle API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    postgres_host: str = Field(default="192.168.100.6", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="cycle", env="POSTGRES_DB")
    postgres_user: str = Field(default="user", env="POSTGRES_USER")
    postgres_password: str = Field(default="password", env="POSTGRES_PASSWORD")
    
    # Redis
    redis_url: str = Field(env="REDIS_URL")
    redis_host: str = Field(default="192.168.100.6", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # JWT
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Email
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: str = Field(default="", env="SMTP_USER")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    email_from: str = Field(default="noreply@cycle.com", env="EMAIL_FROM")
    
    # Cloudinary Storage
    cloudinary_cloud_name: str = Field(default="", env="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(default="", env="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(default="", env="CLOUDINARY_API_SECRET")
    cloudinary_secure: bool = Field(default=True, env="CLOUDINARY_SECURE")
    
    # M-Pesa
    mpesa_consumer_key: str = Field(default="", env="MPESA_CONSUMER_KEY")
    mpesa_consumer_secret: str = Field(default="", env="MPESA_CONSUMER_SECRET")
    mpesa_passkey: str = Field(default="", env="MPESA_PASSKEY")
    mpesa_business_short_code: str = Field(default="", env="MPESA_BUSINESS_SHORT_CODE")
    mpesa_environment: str = Field(default="sandbox", env="MPESA_ENVIRONMENT")
    
    # Expo Push
    expo_access_token: str = Field(default="", env="EXPO_ACCESS_TOKEN")
    
    # Sentry
    sentry_dsn: str = Field(default="", env="SENTRY_DSN")
    
    # CORS
    cors_origins: List[str] = Field(default=["http://192.168.100.6:3000", "http://localhost:3000"], env="CORS_ORIGINS")
    
    # Security
    secret_key: str = Field(env="SECRET_KEY")
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
