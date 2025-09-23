from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class Challenge:
    id: str
    name: str
    type: str
    flag_regex: Optional[str] = None
    timeout: Optional[int] = None
    submit_on_success: bool = False
    # exploit
    command: Optional[str] = None
    # dynamic-basic
    host: Optional[str] = None
    port: Optional[int] = None
    send: Optional[str] = None
    expect_regex: Optional[str] = None
    # free-form
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Config:
    global_concurrency: int = 4
    global_timeout: int = 30
    submit_enabled: bool = False
    submit_url: Optional[str] = None
    submit_token: Optional[str] = None
    challenges: List[Challenge] = field(default_factory=list)
    # telegram
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_notify_on: List[str] = field(default_factory=list)
