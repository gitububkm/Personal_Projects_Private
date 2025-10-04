#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой userbot для автоматических ответов в личных сообщениях от указанного аккаунта.
Работает через Telethon. Настройки — в .env файле.
Автор: вы (подставьте свои данные в .env)
"""

import os
import re
import asyncio
from datetime import datetime, time
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser
from telethon.errors import FloodWaitError

load_dotenv()

# --- Обязательные параметры (заполните в .env) ---
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
ME_ID = os.getenv("ME_ID", "").strip()        # ваш числовой Telegram ID (рекомендуется)
GIRL_ID = os.getenv("GIRL_ID", "").strip()    # её числовой Telegram ID (рекомендуется)
# --- Дополнительные настройки (можно менять в .env) ---
MODE = os.getenv("MODE", "auto").lower()      # "auto" | "draft"
QUIET_HOURS = os.getenv("QUIET_HOURS", "23-08")
MIN_REPLY_GAP_SEC = int(os.getenv("MIN_REPLY_GAP_SEC", "1800"))
APPEND_AUTO_TAG = os.getenv("APPEND_AUTO_TAG", "true").lower() == "true"

OPENING_TEXT = os.getenv("OPENING_TEXT", "Сейчас не у экрана, отвечу позже ❤️")
BUSY_TEXT = os.getenv("BUSY_TEXT", "Сейчас занят(а), напишу как освобожусь.")
MEET_TEXT = os.getenv("MEET_TEXT", "Давай сегодня после 19:00? Могу подстроиться.")
CARE_TEXT = os.getenv("CARE_TEXT", "Обнимаю, думаю о тебе 🫶")
DEFAULT_TEXT = os.getenv("DEFAULT_TEXT", "Принял(а) сообщение, скоро отвечу.")

SESSION_NAME = os.getenv("SESSION_NAME", "girl_responder_session")

# ------------- Вспомогательные функции -------------
def parse_quiet_hours(s: str):
    m = re.match(r"^\s*(\d{1,2})\s*-\s*(\d{1,2})\s*$", s)
    if not m:
        return time(23, 0), time(8, 0)
    a, b = int(m.group(1)), int(m.group(2))
    return time(a % 24, 0), time(b % 24, 0)

Q_START, Q_END = parse_quiet_hours(QUIET_HOURS)

def in_quiet_hours(now: datetime) -> bool:
    t = now.time()
    if Q_START <= Q_END:
        return Q_START <= t < Q_END
    return t >= Q_START or t < Q_END

def suggest_replies(text: str):
    t = (text or "").lower()
    suggestions = []
    if any(w in t for w in ["как ты", "как дела", "как ты?"]):
        suggestions.append(OPENING_TEXT)
    if any(w in t for w in ["когда", "встретимся", "во сколько"]):
        suggestions.append(MEET_TEXT)
    if any(w in t for w in ["скуч", "люблю", "miss", "любл"]):
        suggestions.append(CARE_TEXT)
    if any(w in t for w in ["занят", "busy", "работ"]):
        suggestions.append(BUSY_TEXT)
    if not suggestions:
        suggestions.append(DEFAULT_TEXT)
    return suggestions[:3]

def add_auto_tag(text: str) -> str:
    return f"{text} {'[автоответ]' if APPEND_AUTO_TAG else ''}".strip()

last_reply_at = {}

# ----------------- Telethon client -----------------
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def resolve_target():
    # возвращаем объект-цель (пользователь) по GIRL_ID
    if GIRL_ID and GIRL_ID.isdigit():
        return PeerUser(int(GIRL_ID))
    if GIRL_ID and GIRL_ID.startswith("@"):
        ent = await client.get_entity(GIRL_ID)
        return ent
    # если GIRL_ID не указан, разрешаем реагировать на любого — будьте осторожны
    return None

HELP_TEXT = (
    "Команды (пишите себе в 'Избранное'):\n"
    "/mode auto|draft  — переключить режим\n"
    "/quiet HH-HH      — задать тихие часы, пример: /quiet 22-08\n"
    "/gap <сек>        — интервал анти-спама, пример: /gap 900\n"
    "/tag on|off       — включить/выключить пометку [автоответ]\n"
    "/ping             — проверить работу\n"
)

@client.on(events.NewMessage(from_users="me"))
async def self_cmd_handler(event: events.NewMessage.Event):
    text = (event.raw_text or "").strip()
    if text.lower() in ("/help", "help"):
        await event.reply(HELP_TEXT); return

    if text.startswith("/mode"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].lower() in ("auto", "draft"):
            global MODE
            MODE = parts[1].lower()
            await event.reply(f"Режим: {MODE}")
        else:
            await event.reply("Использование: /mode auto|draft")
        return

    if text.startswith("/quiet"):
        parts = text.split()
        if len(parts) == 2:
            global Q_START, Q_END
            Q_START, Q_END = parse_quiet_hours(parts[1])
            await event.reply(f"Тихие часы: {Q_START.strftime('%H:%M')}-{Q_END.strftime('%H:%M')}")
        else:
            await event.reply("Использование: /quiet HH-HH")
        return

    if text.startswith("/gap"):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            global MIN_REPLY_GAP_SEC
            MIN_REPLY_GAP_SEC = int(parts[1])
            await event.reply(f"MIN_REPLY_GAP_SEC={MIN_REPLY_GAP_SEC}")
        else:
            await event.reply("Использование: /gap <секунд>")
        return

    if text.startswith("/tag"):
        parts = text.split()
        if len(parts) == 2 and parts[1].lower() in ("on", "off"):
            global APPEND_AUTO_TAG
            APPEND_AUTO_TAG = parts[1].lower() == "on"
            await event.reply(f"APPEND_AUTO_TAG={APPEND_AUTO_TAG}")
        else:
            await event.reply("Использование: /tag on|off")
        return

    if text.strip() == "/ping":
        await event.reply("pong"); return

@client.on(events.NewMessage(incoming=True))
async def on_pm(event: events.NewMessage.Event):
    # реагируем только на личные сообщения (private)
    if not event.is_private:
        return

    # если указан GIRL_ID — работаем только с её сообщениями
    if GIRL_ID and GIRL_ID.isdigit() and event.chat_id != int(GIRL_ID):
        return

    now = datetime.now()
    text = event.raw_text or ""

    if MODE == "draft":
        await client.send_message("me",
            f"Входящее сообщение от {event.sender_id}:\n\n{text}\n\n(режим draft — ответ вручную в этом чате)"
        )
        return

    last = last_reply_at.get(event.chat_id)
    if last and (now - last).total_seconds() < MIN_REPLY_GAP_SEC:
        return

    if in_quiet_hours(now):
        reply = add_auto_tag("Позже свяжусь, сейчас не у экрана 🌙")
        await asyncio.sleep(1.2)
        try:
            await event.reply(reply)
            last_reply_at[event.chat_id] = now
            await client.send_message("me", f"[auto] Ответ отправлен (тихие часы):\n{text}\n→ {reply}")
        except Exception:
            await client.send_message("me", "Ошибка при отправке тихого ответа.")
        return

    suggestions = suggest_replies(text)
    reply = add_auto_tag(suggestions[0])

    try:
        await asyncio.sleep(1.0 + len(text) * 0.02)
        await event.reply(reply)
        last_reply_at[event.chat_id] = now
        await client.send_message("me", f"[auto] Ответ отправлен:\n{text}\n→ {reply}")
    except FloodWaitError as fw:
        await client.send_message("me", f"FloodWait {fw.seconds}s. Ответ не отправлен.")
    except Exception as e:
        await client.send_message("me", f"Ошибка отправки: {e}")

async def main():
    print("Запуск girl_responder...")
    await client.start()
    print("Клиент запущен. Напишите /help в 'Избранное' для команд.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
