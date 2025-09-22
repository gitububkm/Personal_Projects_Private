# secur.py
# Windows-only. Build to secur.exe via PyInstaller.
# Asks for registry section name (expects number 3442), reads signature from
# HKCU\Software\ububkm (value "Signature"), loads public key (pubkey.pem) from
# the same folder as the opened sys.tat, verifies signature over the exact
# sys.tat content. Allows or denies viewing.

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
    print("\n=== SYSTEM INFORMATION (decoded) ===")
    try:
        obj = json.loads(decoded_json_str)
        for k, v in obj.items():
            print(f"{k}: {v}")
    except Exception:
        print(decoded_json_str)
    print("====================================\n")
    input("Press Enter to exit...")

def main():
    if len(sys.argv) < 2:
        print("Usage: secur.exe <path_to_sys.tat>")
        sys.exit(1)

    tat_path = sys.argv[1]
    if not os.path.isfile(tat_path):
        print("sys.tat not found.")
        sys.exit(1)

    # 1) Ask user for registry section name (expects 3442)
    section = prompt_section_number()
    if section != EXPECTED_SECTION_NUMBER:
        print("Incorrect registry section. Access denied.")
        sys.exit(1)

    # 2) Read signature from HKCU\Software\ububkm
    try:
        sig_b64 = read_registry_signature()
    except FileNotFoundError:
        print("Signature not found in registry. Access denied.")
        sys.exit(1)
    except Exception:
        print("Error reading signature. Access denied.")
        sys.exit(1)

    # 3) Load public key located next to sys.tat (pubkey.pem)
    pubkey_path = os.path.join(os.path.dirname(tat_path), "pubkey.pem")
    if not os.path.isfile(pubkey_path):
        print("Public key file (pubkey.pem) is missing. Access denied.")
        sys.exit(1)
    pub = load_public_key(pubkey_path)

    # 4) Read sys.tat and verify signature over its exact content
    with open(tat_path, "r", encoding="utf-8") as f:
        encoded = f.read()

    ok = verify_signature(pub, encoded.encode('utf-8'), sig_b64)
    if not ok:
        print("Signature verification failed. Access denied.")
        sys.exit(1)

    # 5) If ok, decode and show info
    try:
        decoded = base64.b64decode(encoded.encode('ascii')).decode('utf-8', errors='replace')
    except Exception:
        print("Could not decode system information. Access denied.")
        sys.exit(1)

    view_info(decoded)

if __name__ == "__main__":
    main()
