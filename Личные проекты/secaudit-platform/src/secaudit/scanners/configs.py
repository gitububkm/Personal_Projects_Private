from __future__ import annotations
import os, re, json, yaml
from typing import List
from ..models import Finding, Severity

def scan_env(path: str, root: str, findings: List[Finding]):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f, start=1):
                s = line.strip()
                if not s or s.startswith('#'): 
                    continue
                if re.search(r'(?i)^debug\s*=\s*true', s):
                    findings.append(Finding('config', Severity.MEDIUM, 'DEBUG=true in .env', os.path.relpath(path, root), i))
                if re.search(r'(?i)bind\s*=\s*0\.0\.0\.0', s):
                    findings.append(Finding('config', Severity.MEDIUM, 'Service binds to 0.0.0.0 in .env', os.path.relpath(path, root), i))
                if re.search(r'(?i)(password|secret|token)\s*=\s*.+', s):
                    findings.append(Finding('config', Severity.LOW, 'Secret-like var in .env', os.path.relpath(path, root), i))
    except Exception:
        pass

def scan_yaml(path: str, root: str, findings: List[Finding]):
    try:
        data = yaml.safe_load(open(path, 'r', encoding='utf-8', errors='ignore'))
        s = str(data)
        if '0.0.0.0' in s:
            findings.append(Finding('config', Severity.MEDIUM, 'Binding 0.0.0.0 in YAML', os.path.relpath(path, root)))
        if 'DEBUG' in s and ('true' in s.lower() or 'True' in s):
            findings.append(Finding('config', Severity.MEDIUM, 'DEBUG=true in YAML', os.path.relpath(path, root)))
    except Exception:
        pass

def scan_json(path: str, root: str, findings: List[Finding]):
    try:
        data = json.load(open(path, 'r', encoding='utf-8', errors='ignore'))
        s = json.dumps(data)
        if '0.0.0.0' in s:
            findings.append(Finding('config', Severity.MEDIUM, 'Binding 0.0.0.0 in JSON', os.path.relpath(path, root)))
    except Exception:
        pass

def scan(root: str) -> List[Finding]:
    findings: List[Finding] = []
    for base, _, files in os.walk(root):
        for name in files:
            path = os.path.join(base, name)
            low = name.lower()
            if low == '.env':
                scan_env(path, root, findings)
            elif low.endswith(('.yaml','.yml')):
                scan_yaml(path, root, findings)
            elif low.endswith('.json'):
                scan_json(path, root, findings)
    return findings
