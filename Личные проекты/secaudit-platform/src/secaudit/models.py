from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class Finding:
    scanner: str
    severity: Severity
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None

@dataclass
class Report:
    target: str
    findings: List[Finding]
