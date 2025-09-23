from typing import Optional
import requests

class Submitter:
    def __init__(self, url: Optional[str], token: Optional[str] = None):
        self.url = url
        self.token = token

    def submit(self, flag: str) -> dict:
        if not self.url:
            return {"ok": False, "error": "submit_url not set"}
        headers = {}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        try:
            r = requests.post(self.url, json={"flag": flag}, headers=headers, timeout=10)
            if r.status_code == 200:
                return {"ok": True, "response": r.json() if r.headers.get('Content-Type','').startswith('application/json') else r.text}
            return {"ok": False, "code": r.status_code, "text": r.text}
        except Exception as e:
            return {"ok": False, "error": str(e)}
