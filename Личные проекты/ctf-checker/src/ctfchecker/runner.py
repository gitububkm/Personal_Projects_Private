import asyncio
import re
import socket
from typing import Optional, Tuple, Dict, Any
from .utils import mask_flag

async def run_static(flag_regex: str, sample_text: str) -> Tuple[bool, Optional[str], str]:
    m = re.search(flag_regex, sample_text or "", flags=re.I)
    if m:
        flag = m.group(0)
        return True, flag, f"matched: {mask_flag(flag)}"
    return False, None, "no match"

async def run_exploit(command: str, flag_regex: str, timeout: int) -> Tuple[bool, Optional[str], str]:
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return False, None, "timeout"
    out = stdout.decode(errors='ignore')
    err = stderr.decode(errors='ignore')
    m = re.search(flag_regex, out, flags=re.I)
    if m:
        flag = m.group(0)
        return True, flag, f"stdout matched: {mask_flag(flag)}"
    return False, None, f"flag not found; stderr: {err[:200]}"

async def run_dynamic_basic(host: str, port: int, send: Optional[str], expect_regex: Optional[str], timeout: int) -> Tuple[bool, Optional[str], str]:
    # Очень упрощенный TCP-клиент
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
    except Exception as e:
        return False, None, f"connect error: {e}"
    try:
        if send:
            writer.write(send.encode() + b"\n")
            await writer.drain()
        data = await asyncio.wait_for(reader.read(4096), timeout=timeout)
        text = data.decode(errors='ignore')
        if expect_regex:
            m = re.search(expect_regex, text, flags=re.I)
            if m:
                return True, None, f"expect matched: {m.group(0)}"
            return False, None, f"expect not matched; got: {text[:200]}"
        return True, None, f"received: {text[:200]}"
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
