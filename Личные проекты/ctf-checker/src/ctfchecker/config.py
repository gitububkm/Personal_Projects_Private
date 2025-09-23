from __future__ import annotations
import yaml
from typing import Any, Dict
from .models import Config, Challenge

def _get(d: Dict[str, Any], key: str, default=None):
    v = d.get(key, default)
    return v

def load_config(path: str) -> Config:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    g = data.get('global', {}) or {}
    submitter = data.get('submitter', {}) or {}
    telegram = data.get('telegram', {}) or {}

    cfg = Config(
        global_concurrency=int(_get(g, 'concurrency', 4)),
        global_timeout=int(_get(g, 'timeout_seconds', 30)),
        submit_enabled=bool(_get(g, 'submit', False)),
        submit_url=submitter.get('url'),
        submit_token=submitter.get('token'),
    )

    # telegram
    cfg.telegram_token = telegram.get('bot_token')
    cfg.telegram_chat_id = str(telegram.get('chat_id')) if telegram.get('chat_id') is not None else None
    notify_on = telegram.get('notify_on', [])
    if isinstance(notify_on, list):
        cfg.telegram_notify_on = [str(x).upper() for x in notify_on]
    elif isinstance(notify_on, str):
        cfg.telegram_notify_on = [notify_on.upper()]
    else:
        cfg.telegram_notify_on = []

    chs = data.get('challenges', []) or []
    for ch in chs:
        extra = {k: v for k, v in ch.items() if k not in {
            'id','name','type','flag_regex','timeout','submit_on_success',
            'command','host','port','send','expect_regex'
        }}
        cfg.challenges.append(Challenge(
            id=str(ch['id']),
            name=str(ch.get('name', ch['id'])),
            type=str(ch['type']),
            flag_regex=ch.get('flag_regex'),
            timeout=ch.get('timeout'),
            submit_on_success=bool(ch.get('submit_on_success', False)),
            command=ch.get('command'),
            host=ch.get('host'),
            port=ch.get('port'),
            send=ch.get('send'),
            expect_regex=ch.get('expect_regex'),
            extra=extra
        ))
    return cfg
