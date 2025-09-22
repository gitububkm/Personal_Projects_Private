# app.py
# Requires: Python 3.x (Windows)
# This file is copied to ProgramData\SimpleTrialApp by the installer.

import os
import json
import time
import winreg

APP_FOLDER = os.path.join(os.getenv('ProgramData'), 'SimpleTrialApp')
INFO_PATH = os.path.join(APP_FOLDER, 'info.json')
NAMES_PATH = os.path.join(APP_FOLDER, 'names.txt')
REG_KEY_PATH = r'Software\SimpleTrialApp'

# Trial limits
TIME_LIMIT_SECONDS = 60   # 1 minute
START_LIMIT = 2           # 2 launches

def ensure_folder():
    os.makedirs(APP_FOLDER, exist_ok=True)

def read_registry_install_path():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, 'InstallPath')
            return val
    except FileNotFoundError:
        return None

def write_registry_install_path(path):
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH) as key:
            winreg.SetValueEx(key, 'InstallPath', 0, winreg.REG_SZ, path)
    except Exception:
        pass

def load_info():
    if os.path.exists(INFO_PATH):
        try:
            with open(INFO_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'first_install_ts': None,
        'time_limit_seconds': TIME_LIMIT_SECONDS,
        'start_limit': START_LIMIT,
        'starts_used': 0,
        'removed_completely': False
    }

def save_info(info):
    with open(INFO_PATH, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2)

def human_seconds(s):
    if s <= 0:
        return '0s'
    m, sec = divmod(int(s), 60)
    if m:
        return f'{m}m {sec}s'
    return f'{sec}s'

def check_limits_and_increment(info):
    now_ts = time.time()
    if not info.get('first_install_ts'):
        info['first_install_ts'] = now_ts
    elapsed = now_ts - info['first_install_ts']
    time_left = info['time_limit_seconds'] - elapsed
    starts_left = info['start_limit'] - info['starts_used']
    if time_left <= 0 or starts_left <= 0:
        return False, time_left, starts_left
    info['starts_used'] += 1
    save_info(info)
    return True, time_left, starts_left - 1

def ask_name_and_store():
    name = input('Enter your full name (e.g., John Smith): ').strip()
    if not name:
        print('Empty input. Exiting.')
        return
    existing = set()
    if os.path.exists(NAMES_PATH):
        with open(NAMES_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                existing.add(line.strip())
    if name in existing:
        print('This name already exists in the file.')
    else:
        with open(NAMES_PATH, 'a', encoding='utf-8') as f:
            f.write(name + '\n')
        print('Name saved.')

def offer_after_limit():
    print('\n=== TRIAL LIMIT REACHED ===')
    print('You may purchase the full version or uninstall the program.')
    print('1) Purchase full version (demo)')
    print('2) Uninstall the program')
    print('0) Exit')
    choice = input('Choose: ').strip()
    if choice == '1':
        print('Thank you for your interest! (Demo only, no real purchase).')
    elif choice == '2':
        installed = read_registry_install_path()
        if installed:
            unp = os.path.join(installed, 'uninstaller.bat')
            if os.path.exists(unp):
                print('Launching uninstaller...')
                os.startfile(unp)
                return
        print('Could not launch uninstaller automatically. Please run uninstaller.bat manually.')
    else:
        print('Exit.')

def main():
    ensure_folder()
    write_registry_install_path(os.path.dirname(os.path.abspath(__file__)))
    info = load_info()
    if info.get('removed_completely'):
        print('Program was fully removed earlier. Trial unavailable.')
        return
    ok, time_left, starts_left = check_limits_and_increment(info)
    if not ok:
        offer_after_limit()
        return
    print(f'Time left: {human_seconds(time_left)}. Launches left: {starts_left}.')
    ask_name_and_store()
    print('\nProgram finished.')
    print('-- Trial restrictions: 1 minute from first install and 2 launches total.')
    print('When the limit is reached, you will be asked to buy the full version or uninstall.')
    print('Thank you!')

if __name__ == '__main__':
    main()
