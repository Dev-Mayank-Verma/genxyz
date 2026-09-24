import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    webhook_secret: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    registrar_base_url: str = os.getenv("REGISTRAR_BASE_URL", "")
    registrar_api_key: str = os.getenv("REGISTRAR_API_KEY", "")
    availability_path: str = os.getenv("REGISTRAR_AVAILABILITY_PATH", "/domains/availability")
    price_path: str = os.getenv("REGISTRAR_PRICE_PATH", "/domains/price")
    register_path: str = os.getenv("REGISTRAR_REGISTER_PATH", "/domains/register")
    status_path: str = os.getenv("REGISTRAR_STATUS_PATH", "/orders/{order_id}")
    coupon_code: str = os.getenv("REGISTRAR_COUPON_CODE", "")

settings = Settings()
