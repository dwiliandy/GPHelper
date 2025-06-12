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
# /start — Tampilkan menu awal + tombol keyboard
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

    buttons = custom.ReplyKeyboardMarkup(
        [
            ["▶️ Start Script", "❌ Stop Semua Script"]
        ],
        resize=True
    )

    await event.respond(menu, buttons=buttons)

# ========================
# Keyboard: Start Script
# ========================
@bot_client.on(events.NewMessage(pattern="▶️ Start Script"))
async def show_commands_handler(event):
    buttons = custom.ReplyKeyboardMarkup(
        [
            ["⚔️ Attack", "🔍 Search"],
            ["📦 SSF", "📁 Cek Session"],
            ["❌ Stop Semua Script", "/start"]
        ],
        resize=True
    )
    await event.respond("Pilih salah satu script berikut:", buttons=buttons)

# ========================
# Handler untuk semua tombol
# ========================
@bot_client.on(events.NewMessage(pattern="⚔️ Attack"))
async def handle_attack(event):
    await run_attack(event)

@bot_client.on(events.NewMessage(pattern="🔍 Search"))
async def handle_search(event):
    await run_search(event)

@bot_client.on(events.NewMessage(pattern="📦 SSF"))
async def handle_ssf(event):
    await run_ssf(event)

@bot_client.on(events.NewMessage(pattern="📁 Cek Session"))
async def handle_cek_session(event):
    user_id = event.sender_id
    session_name = get_user_session(user_id)
    if not session_name:
        await event.respond("⚠️ Session tidak ditemukan untuk akun kamu.")
        return
    await event.respond(f"📦 Session kamu: `{session_name}.session`")

@bot_client.on(events.NewMessage(pattern="❌ Stop Semua Script"))
@bot_client.on(events.NewMessage(pattern="/q"))
async def handle_quit_all(event):
    await quit_all(event)

# ========================
# Fungsi Jalankan Script
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
    await event.respond("""Petunjuk Penggunaan: \n
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

    await event.respond("📦 Menjalankan Script SSF...")
    await event.respond("""Petunjuk Penggunaan: \n
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
# Jalankan Bot
# ========================
print("🤖 Bot Helper aktif. Kirim /start ke bot kamu.")
bot_client.run_until_disconnected()
