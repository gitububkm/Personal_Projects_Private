import os
import sys
import hashlib
import base64
import getpass
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import win32security
import win32con


# Папка для защиты
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
PROTECT_FOLDER = os.path.join(DESKTOP, "1a")

# Файл конфигурации внутри папки
CONFIG_FILE = os.path.join(PROTECT_FOLDER, "template.tbl")


# --- Менеджер безопасности ---
class SecurityManager:
    def __init__(self):
        self.everyone_sid = win32security.CreateWellKnownSid(win32security.WinWorldSid)

    def set_read_only(self, path):
        if not os.path.exists(path):
            return False, f"Файл не найден: {path}"

        # Исключение для картинок 1.jpg и 2.jpg, чтобы они оставались доступными для чтения
        if path.endswith("1.jpg") or path.endswith("2.jpg"):
            return True, f"Доступ разрешён для: {os.path.basename(path)}"
        
        try:
            # Получаем текущие права доступа (DACL) файла
            sd = win32security.GetNamedSecurityInfo(
                path,
                win32security.SE_FILE_OBJECT,
                win32security.DACL_SECURITY_INFORMATION,
            )
            # Получаем DACL, если его нет, создаём новый
            dacl = sd.GetSecurityDescriptorDacl() or win32security.ACL()

            # Удаляем старые записи для 'Everyone' (если они есть)
            aces_to_remove = [
                i
                for i in range(dacl.GetAceCount())
                if dacl.GetAce(i)[2] == self.everyone_sid
                and dacl.GetAce(i)[0][0] == win32security.ACCESS_DENIED_ACE_TYPE
            ]
            for i in sorted(aces_to_remove, reverse=True):
                dacl.DeleteAce(i)

            # Добавляем новый доступ: запрещаем изменения, но разрешаем чтение
            dacl.AddAccessDeniedAceEx(
                win32security.ACL_REVISION,
                0,
                win32con.GENERIC_WRITE | win32con.DELETE,
                self.everyone_sid,
            )

            # Применяем изменённые права доступа (DACL)
            win32security.SetNamedSecurityInfo(
                path,
                win32security.SE_FILE_OBJECT,
                win32security.DACL_SECURITY_INFORMATION,
                None, None, dacl, None
            )

            return True, f"Доступ ограничен для: {os.path.basename(path)}"
        except Exception as e:
            return False, f"Ошибка: {e}"

    def remove_restrictions(self, path):
        if not os.path.exists(path):
            return False, f"Файл не найден: {path}"

        # Исключение для картинок 1.jpg и 2.jpg
        if path.endswith("1.jpg") or path.endswith("2.jpg"):
            return True, f"Доступ восстановлен для: {os.path.basename(path)}"
        
        try:
            # Получаем текущие права доступа (DACL) файла
            sd = win32security.GetNamedSecurityInfo(
                path,
                win32security.SE_FILE_OBJECT,
                win32security.DACL_SECURITY_INFORMATION,
            )
            # Получаем DACL, если его нет, создаём новый
            dacl = sd.GetSecurityDescriptorDacl() or win32security.ACL()

            # Удаляем старые записи для 'Everyone' (если они есть)
            aces_to_remove = [
                i
                for i in range(dacl.GetAceCount())
                if dacl.GetAce(i)[2] == self.everyone_sid
                and dacl.GetAce(i)[0][0] == win32security.ACCESS_DENIED_ACE_TYPE
            ]
            for i in sorted(aces_to_remove, reverse=True):
                dacl.DeleteAce(i)

            # Добавляем разрешение на доступ (разрешаем всем полный доступ)
            dacl.AddAccessAllowedAceEx(
                win32security.ACL_REVISION,
                0,
                win32con.GENERIC_ALL,
                self.everyone_sid,
            )

            # Применяем изменённые права доступа (DACL)
            win32security.SetNamedSecurityInfo(
                path,
                win32security.SE_FILE_OBJECT,
                win32security.DACL_SECURITY_INFORMATION,
                None, None, dacl, None
            )

            return True, f"Доступ восстановлен для: {os.path.basename(path)}"
        except Exception as e:
            return False, f"Ошибка: {e}"


# --- Менеджер конфигурации ---
class ConfigManager:
    def __init__(self, path):
        self.path = path
        self.salt = None
        self.password_hash = None

    def exists(self):
        return os.path.exists(self.path)

    def create(self, password):
        salt_bytes = os.urandom(16)
        self.salt = base64.b64encode(salt_bytes).decode("utf-8")
        self.password_hash = self._hash_password(password, self.salt)
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(f"{self.salt}:{self.password_hash}\n")
        except PermissionError:
            print(f"Нет прав на запись файла конфигурации: {self.path}")
            sys.exit(1)

    def verify_password(self, password):
        return self.password_hash == self._hash_password(password, self.salt)

    @staticmethod
    def _hash_password(password, salt):
        return hashlib.sha256(salt.encode() + password.encode()).hexdigest()


# --- Интерфейс GUI ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Файловый Протектор")
        self.root.geometry("400x300")
        
        self.config = ConfigManager(CONFIG_FILE)
        self.security_manager = SecurityManager()

        self.is_protected = False  # Статус защиты

        # Картинка для отображения
        self.img_label = tk.Label(self.root)
        self.img_label.pack(pady=20)

        # Кнопки для включения/выключения защиты
        self.protect_button = tk.Button(
            self.root, text="Включить защиту", command=self.enable_protection
        )
        self.protect_button.pack(pady=10)
        
        self.unprotect_button = tk.Button(
            self.root, text="Отключить защиту", command=self.disable_protection
        )
        self.unprotect_button.pack(pady=10)

    def show_image(self, image_path):
        img = Image.open(image_path)
        img = img.resize((250, 250))  # Подгоняем размер
        img = ImageTk.PhotoImage(img)
        self.img_label.config(image=img)
        self.img_label.image = img  # Чтобы изображение не удалялось

    def enable_protection(self):
        password = simpledialog.askstring(
            "Введите пароль", "Введите новый пароль для защиты:", show="*"
        )
        if password:
            self.config.create(password)
            self.apply_protection()
            self.show_image(os.path.join(PROTECT_FOLDER, "1.jpg"))
            self.is_protected = True
            messagebox.showinfo("Защита включена", "Защита файлов включена.")

    def disable_protection(self):
        password = simpledialog.askstring(
            "Введите пароль", "Введите пароль для отключения защиты:", show="*"
        )
        if password:
            if self.config.verify_password(password):
                self.remove_protection()
                self.show_image(os.path.join(PROTECT_FOLDER, "2.jpg"))
                self.is_protected = False
                messagebox.showinfo("Защита отключена", "Защита файлов отключена.")
            else:
                messagebox.showerror("Ошибка", "Неверный пароль.")

    def apply_protection(self):
        for root, dirs, files in os.walk(PROTECT_FOLDER):
            for name in files + dirs:
                path = os.path.join(root, name)
                success, msg = self.security_manager.set_read_only(path)
                print(msg)

    def remove_protection(self):
        for root, dirs, files in os.walk(PROTECT_FOLDER):
            for name in files + dirs:
                path = os.path.join(root, name)
                success, msg = self.security_manager.remove_restrictions(path)
                print(msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
