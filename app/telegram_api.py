import requests
from .config import settings

class TelegramError(RuntimeError): pass

def tg(method, payload):
    if not settings.telegram_token:
        raise TelegramError("TELEGRAM_BOT_TOKEN is not configured")
    url=f"https://api.telegram.org/bot{settings.telegram_token}/{method}"
    r=requests.post(url, json=payload, timeout=20)
    if not r.ok:
        raise TelegramError(f"Telegram HTTP {r.status_code}: {r.text[:300]}")
    data=r.json()
    if not data.get("ok"):
        raise TelegramError(str(data))
    return data.get("result")

def send(chat_id, text, keyboard=None):
    payload={"chat_id":chat_id,"text":text,"disable_web_page_preview":True}
    if keyboard:
        payload["reply_markup"]={"inline_keyboard":keyboard}
    return tg("sendMessage",payload)
