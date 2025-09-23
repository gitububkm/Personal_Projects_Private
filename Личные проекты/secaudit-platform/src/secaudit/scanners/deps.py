from __future__ import annotations
import os, re, json
from typing import List
from ..models import Finding, Severity

# Очень маленькая демо-база: (pkg, version) -> описание
DEMO_CVES = {
    ('requests','2.19.0'): 'CVE-2018-18074: open redirect in requests',
    ('flask','0.12'): 'CVE-2018-XXXX: known issues in Flask 0.12 (demo)',
}

def parse_requirements(path: str):
    pkgs = []
    if not os.path.exists(path):
        return pkgs
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            m = re.match(r'([A-Za-z0-9_\-]+)\s*(==|>=|<=|~=)?\s*([A-Za-z0-9\.\-]+)?', s)
            if m:
                name, op, ver = m.group(1).lower(), m.group(2), m.group(3)
                pkgs.append((name, op or None, ver or None))
    return pkgs

def scan(root: str) -> List[Finding]:
    findings: List[Finding] = []
    req = os.path.join(root, 'requirements.txt')
    pkgs = parse_requirements(req)
    for (name, op, ver) in pkgs:
        if op is None or ver is None:
            findings.append(Finding(
                scanner='deps',
                severity=Severity.MEDIUM,
                message=f'Dependency not pinned: {name} (use ==version)',
                file='requirements.txt',
                line=None,
                meta={'package': name}
            ))
        desc = DEMO_CVES.get((name, ver))
        if desc:
            findings.append(Finding(
                scanner='deps',
                severity=Severity.HIGH,
                message=f'Known vulnerability for {name}=={ver}: {desc}',
                file='requirements.txt',
                line=None,
                meta={'package': name, 'version': ver, 'cve': desc}
            ))
    return findings
