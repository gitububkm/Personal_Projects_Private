from __future__ import annotations
import time
import requests
from typing import Iterable, Optional

class TelegramNotifier:
    """Lightweight Telegram bot sender via Bot API.

    Usage:
        tn = TelegramNotifier(token="123:ABC", chat_id="123456789", notify_on=["OK","FAIL","ERROR"])
        tn.notify(status="OK", challenge_id="exploit-1", details="stdout matched: ...", duration_ms=123)
    """

    def __init__(self, token: Optional[str], chat_id: Optional[str], notify_on: Optional[Iterable[str]] = None, timeout: int = 10):
        self.token = token
        self.chat_id = chat_id
        self.notify_on = set([s.upper() for s in (notify_on or [])])
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id and self.notify_on)

    def _url(self) -> str:
        return f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send(self, text: str) -> dict:
        if not self.enabled:
            return {"ok": False, "error": "telegram not configured"}
        try:
            r = requests.post(self._url(), json={"chat_id": self.chat_id, "text": text}, timeout=self.timeout)
            if r.status_code == 200:
                return {"ok": True}
            return {"ok": False, "code": r.status_code, "text": r.text}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def notify(self, *, status: str, challenge_id: str, details: str, duration_ms: int):
        if not self.enabled:
            return
        status_u = (status or "").upper()
        if self.notify_on and status_u not in self.notify_on:
            return
        # Keep it simple: plain text (no Markdown), truncate long details
        d = details if len(details) < 500 else details[:500] + "…"
        msg = (f"CTF Checker\n"
               f"Status: {status_u}\n"
               f"Challenge: {challenge_id}\n"
               f"Duration: {duration_ms} ms\n"
               f"Details: {d}")
        self.send(msg)
