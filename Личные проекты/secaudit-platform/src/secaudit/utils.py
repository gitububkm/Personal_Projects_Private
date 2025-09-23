import os, re, json, hashlib, time
from typing import Iterable

TEXT_EXT = {'.py','.txt','.md','.yaml','.yml','.json','.env','.ini','.cfg','.conf','.toml','.sh','.dockerfile','.gitignore'}

def is_text_file(path: str) -> bool:
    p = path.lower()
    _, ext = os.path.splitext(p)
    if ext in TEXT_EXT:
        return True
    # simple heuristic: small files with mostly printable chars
    try:
        with open(path, 'rb') as f:
            data = f.read(2048)
        if not data:
            return True
        printable = sum(32 <= b <= 126 or b in (9,10,13) for b in data)
        return printable / max(1,len(data)) > 0.9
    except:
        return False

def walk_files(root: str) -> Iterable[str]:
    for base, _, files in os.walk(root):
        for name in files:
            yield os.path.join(base, name)
