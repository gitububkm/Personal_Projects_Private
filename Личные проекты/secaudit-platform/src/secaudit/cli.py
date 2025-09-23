from __future__ import annotations
import argparse, json, os, sys
from typing import List
from .models import Report, Finding, Severity
from .scanners import secrets, deps, configs
from .report import to_html, to_pdf

def run_scan(target: str):
    target = os.path.abspath(target)
    findings: List[Finding] = []
    findings += secrets.scan(target)
    findings += deps.scan(target)
    findings += configs.scan(target)
    return Report(target=target, findings=findings)

def cmd_scan(args):
    report = run_scan(args.path)
    if args.html:
        html = to_html(report)
        with open(args.html, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"[+] HTML report saved to {args.html}")
    if args.pdf:
        to_pdf(report, args.pdf)
        print(f"[+] PDF report saved to {args.pdf}")
    if not (args.html or args.pdf):
        print(json.dumps([f.__dict__ for f in report.findings], indent=2, default=str))

def cmd_summary(args):
    report = run_scan(args.path)
    sev_order = ['CRITICAL','HIGH','MEDIUM','LOW','INFO']
    counts = {k:0 for k in sev_order}
    for f in report.findings:
        counts[str(f.severity)] += 1
    print(f"Target: {report.target}")
    for k in sev_order:
        print(f"{k:8} : {counts[k]} findings")
    print(f"TOTAL    : {len(report.findings)}")


def main():
    p = argparse.ArgumentParser(prog='secaudit', description='SecAudit Platform (MVP)')
    sub = p.add_subparsers(dest='cmd', required=True)

    s1 = sub.add_parser('scan', help='Scan target directory and produce report')
    s1.add_argument('path')
    s1.add_argument('--html', help='Save HTML report to file')
    s1.add_argument('--pdf', help='Save PDF report to file')
    s1.set_defaults(func=cmd_scan)

    s2 = sub.add_parser('summary', help='Quick summary of findings')
    s2.add_argument('path')
    s2.set_defaults(func=cmd_summary)

    args = p.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
