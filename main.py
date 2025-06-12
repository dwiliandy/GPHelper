from telethon import TelegramClient, events
import asyncio
import os
from datetime import datetime
from telethon.tl.custom import Button
from script import gp
from script import auto_search
from script import ssf_auto
from session_manager import get_user_session, get_connected_user_client, add_user, load_users 


API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot_client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


# Dictionary untuk menyimpan task-task aktif
running_tasks = {}


@bot_client.on(events.NewMessage(pattern="Start"))
async def show_reply_keyboard(event):
      now = datetime.now()
      tanggal = now.strftime("%A, %d %B %Y - %H:%M:%S")
      sender = await event.get_sender()
      user_id = sender.id
      name = sender.first_name
      username = sender.username
      
      # Panggil add_user untuk simpan data user jika belum ada
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
      # buttons = [
      #     [Button.inline("⚔️ Attack", b"attack")]
      # ]

      await event.respond(menu)


# ========================
#  /start — Tampilkan menu
# ========================
@bot_client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    sender = await event.get_sender()
    user_id = sender.id
    name = sender.first_name
    username = sender.username

    # Panggil add_user untuk simpan data user jika belum ada
    add_user(user_id, name, username) 

    users = load_users()
    user_data = users.get(str(user_id), {})
    tanggal = user_data.get("joined_at", None)
    if tanggal:
        dt = datetime.fromisoformat(tanggal)
        tanggal = dt.strftime("%d-%m-%Y %H:%M:%S")
    else:
        tanggal = datetime.now().strftime("%d-%m-%Y %H:%M:%S")



    # Tampilkan menu
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
    await event.respond(menu)

# ========================
#  /attack — Jalankan Script GP
# ========================
@bot_client.on(events.CallbackQuery(data=b"attack"))
async def handle_attack_button(event):
    await event.answer()  # Tutup loading animasi di tombol

    message = await event.get_message()
    message.message = "/attack"  # Simulasikan pesan seolah user ketik /attack

    await run_attack(message)  # Panggil handler /attack

@bot_client.on(events.NewMessage(pattern="/attack"))
async def run_attack(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)

    if not user_client:
        return  # Pesan error sudah dikirim oleh get_connected_user_client

    auto_search.init(user_client, user_id)  # Daftarkan event handler jika ada

    user_tasks = running_tasks.get(user_id, {})

    if 'attack' in user_tasks and not user_tasks['attack'].done():
        await event.respond("⚠️ Script Attack sudah berjalan untuk akun kamu.")
        return

    await event.respond("⚔️ Menjalankan Script Attack...")

    # Jalankan task
    task = asyncio.create_task(gp.run_attack(user_id, user_client))

    # Simpan task per user
    if user_id not in running_tasks:
        running_tasks[user_id] = {}
    running_tasks[user_id]['attack'] = task

@bot_client.on(events.NewMessage(pattern="/search"))
async def run_search(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)

    if not user_client:
        return  # Pesan error sudah dikirim oleh get_connected_user_client

    auto_search.init(user_client, user_id)  # Daftarkan event handler jika ada

    user_tasks = running_tasks.get(user_id, {})

    if 'search' in user_tasks and not user_tasks['search'].done():
        await event.respond("⚠️ Script Search sudah berjalan untuk akun kamu.")
        return

    await event.respond("🔍 Memulai Script Search...")
    await event.respond(f"""Petunjuk Penggunaan: \n
          1. Pastikan sudah di adventure paling jauh.\n
          2. Kirim /adv ke bot untuk memulai script ini.\n
          3. Setelah Musuh ketemu silahkan lakukan apapun.\n
          4. Setelah selesai, kirim /adv lagi untuk melanjutkan.\n
          5. Gunakan perintah /q untuk menghentikan script ini.""")

    # Jalankan task
    task = asyncio.create_task(auto_search.run_search(user_id, user_client))

    # Simpan task per user
    if user_id not in running_tasks:
        running_tasks[user_id] = {}
    running_tasks[user_id]['search'] = task

# ========================
#  /ssf — Jalankan Script Auto CLaim SSF
# ========================
@bot_client.on(events.NewMessage(pattern="/ssf"))
async def run_ssf(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)

    if not user_client:
        return  # Pesan error sudah dikirim oleh get_connected_user_client

    ssf_auto.init(user_client, user_id)  # Daftarkan event handler jika ada

    user_tasks = running_tasks.get(user_id, {})

    if 'ssf' in user_tasks and not user_tasks['ssf'].done():
        await event.respond("⚠️ Script Claim SSF sudah berjalan untuk akun kamu.")
        return

    await event.respond("⚔️ Menjalankan Script Claim SSF...")
    
    await event.respond(f"""Petunjuk Penggunaan: \n
          1. Pastikan sudah perjalanan atau sampai Zou.\n
          2. Gunakan perintah /ssf untuk memulai script ini.\n
          3. Script akan otomatis mengklaim SSF setiap 2 detik.\n
          4. Gunakan perintah /q untuk menghentikan script ini.""")
    

    # Jalankan task
    task = asyncio.create_task(ssf_auto.run_ssf(user_id, user_client))

    # Simpan task per user
    if user_id not in running_tasks:
        running_tasks[user_id] = {}
    running_tasks[user_id]['ssf'] = task


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