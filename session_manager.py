import json
import os
from pathlib import Path
from telethon import TelegramClient, events
from datetime import datetime

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SESSION_MAP_FILE = Path("sessions/sessions_map.json")
USERS_FILE = Path("user_sessions.json")  # ganti nama file jadi users.json

user_clients = {}  # Dictionary untuk menyimpan client aktif per user

def load_session_map():
    if SESSION_MAP_FILE.exists():
        with open(SESSION_MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_session_map(session_map):
    with open(SESSION_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(session_map, f, indent=2, ensure_ascii=False)

def set_user_session(user_id: int, session_name: str):
    session_map = load_session_map()
    session_map[str(user_id)] = {"session_name": session_name}
    save_session_map(session_map)

def get_user_session(user_id):
    if SESSION_MAP_FILE.exists():
        with open(SESSION_MAP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(str(user_id), {}).get("session_name")
    return None

async def get_connected_user_client(user_id, event):
    if user_id in user_clients:
        client = user_clients[user_id]
        if not client.is_connected():
            await client.connect()
        return client

    session_name = get_user_session(user_id)
    if not session_name:
        await event.respond("⚠️ Session tidak ditemukan.")
        return None

    client = TelegramClient(f"sessions/{session_name}", API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        await event.respond("🔐 Akun belum login. Silakan login dahulu.")
        return None

    user_clients[user_id] = client  # simpan instance
    return client

async def disconnect_user_client(user_id):
    if user_id in user_clients:
        try:
            await user_clients[user_id].disconnect()
        except Exception:
            pass
        del user_clients[user_id]

def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_user(user_id: int, name: str, username: str = None):
    users = load_users()

    if str(user_id) not in users:
        users[str(user_id)] = {
            "name": name,
            "username": username,
            "joined_at": datetime.now().isoformat()
        }
        save_users(users)
        print(f"✅ User baru ditambahkan: {name} ({user_id})")