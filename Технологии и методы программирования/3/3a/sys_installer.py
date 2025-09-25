# sys_installer.py (исправлённая версия)
# Windows-only. Build to sys_doc.exe via PyInstaller (see instructions below).
# Автоматически создаёт папку "data" на рабочем столе и кладёт туда sys.tat, pubkey.pem и secur (exe или py).
# Ассоциирует .tat с защитным модулем так, чтобы двойной клик открывал файл.

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
SECUR_PY_NAME = "secur.py"
PUBKEY_NAME = "pubkey.pem"
SYS_TAT_NAME = "sys.tat"

# -------- helper functions --------
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
        "cpu": cpu_name.strip() if isinstance(cpu_name, str) else cpu_name,
        "total_memory_bytes": parse_first_number(total_mem),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    return info

def run_and_capture(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False, text=True)
        # take last non-empty line
        lines = [l for l in out.splitlines() if l.strip()]
        return lines[-1] if lines else ""
    except Exception:
        return ""

def parse_first_number(s):
    # extract first integer-ish number from a string
    if not s:
        return 0
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
    # RSA 2048 for demo
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

def associate_tat_with_command(command: str):
    """
    Создаёт per-user ассоциацию .tat -> command
    command должен быть строкой, содержащей "%1" где подставляется путь к файлу.
    """
    base = r"Software\Classes"
    # .tat -> TatFile.Secure
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"{base}\{ASSOC_DOT}") as k:
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, ASSOC_PROG_ID)
    # ProgID description
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"{base}\{ASSOC_PROG_ID}") as k:
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, ASSOC_DESC)
    # Open command
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"{base}\{ASSOC_PROG_ID}\shell\open\command") as k:
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, command)

# -------- secur.py template (запишем его в целевую папку при отсутствии secur.exe) --------
SECUR_PY_TEMPLATE = r'''# secur.py (generated)
import base64
import json
import os
import sys
import winreg

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

APP_VENDOR = "ububkm"
REG_APP_KEY = fr"Software\{APP_VENDOR}"
REG_SIGNATURE_VALUE = "Signature"
EXPECTED_SECTION_NUMBER = "3442"

def read_registry_signature():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_APP_KEY, 0, winreg.KEY_READ) as k:
        val, _ = winreg.QueryValueEx(k, REG_SIGNATURE_VALUE)
        return val

def load_public_key(pubkey_path: str):
    with open(pubkey_path, "rb") as f:
        return serialization.load_pem_public_key(f.read())

def verify_signature(pub, data_bytes: bytes, sig_b64: str) -> bool:
    sig = base64.b64decode(sig_b64.encode('ascii'))
    try:
        pub.verify(sig, data_bytes, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False

def prompt_section_number():
    print("Enter registry section number with the digital signature (hint: a number):")
    entered = input("> ").strip()
    return entered

def view_info(decoded_json_str: str):
    print("\\n=== SYSTEM INFORMATION (decoded) ===")
    try:
        obj = json.loads(decoded_json_str)
        for k, v in obj.items():
            print(f"{k}: {v}")
    except Exception:
        print(decoded_json_str)
    print("====================================\\n")
    input("Press Enter to exit...")

def main():
    if len(sys.argv) < 2:
        print("Usage: secur.py <path_to_sys.tat>")
        sys.exit(1)

    tat_path = sys.argv[1]
    if not os.path.isfile(tat_path):
        print("sys.tat not found.")
        sys.exit(1)

    section = prompt_section_number()
    if section != EXPECTED_SECTION_NUMBER:
        print("Incorrect registry section. Access denied.")
        sys.exit(1)

    try:
        sig_b64 = read_registry_signature()
    except Exception:
        print("Signature not found or cannot be read. Access denied.")
        sys.exit(1)

    pubkey_path = os.path.join(os.path.dirname(tat_path), "pubkey.pem")
    if not os.path.isfile(pubkey_path):
        print("Public key file (pubkey.pem) is missing. Access denied.")
        sys.exit(1)
    pub = load_public_key(pubkey_path)

    with open(tat_path, "r", encoding="utf-8") as f:
        encoded = f.read()

    ok = verify_signature(pub, encoded.encode('utf-8'), sig_b64)
    if not ok:
        print("Signature verification failed. Access denied.")
        sys.exit(1)

    try:
        decoded = base64.b64decode(encoded.encode('ascii')).decode('utf-8', errors='replace')
    except Exception:
        print("Could not decode system information. Access denied.")
        sys.exit(1)

    view_info(decoded)

if __name__ == "__main__":
    main()
'''

# -------- main GUI / flow (faux progress) --------
import tkinter as tk
from tkinter import ttk, messagebox

def faux_paint_update_window():
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
        time.sleep(0.25)

    def run_install():
        try:
            step("Preparing installer...", 10)

            # Автоматически создаём папку "data" на рабочем столе
            desk = os.path.join(os.path.expanduser("~"), "Desktop")
            target_folder = os.path.join(desk, "data")
            os.makedirs(target_folder, exist_ok=True)

            step("Collecting system information...", 15)
            info = collect_system_info()
            encoded = b64(json.dumps(info, ensure_ascii=False).encode('utf-8'))

            sys_tat_path = os.path.join(target_folder, SYS_TAT_NAME)
            step("Writing sys.tat...", 10)
            with open(sys_tat_path, "w", encoding="utf-8") as f:
                f.write(encoded)

            step("Generating cryptographic keys...", 10)
            priv, pub = generate_keypair()
            pub_pem = export_public_pem(pub)

            step("Signing system information...", 10)
            signature = sign_bytes(priv, encoded.encode('utf-8'))
            sig_b64 = b64(signature)
            write_registry_signature(sig_b64)

            # Drop/copy secur.exe if present, otherwise write secur.py
            step("Installing protection module...", 15)
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            secur_src_guess = os.path.join(exe_dir, SECUR_EXE_NAME)
            secur_dst_exe = os.path.join(target_folder, SECUR_EXE_NAME)
            secur_dst_py = os.path.join(target_folder, SECUR_PY_NAME)

            if os.path.isfile(secur_src_guess):
                try:
                    shutil.copy2(secur_src_guess, secur_dst_exe)
                    secur_target_command = f'"{secur_dst_exe}" "%1"'
                except Exception:
                    # fallback: write secur.py
                    with open(secur_dst_py, "w", encoding="utf-8") as sp:
                        sp.write(SECUR_PY_TEMPLATE)
                    secur_target_command = f'"{sys.executable}" "{secur_dst_py}" "%1"'
            else:
                # Dev mode: write secur.py so double-click works without a built secur.exe
                with open(secur_dst_py, "w", encoding="utf-8") as sp:
                    sp.write(SECUR_PY_TEMPLATE)
                secur_target_command = f'"{sys.executable}" "{secur_dst_py}" "%1"'

            # write public key
            pubkey_path = os.path.join(target_folder, PUBKEY_NAME)
            with open(pubkey_path, "wb") as fpk:
                fpk.write(pub_pem)

            step("Registering file association (.tat -> secur)...", 10)
            # Use per-user association with the command we prepared (must contain %1)
            associate_tat_with_command(secur_target_command)

            # Launch secur for the new sys.tat once
            step("Finalizing...", 5)
            try:
                # Launch via same mechanism we associated (use subprocess to run the command)
                # If we associated to python secur.py, call python
                if secur_target_command.lower().startswith(f'"{secur_dst_exe.lower()}"'):
                    # secur exe present
                    subprocess.Popen([secur_dst_exe, sys_tat_path], close_fds=True)
                else:
                    # call python with secur.py
                    subprocess.Popen([sys.executable, secur_dst_py, sys_tat_path], close_fds=True)
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
    faux_paint_update_window()

if __name__ == "__main__":
    main()
