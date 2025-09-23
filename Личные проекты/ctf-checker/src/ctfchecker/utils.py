import re
import time
from typing import Optional

FLAG_MASK = re.compile(r'(CTF\{)([^}]*)\}')

def mask_flag(s: str) -> str:
    # Показываем только первые 4 символа полезной части
    def repl(m):
        prefix = m.group(1)
        body = m.group(2)
        if len(body) <= 4:
            return f"{prefix}{body}***}}"
        return f"{prefix}{body[:4]}***}}"
    return FLAG_MASK.sub(repl, s)

def now_ts() -> int:
    return int(time.time())
