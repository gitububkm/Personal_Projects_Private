from __future__ import annotations
import os, uuid
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ..models import Report
from ..cli import run_scan
from ..report import to_html, to_pdf

app = FastAPI(title='SecAudit Platform (MVP)')
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), '..', 'templates'))

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.post('/scan', response_class=HTMLResponse)
def scan(request: Request, target: str = Form(...)):
    report = run_scan(target)
    html = to_html(report)
    out_dir = '/tmp'
    rid = str(uuid.uuid4())[:8]
    html_path = os.path.join(out_dir, f'secaudit_{rid}.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return templates.TemplateResponse('result.html', {'request': request, 'html_path': html_path, 'target': target, 'count': len(report.findings)})

@app.get('/download')
def download(path: str):
    return FileResponse(path, filename=os.path.basename(path))
