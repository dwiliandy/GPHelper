from telethon import TelegramClient, events

from load_env import API_ID, API_HASH, BOT_TOKEN
import asyncio
from datetime import datetime
from telethon.tl.custom import Button
from script import gp, auto_search, ssf_claim
from session_manager import get_user_session, get_connected_user_client, add_user, load_users 

bot_client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)# Akun user untuk mengirim perintah ke GrandPiratesBot (pakai nomor HP)
# user_client = TelegramClient('session_name', API_ID, API_HASH)


# Dictionary untuk menyimpan task-task aktif
running_tasks = {}


# ===========================
# Menu Utama
# ===========================
async def show_main_menu(event):

    # Panggil add_user untuk simpan data user jika belum ada
    sender = await event.get_sender()
    user_id = sender.id
    name = sender.first_name

    add_user(user_id, name, name) 
    users = load_users()
    user_data = users.get(str(user_id), {})
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
/ssf           - Script Auto Claim SSF

/cek_session   - Cek nama session
/q             - Stop semua script
""".strip()

    inline_buttons = [
        [
            Button.inline("⚔️ /attack", b"/attack"),
            Button.inline("🔍 /search", b"/search"),
            Button.inline("🐌 /ssf", b"/ssf")
        ]
    ]

    keyboard_buttons = [
        [Button.text("▶️ Start Script", resize=True)],
        [Button.text("/q", resize=True)]
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



@bot_client.on(events.NewMessage(pattern="/attack"))
async def run_attack(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        return

    auto_search.init(user_client, user_id)  # Daftarkan event handler jika ada
    user_tasks = running_tasks.get(user_id, {})

    if 'attack' in user_tasks and not user_tasks['attack'].done():
        await event.respond("⚠️ Script Attack sudah berjalan untuk akun kamu.")
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

    ssf_claim.init(user_client, user_id)
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
    task = asyncio.create_task(ssf_claim.run_ssf(user_id, user_client))
    running_tasks.setdefault(user_id, {})['ssf'] = task

# ========================
#  /q — Matikan semua script
# ========================
@bot_client.on(events.NewMessage(pattern="/q"))
async def quit_all(event):
    user_id = event.sender_id
    user_tasks = running_tasks.get(user_id, {})
    if not user_tasks:
        await event.respond("⚠️ Tidak ada Script yang sedang berjalan untuk kamu.")
        return


    stop_count = 0

    for name, task in list(user_tasks.items()):
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                stop_count += 1

    # Bersihkan task user ini
    running_tasks[user_id] = {}
    print (running_tasks)
    await event.respond(f"❌ {stop_count} Script kamu dihentikan.")


# ========================
#  /cek_session — Cek nama session
# ========================
@bot_client.on(events.NewMessage(pattern="/cek_session"))
async def cek_session(event):
    user_id = event.sender_id
    session_name = get_user_session(user_id)
    if not session_name:
        await event.respond("⚠️ Session tidak ditemukan untuk akun kamu.")
        return
    await event.respond(f"📦 Session kamu: `{session_name}.session`")

# ========================
#  Jalankan bot
# ========================
print("🤖 Bot Helper aktif. Kirim /start ke bot kamu.")
bot_client.run_until_disconnected()