import argparse
import asyncio
import time
from typing import List
from .config import load_config
from .scheduler import Scheduler
from .storage import Storage
from .submitter import Submitter

def cmd_list(cfg_path: str):
    cfg = load_config(cfg_path)
    print("Challenges:")
    for ch in cfg.challenges:
        print(f"- {ch.id:12} | {ch.type:12} | {ch.name}")

def cmd_run_all(cfg_path: str, only_ids: List[str] | None = None):
    cfg = load_config(cfg_path)
    storage = Storage()
    submitter = Submitter(cfg.submit_url, cfg.submit_token)
    sched = Scheduler(cfg, storage, submitter)
    asyncio.run(sched.run_all(only_ids=only_ids))

def cmd_history(limit: int):
    storage = Storage()
    rows = storage.history(limit=limit)
    print(f"Last {limit} results:")
    for (rid, ts, cid, status, dur, details) in rows:
        t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        print(f"[{rid}] {t} | {cid:12} | {status:5} | {dur:5} ms | {details[:120]}")

def main():
    p = argparse.ArgumentParser(prog="ctfchecker", description="CTF Checker CLI")
    p.add_argument("--config", default="examples/config.yaml", help="Path to YAML config")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List challenges")
    p_run = sub.add_parser("run", help="Run selected challenge IDs")
    p_run.add_argument("ids", nargs="+", help="Challenge IDs to run")
    sub.add_parser("run-all", help="Run all challenges")
    p_hist = sub.add_parser("history", help="Show last N results")
    p_hist.add_argument("--limit", type=int, default=20)

    args = p.parse_args()

    if args.cmd == "list":
        cmd_list(args.config)
    elif args.cmd == "run":
        cmd_run_all(args.config, only_ids=args.ids)
    elif args.cmd == "run-all":
        cmd_run_all(args.config, only_ids=None)
    elif args.cmd == "history":
        cmd_history(args.limit)

if __name__ == "__main__":
    main()
