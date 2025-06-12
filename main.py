from telethon import TelegramClient, events, Button, custom
import asyncio
import os
from datetime import datetime
from script import gp, auto_search, ssf_auto
from session_manager import get_user_session, get_connected_user_client, add_user, load_users

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot_client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

running_tasks = {}

# ========================
# /start — Tampilkan tombol utama (ReplyKeyboard)
# ========================
@bot_client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    sender = await event.get_sender()
    user_id = sender.id
    name = sender.first_name
    username = sender.username

    add_user(user_id, name, username)
    users = load_users()
    user_data = users.get(str(user_id), {})
    tanggal = user_data.get("joined_at", None)
    if tanggal:
        dt = datetime.fromisoformat(tanggal)
        tanggal = dt.strftime("%d-%m-%Y %H:%M:%S")
    else:
        tanggal = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    menu = f"""
===============================
Daftar Script
===============================
Halo {name}!
Tanggal: {tanggal}

Script tersedia:
1. /attack        - Auto Attack
2. /search        - Search Musuh
3. /ssf           - Script Auto Claim SSF

/cek_session      - Cek nama session
/q                - Stop semua script

Terdaftar: {tanggal}
"""

    keyboard = custom.ReplyKeyboardMarkup(
        [
            ["▶️ Start Script", "❌ Stop Semua Script"]
        ],
        resize=True
    )
    await event.respond(menu, buttons=keyboard)


# ========================
# Handler untuk semua tombol ReplyKeyboard
# ========================
@bot_client.on(events.NewMessage)
async def handle_menu_command(event):
    text = event.raw_text.strip()
    user_id = event.sender_id

    if text == "▶️ Start Script":
        script_buttons = custom.ReplyKeyboardMarkup(
            [
                ["⚔️ Attack", "🔍 Search"],
                ["🐌 SSF", "📁 Cek Session"],
                ["❌ Stop Semua Script", "/start"]
            ],
            resize=True
        )
        await event.respond("Silakan pilih script yang ingin dijalankan:", buttons=script_buttons)

    elif text == "❌ Stop Semua Script" or text == "/q":
        await quit_all(event)

    elif text == "⚔️ Attack" or text == "/attack":
        await run_attack(event)

    elif text == "🔍 Search" or text == "/search":
        await run_search(event)

    elif text == "🐌 SSF" or text == "/ssf":
        await run_ssf(event)

    elif text == "📁 Cek Session" or text == "/cek_session":
        session_name = get_user_session(user_id)
        if session_name:
            await event.respond(f"📁 Session kamu: `{session_name}.session`")
        else:
            await event.respond("⚠️ Session tidak ditemukan.")

# ========================
# Fungsi Script
# ========================
async def run_attack(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        return

    auto_search.init(user_client, user_id)

    user_tasks = running_tasks.get(user_id, {})
    if 'attack' in user_tasks and not user_tasks['attack'].done():
        await event.respond("⚠️ Script Attack sudah berjalan.")
        return

    await event.respond("⚔️ Menjalankan Script Attack...")
    task = asyncio.create_task(gp.run_attack(user_id, user_client))
    running_tasks.setdefault(user_id, {})['attack'] = task


async def run_search(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        return

    auto_search.init(user_client, user_id)

    user_tasks = running_tasks.get(user_id, {})
    if 'search' in user_tasks and not user_tasks['search'].done():
        await event.respond("⚠️ Script Search sudah berjalan.")
        return

    await event.respond("🔍 Menjalankan Script Search...")    
    await event.respond(f"""Petunjuk Penggunaan: \n
1. Pastikan sudah di adventure paling jauh.\n
2. Kirim /adv ke bot untuk memulai script ini.\n
3. Setelah Musuh ketemu silahkan lakukan apapun.\n
4. Setelah selesai, kirim /adv lagi untuk melanjutkan.\n
5. Gunakan perintah /q untuk menghentikan script ini.""")
    task = asyncio.create_task(auto_search.run_search(user_id, user_client))
    running_tasks.setdefault(user_id, {})['search'] = task


async def run_ssf(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        return

    ssf_auto.init(user_client, user_id)

    user_tasks = running_tasks.get(user_id, {})
    if 'ssf' in user_tasks and not user_tasks['ssf'].done():
        await event.respond("⚠️ Script SSF sudah berjalan.")
        return

    await event.respond("🐌 Menjalankan Script SSF...")
    await event.respond(f"""Petunjuk Penggunaan: \n
1. Pastikan sudah perjalanan atau sampai Zou.\n
2. Gunakan perintah /ssf untuk memulai script ini.\n
3. Script akan otomatis mengklaim SSF setiap 2 detik.\n
4. Gunakan perintah /q untuk menghentikan script ini.""")
    task = asyncio.create_task(ssf_auto.run_ssf(user_id, user_client))
    running_tasks.setdefault(user_id, {})['ssf'] = task


async def quit_all(event):
    user_id = event.sender_id
    user_tasks = running_tasks.get(user_id, {})
    if not user_tasks:
        await event.respond("⚠️ Tidak ada Script yang sedang berjalan.")
        return

    stop_count = 0
    for name, task in list(user_tasks.items()):
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                stop_count += 1

    running_tasks[user_id] = {}
    await event.respond(f"❌ {stop_count} Script kamu dihentikan.")


# ========================
# Jalankan bot
# ========================
print("🤖 Bot Helper aktif. Kirim /start ke bot kamu.")
bot_client.run_until_disconnected()
