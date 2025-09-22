# server_gui.py
# GUI Flask receiver: shows "Waiting..." with animation, saves JSON to Desktop\data,
# and notifies the GUI when a file arrives.

import os
import json
import datetime
import threading
import queue
from flask import Flask, request, jsonify
import tkinter as tk
from tkinter import ttk, messagebox

# ====== CONFIG ======
API_KEY = "b7f9d2a3-4e6c-41f2-9a8e-5c3d7f0b2e1c"  # <-- set the same as client
PORT = 8443
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
DATA_ROOT = os.path.join(DESKTOP, "data")
# ====================

os.makedirs(DATA_ROOT, exist_ok=True)

# -- cross-thread queue from Flask -> GUI
event_q = queue.Queue()

app = Flask(__name__)

def safe_name(s: str) -> str:
    return "".join(c for c in (s or "") if c.isalnum() or c in ("-","_",".")) or "unknown"

@app.route("/collect", methods=["POST"])
def collect():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"status":"error","reason":"invalid_json"}), 400

    key = payload.get("api_key") or request.headers.get("X-Api-Key")
    if key != API_KEY:
        return jsonify({"status":"error","reason":"unauthorized"}), 401

    info = payload.get("info", {})
    client_ip = request.remote_addr or "unknown_ip"
    host = info.get("computer") or info.get("hostname") or "unknown_host"
    user = info.get("user") or info.get("username") or "unknown_user"
    client_id = safe_name(f"{client_ip}_{host}_{user}")

    folder = os.path.join(DATA_ROOT, client_id)
    os.makedirs(folder, exist_ok=True)

    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{ts}.json"
    path = os.path.join(folder, filename)

    record = {
        "received_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "client_ip": client_ip,
        "info": info
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    # notify GUI
    event_q.put({"type": "saved", "path": path})
    return jsonify({"status":"ok","stored": path})

def run_flask():
    # Run Flask server in this background thread
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

# ---------- GUI ----------
class ServerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Receiver — Waiting for client")
        self.geometry("520x220")
        self.resizable(False, False)

        self.lbl_title = ttk.Label(self, text="Waiting for system info...", font=("Segoe UI", 14))
        self.lbl_title.pack(pady=(18, 6))

        self.pb = ttk.Progressbar(self, orient="horizontal", length=440, mode="indeterminate")
        self.pb.pack(pady=8)
        self.pb.start(12)  # animation speed

        self.lbl_path = ttk.Label(self, text="Saving to: " + DATA_ROOT, wraplength=480, justify="center")
        self.lbl_path.pack(pady=(8, 6))

        self.status_var = tk.StringVar(value=f"Listening on port {PORT}...")
        self.lbl_status = ttk.Label(self, textvariable=self.status_var, foreground="#555")
        self.lbl_status.pack(pady=(4, 2))

        self.btn_close = ttk.Button(self, text="Close", command=self.on_close, state="disabled")
        self.btn_close.pack(pady=(12, 8))

        # poll for events from flask
        self.after(300, self.poll_events)

    def poll_events(self):
        try:
            while True:
                msg = event_q.get_nowait()
                if msg.get("type") == "saved":
                    saved_path = msg.get("path")
                    self.pb.stop()
                    self.status_var.set("Data received successfully.")
                    self.lbl_title.configure(text="✅ System info received")
                    self.lbl_path.configure(text=f"Saved to:\n{saved_path}")
                    self.btn_close.configure(state="normal")
        except queue.Empty:
            pass
        # keep polling
        self.after(300, self.poll_events)

    def on_close(self):
        self.destroy()

def main():
    # start Flask in background
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # start GUI
    try:
        # optional: set ttk theme
        try:
            from tkinter import ttk
            style = ttk.Style()
            if "vista" in style.theme_names():
                style.theme_use("vista")
        except Exception:
            pass

        gui = ServerGUI()
        gui.mainloop()
    except Exception as e:
        messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    main()
