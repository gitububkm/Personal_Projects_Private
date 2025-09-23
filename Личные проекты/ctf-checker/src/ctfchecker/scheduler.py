import asyncio
import time
from typing import List, Tuple
from .models import Config, Challenge
from .runner import run_static, run_exploit, run_dynamic_basic
from .storage import Storage
from .submitter import Submitter
from .utils import mask_flag
from .notifier import TelegramNotifier

class Scheduler:
    def __init__(self, cfg: Config, storage: Storage, submitter: Submitter):
        self.cfg = cfg
        self.storage = storage
        self.submitter = submitter
        self.sem = asyncio.Semaphore(cfg.global_concurrency)
        self.notifier = TelegramNotifier(
            token=cfg.telegram_token,
            chat_id=cfg.telegram_chat_id,
            notify_on=cfg.telegram_notify_on
        )

    async def run_challenge(self, ch: Challenge):
        t0 = time.perf_counter()
        status = "ERROR"
        details = ""
        try:
            if ch.type == "static":
                ok, flag, info = await run_static(
                    ch.flag_regex or r"CTF\{[A-Za-z0-9_\-]{8,64}\}",
                    ch.extra.get("sample_text", "CTF{DEMO_FLAG_1234}")
                )
                if ok and flag and ch.submit_on_success:
                    sr = self.submitter.submit(flag)
                    info += f"; submit: {sr}"
                status = "OK" if ok else "FAIL"
                details = info

            elif ch.type == "exploit":
                ok, flag, info = await run_exploit(
                    ch.command or "",
                    ch.flag_regex or r"CTF\{[A-Za-z0-9_\-]{8,64}\}",
                    timeout=ch.timeout or self.cfg.global_timeout
                )
                if ok and flag and ch.submit_on_success:
                    sr = self.submitter.submit(flag)
                    info += f"; submit: {sr}"
                status = "OK" if ok else "FAIL"
                details = info

            elif ch.type == "dynamic-basic":
                ok, flag, info = await run_dynamic_basic(
                    host=ch.host or "127.0.0.1",
                    port=int(ch.port or 31337),
                    send=ch.send,
                    expect_regex=ch.expect_regex,
                    timeout=ch.timeout or self.cfg.global_timeout
                )
                status = "OK" if ok else "FAIL"
                details = info

            else:
                status = "ERROR"
                details = f"unknown type: {ch.type}"

        except Exception as e:
            status = "ERROR"
            details = f"exception: {e}"

        finally:
            dt_ms = int((time.perf_counter() - t0) * 1000)
            self.storage.add(ch.id, status, dt_ms, details)
            # Telegram notify (non-blocking fire-and-forget would be nicer, but keep it simple)
            try:
                self.notifier.notify(status=status, challenge_id=ch.id, details=details, duration_ms=dt_ms)
            except Exception:
                pass

    async def run_all(self, only_ids: List[str] | None = None):
        tasks = []
        for ch in self.cfg.challenges:
            if only_ids and ch.id not in only_ids:
                continue
            tasks.append(self._guarded_run(ch))
        await asyncio.gather(*tasks)

    async def _guarded_run(self, ch: Challenge):
        async with self.sem:
            await self.run_challenge(ch)
