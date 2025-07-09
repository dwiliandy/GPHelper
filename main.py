from telethon import TelegramClient, events
from load_env import API_ID, API_HASH, BOT_TOKEN
import asyncio
import logging
from datetime import datetime
from telethon.tl.custom import Button
from script import gp, auto_search, ssf_claim, ytta_GoldenSnail, nb, mb, ev
from session_manager import get_user_session, get_connected_user_client, add_user, load_users

bot_client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

running_tasks = {}

# ===========================
# Menu Utama
# ===========================
async def show_main_menu(event):
    sender = await event.get_sender()
    user_id = sender.id
    name = sender.first_name

    add_user(user_id, name, name)
    users = load_users()
    tanggal = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        await event.respond("❌ Gagal menyambung ulang ke akun kamu.")
        return

    menu = f"""
===============================
Daftar Script
===============================
Halo {name}!
Tanggal: {tanggal}

Perintah:
/attack           - Auto Attack
/search          - Auto Search Musuh
/ssf                - Auto Claim SSF
/gs                 - Auto Golden Snail
/nb                 - Auto Attack Naval Battle
/mb                 - Auto Marine Base


/cek_session        - Cek session login
/q                            - Stop semua script
""".strip()

    inline_buttons = [
        [
            Button.inline("⚔️ Attack", b"/attack"),
            Button.inline("🔍 Search", b"/search"),
            Button.inline("🐌 Ssf", b"/ssf")
        ],
        [
            Button.inline("🐌 Gs", b"/gs"),
            Button.inline("🐌 Nb", b"/nb"),
            Button.inline("🗒 Mb", b"/mb")
        ],[
            Button.inline("Event", b"/ev"),
        ],
        [
            Button.inline("Quit", b"/q"),
            Button.inline("Cek Session", b"/cek_session")
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

# Inline button handler
@bot_client.on(events.CallbackQuery)
async def handle_inline_button(event):
    data = event.data.decode("utf-8")

    command_map = {
        "/attack": run_attack,
        "/search": run_search,
        "/ssf": run_ssf,
        "/gs": run_gs,
        "/nb": run_nb,
        "/mb": run_mb,
        '/ev': run_ev,
        "/q": quit_all,
        "/cek_session": cek_session
    }

    if data in command_map:
        await command_map[data](event)
    else:
        await event.answer("Perintah tidak dikenali", alert=True)

@bot_client.on(events.NewMessage(pattern="/attack"))
async def run_attack(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        await event.respond("❌ Gagal menyambung ulang ke akun kamu.")
        return
    gp.init(user_client)
    user_tasks = running_tasks.get(user_id, {})

    if 'attack' in user_tasks and not user_tasks['attack'].done():
        await event.respond("⚠️ Script Attack sudah berjalan untuk akun kamu.")
        return
    await event.respond("⚔️ Menjalankan Script Attack...")
    await event.respond("""📘 Petunjuk Penggunaan:

1. Pastikan sudah di pulau yang ingin di serang.
3. Script akan otomatis cek EXP Kapal dan upgrade bila sudah bisa di upgrade.
4. Gunakan perintah /q untuk menghentikan script ini.
""")
    task = asyncio.create_task(gp.run_attack(user_id, user_client))
    running_tasks.setdefault(user_id, {})['attack'] = task

@bot_client.on(events.NewMessage(pattern="/search"))
async def run_search(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        await event.respond("❌ Gagal menyambung ulang ke akun kamu.")
        return
    auto_search.init(user_client)
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
        await event.respond("❌ Gagal menyambung ulang ke akun kamu.")
        return
    ssf_claim.init(user_client)
    user_tasks = running_tasks.get(user_id, {})
    if 'ssf' in user_tasks and not user_tasks['ssf'].done():
        await event.respond("⚠️ Script SSF sudah berjalan.")
        return
    await event.respond("🐌 Menjalankan Script SSF...")
    await event.respond("""📘 Petunjuk Penggunaan:

1. Pastikan sudah perjalanan atau sampai Zou.
2. Gunakan perintah /ssf untuk memulai script ini.
3. Script akan otomatis mengklaim SSF.
4. Gunakan perintah /q untuk menghentikan script ini.
""")
    task = asyncio.create_task(ssf_claim.run_ssf(user_id, user_client))
    running_tasks.setdefault(user_id, {})['ssf'] = task

@bot_client.on(events.NewMessage(pattern="/gs"))
async def run_gs(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        await event.respond("❌ Gagal menyambung ulang ke akun kamu.")
        return
    ytta_GoldenSnail.init(user_client)
    user_tasks = running_tasks.get(user_id, {})
    if 'gs' in user_tasks and not user_tasks['gs'].done():
        await event.respond("⚠️ Script GoldenSnail sudah berjalan.")
        return
    await event.respond("🐌 Menjalankan Script GoldenSnail...")
    await event.respond("""📘 Petunjuk:

1. Simpan config di Saved Messages dengan format: `batas_gs=5` jika ingin stop saat tersisa 5.
2. Kirim perintah /gs untuk memulai script.
3. Gunakan perintah /q untuk menghentikan script ini.
""")
    task = asyncio.create_task(ytta_GoldenSnail.run_gs(user_id, user_client))
    running_tasks.setdefault(user_id, {})['gs'] = task

@bot_client.on(events.NewMessage(pattern="/nb"))
async def run_nb(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        await event.respond("❌ Gagal menyambung ulang ke akun kamu.")
        return
    nb.init(user_client)
    user_tasks = running_tasks.get(user_id, {})
    if 'nb' in user_tasks and not user_tasks['nb'].done():
        await event.respond("Script NavalBattle sudah berjalan.")
        return
    await event.respond("🐌 Menjalankan Script NavalBattle...")
    await event.respond("""📘 Petunjuk Penggunaan:

1. Pastikan kamu sudah berada di area laut (Adventure).
2. Simpan konfigurasi di Saved Messages:
   `snail = 25/50/75/100/125/150/175/200/225/250/275/300/_`
   `use_grand_snail = yes/no`
3. Kirim perintah /nb untuk memulai script NavalBattle.
4. Script akan otomatis menyerang.
5. Gunakan perintah /q untuk menghentikan script ini.
""")
    task = asyncio.create_task(nb.run_nb(user_client))
    running_tasks.setdefault(user_id, {})['nb'] = task



@bot_client.on(events.NewMessage(pattern="/mb"))
async def run_mb(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        await event.respond("❌ Gagal menyambung ulang ke akun kamu.")
        return
    mb.init(user_client)  # ✅ gunakan init dari script mb.py
    user_tasks = running_tasks.get(user_id, {})
    if 'mb' in user_tasks and not user_tasks['mb'].done():
        await event.respond("Script MarineBase sudah berjalan.")
        return
    await event.respond("🗒 Menjalankan Script MarineBase...")
    await event.respond("""📘 Petunjuk Penggunaan:

1. Pastikan kamu sudah berada di Grove46.
2. Script akan otomatis memasukkan kru ke misi dan mengeluarkan lagi jika requirement tidak tercapai.
3. Gunakan perintah /q untuk menghentikan script ini.
""")
    task = asyncio.create_task(mb.run_mb(user_client))
    running_tasks.setdefault(user_id, {})['mb'] = task



@bot_client.on(events.NewMessage(pattern="/ev"))
async def run_ev(event):
    user_id = event.sender_id
    user_client = await get_connected_user_client(user_id, event)
    if not user_client:
        await event.respond("❌ Gagal menyambung ulang ke akun kamu.")
        return
    ev.init(user_client)  # ✅ gunakan init dari script mb.py
    user_tasks = running_tasks.get(user_id, {})
    if 'ev' in user_tasks and not user_tasks['ev'].done():
        await event.respond("Script Event.")
        return
    await event.respond("🗒 Menjalankan Event...")
    task = asyncio.create_task(ev.run_ev(user_client))
    running_tasks.setdefault(user_id, {})['ev'] = task

# ========================
#  /q — Matikan semua script
# ========================
@bot_client.on(events.NewMessage(pattern="/q"))
async def quit_all(event):
    user_id = event.sender_id
    user_tasks = running_tasks.get(user_id, {})
    if not user_tasks:
        await event.respond("⚠️ Tidak ada script yang sedang berjalan.")
        return

    stop_count = 0

    # Ambil user_client jika tersedia
    user_client = await get_connected_user_client(user_id, event)
    # ✅ Cancel semua task
    for name, task in list(user_tasks.items()):
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                stop_count += 1

    # ✅ Kosongkan task list
    running_tasks[user_id] = {}

    # ✅ Disconnect client jika masih terhubung
    if user_client and user_client.is_connected():
        await user_client.disconnect()
        logging.info(f"🔌 User {user_id} disconnected via /q")

    await event.respond(f"❌ {stop_count} script kamu dihentikan & koneksi dimatikan.")

@bot_client.on(events.NewMessage(pattern="/cek_session"))
async def cek_session(event):
    user_id = event.sender_id
    session_name = get_user_session(user_id)
    if not session_name:
        await event.respond("⚠️ Session tidak ditemukan untuk akun kamu.")
        return
    await event.respond(f"📦Session kamu: `{session_name}.session`")

print("Bot Helper aktif. Kirim /start ke bot kamu.")
bot_client.run_until_disconnected() 