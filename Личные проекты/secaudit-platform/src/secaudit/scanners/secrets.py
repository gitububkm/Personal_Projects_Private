from __future__ import annotations
import re, os
from typing import List
from ..models import Finding, Severity

SECRET_PATTERNS = [
    (Severity.CRITICAL, r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*([A-Z0-9/+=]{16,40})'),
    (Severity.HIGH, r'(?i)(api_?key|secret|token|passwd|password)\s*[:=]\s*([\w\-\+/=]{8,})'),
    (Severity.MEDIUM, r'(?i)bearer\s+[A-Za-z0-9\-\._~\+\/]+=*'),
    (Severity.LOW, r'(?i)private_key|BEGIN\s+PRIVATE\s+KEY'),
]

SKIP_DIRS = {'.git','node_modules','venv','.venv','dist','build','__pycache__'}

def scan(root: str) -> List[Finding]:
    findings: List[Finding] = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = os.path.join(base, name)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, start=1):
                        for sev, pattern in SECRET_PATTERNS:
                            m = re.search(pattern, line)
                            if m:
                                findings.append(Finding(
                                    scanner='secrets',
                                    severity=sev,
                                    message=f'Potential secret: {m.group(1) if m.lastindex else "match"}',
                                    file=os.path.relpath(path, root),
                                    line=i,
                                    meta={'excerpt': line.strip()[:200]}
                                ))
            except Exception:
                continue
    return findings
