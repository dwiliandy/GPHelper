from telethon import TelegramClient, events, Button
import asyncio
import os
from datetime import datetime
from script import gp, auto_search, ssf_auto
from session_manager import get_user_session, get_connected_user_client, add_user, load_users

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot_client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Simulasi struktur task dan session
running_tasks = {}
user_sessions = {}

# ===========================
# Fungsi Bantu
# ===========================
def get_user_session(user_id):
    return user_sessions.get(user_id)

async def get_connected_user_client(user_id, event):
    # Simulasi client aktif dari session
    session_name = get_user_session(user_id)
    if not session_name:
        await event.respond("⚠️ Session kamu belum terhubung.")
        return None
    return TelegramClient(session_name, API_ID, API_HASH)

# ===========================
# Menu Utama
# ===========================
async def show_main_menu(event):
    sender = await event.get_sender()
    name = sender.first_name
    tanggal = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    menu = f"""
===============================
Daftar Script
===============================
Halo {name}!
Tanggal: {tanggal}

Script tersedia:
/attack        - Auto Attack
/search        - Search Musuh
/ssf 🐌         - Script Auto Claim SSF

/cek_session   - Cek nama session
/q             - Stop semua script
""".strip()

    inline_buttons = [
        [
            Button.inline("⚔️ /attack", b"cmd_attack"),
            Button.inline("🔍 /search", b"cmd_search"),
            Button.inline("🐌 /ssf", b"cmd_ssf")
        ]
    ]

    keyboard_buttons = [
        [Button.text("▶️ Start Script", resize=True)],
        [Button.text("❌ Stop Semua Script", resize=True)],
        [
            Button.text("/attack", resize=True),
            Button.text("/search", resize=True)
        ],
        [
            Button.text("/ssf 🐌", resize=True),
            Button.text("/cek_session", resize=True)
        ]
    ]

    await event.respond(menu, buttons=inline_buttons)
    await event.respond("Gunakan tombol di bawah atau ketik perintah.", buttons=keyboard_buttons)

# ===========================
# Handler Menu & Tombol
# ===========================
@bot_client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    await show_main_menu(event)

@bot_client.on(events.NewMessage(pattern="▶️ Start Script"))
async def handle_start_script(event):
    await show_main_menu(event)

@bot_client.on(events.NewMessage(pattern="❌ Stop Semua Script"))
async def handle_quit_script(event):
    await event.respond("/q")

@bot_client.on(events.CallbackQuery(data=b"cmd_attack"))
async def inline_attack(event):
    await event.respond("/attack")
    await event.answer("Menjalankan /attack")

@bot_client.on(events.CallbackQuery(data=b"cmd_search"))
async def inline_search(event):
    await event.respond("/search")
    await event.answer("Menjalankan /search")

@bot_client.on(events.CallbackQuery(data=b"cmd_ssf"))
async def inline_ssf(event):
    await event.respond("/ssf")
    await event.answer("Menjalankan /ssf")

# ===========================
# Command untuk Script
# ===========================
@bot_client.on(events.NewMessage(pattern="/attack"))
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

@bot_client.on(events.NewMessage(pattern="/search"))
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
    await event.respond("""📘 Petunjuk Penggunaan:

1. Pastikan sudah di adventure paling jauh.
2. Kirim /adv ke bot untuk memulai script ini.
3. Setelah Musuh ketemu silahkan lakukan apapun.
4. Setelah selesai, kirim /adv lagi untuk melanjutkan.
5. Gunakan perintah /q untuk menghentikan script ini.
""")
    task = asyncio.create_task(auto_search.run_search(user_id, user_client))
    running_tasks.setdefault(user_id, {})['search'] = task

@bot_client.on(events.NewMessage(pattern="/ssf"))
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
    await event.respond("""📘 Petunjuk Penggunaan:

1. Pastikan sudah perjalanan atau sampai Zou.
2. Gunakan perintah /ssf untuk memulai script ini.
3. Script akan otomatis mengklaim SSF setiap 2 detik.
4. Gunakan perintah /q untuk menghentikan script ini.
""")
    task = asyncio.create_task(ssf_auto.run_ssf(user_id, user_client))
    running_tasks.setdefault(user_id, {})['ssf'] = task

@bot_client.on(events.NewMessage(pattern="/cek_session"))
async def cek_session(event):
    user_id = event.sender_id
    session_name = get_user_session(user_id)
    if not session_name:
        await event.respond("⚠️ Session tidak ditemukan untuk akun kamu.")
    else:
        await event.respond(f"📦 Session kamu: `{session_name}.session`")

@bot_client.on(events.NewMessage(pattern="/q"))
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

    await show_main_menu(event)

# ===========================
# Jalankan bot
# ===========================
print("🤖 Bot Helper aktif. Kirim /start ke bot kamu.")
bot_client.run_until_disconnected()
