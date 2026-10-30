import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    admin_id: int
    proxy_url: Optional[str] = None


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    admin_id = os.getenv("ADMIN_ID")
    proxy_url = os.getenv("PROXY_URL")

    if not token:
        raise ValueError("BOT_TOKEN не задан в .env")
    if not admin_id:
        raise ValueError("ADMIN_ID не задан в .env")

    return Config(
        bot_token=token,
        admin_id=int(admin_id),
        proxy_url=proxy_url,
    )