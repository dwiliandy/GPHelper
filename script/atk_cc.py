from telethon import events
import asyncio
import re
import logging

bot_username = 'GrandPiratesBot'

# Per-user tracking
running_flags = {}     # user_id = bool
user_state = {}        # user_id = { is_attacking, buff_event }
handler_registered = False

def init(client):
    global handler_registered
    if handler_registered:
        return

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        user = await event.client.get_me()
        user_id = user.id

        if not running_flags.get(user_id, False):
            return

        text = event.raw_text

        # 🔁 Proses pesan balasan dari /cc_buff_FH
        if "Kru yang bisa disembuhkan adalah kru yang masih hidup" in text:
            print("[BOT] 📥 Pesan buff diterima. Proses HP kru...")
            await handle_buff_response(event, user_id)
            return

        elif 'Serang dan kalahkan musuh-musuh lain yang ada di ' in text:
            print("[BOT] ⚔️ Balasan dari /cc_battle diterima. Klik tombol pertama...")
            await asyncio.sleep(2)
            await event.click(0)
            return

        elif 'Lawan sudah kabur, silakan cari lawan lain' in text:
            print("[BOT] 🚫 Lawan kabur. Klik tombol untuk cari lawan lagi.")
            await asyncio.sleep(4)
            await event.click(0)
            return

        elif 'Kamu mencari musuh dan bertemu dengan kru Bajak Laut' in text:
            match = re.search(r'🏴‍☠️\s*([\w\'’\-]+):\s*[\w\'’\-]+\[([A-Z]+)\]', text)
            if not match:
                print("[BOT] ❌ Format musuh tidak dikenali.")
                return

            group = match.group(1).strip()
            tier = match.group(2).strip()

            print(f"[MUSUH] 🎯 Grup: {group}, Tier: {tier}")

            blocked_groups = user_state[user_id].get("blocked_groups", set())
            valid_tiers = user_state[user_id].get("valid_tiers", set())

            if group in blocked_groups and tier in valid_tiers:
                print("[ACTION] 🛑 Musuh dihindari. Klik tombol cari lagi...")
                await asyncio.sleep(4)
                await event.click(0)
            else:
                print("[ACTION] ✅ Musuh valid. Mencari command /cc_serang...")
                serang_commands = re.findall(r'/cc_serang_\d+', text)
                if serang_commands:
                    print(f"[ACTION] 🚀 Menyerang dengan: {serang_commands[0]}")
                    user_state[user_id]["is_attacking"] = True
                    await asyncio.sleep(1.5)
                    await event.client.send_message(bot_username, serang_commands[0])
                    await asyncio.sleep(1.5)
                    user_state[user_id]["is_attacking"] = False
                else:
                    print("[ACTION] ⚠️ Tidak ditemukan command /cc_serang.")
                    await asyncio.sleep(4)
                    await event.click(0)
            return

        elif "Kamu menyerang" in text and "berhasil menghasilkan" in text:
            print("[ACTION] 🥊 Serangan berhasil. Klik tombol pertama untuk lanjut cari lawan...")
            if event.buttons:
                await asyncio.sleep(2)
                await event.click(0)
            else:
                print("[ACTION] ⚠️ Tidak ada tombol untuk klik.")
            return

        elif "Tunggu 4 detik sebelum kamu bisa mencari musuh lain lagi" in text:
            print("[ACTION] ⏳ Delay 4 detik. Tunggu & klik tombol...")
            await asyncio.sleep(4)
            if event.buttons:
                await event.click(0)
                print("[ACTION] ✅ Klik tombol pertama setelah delay.")
            else:
                print("[ACTION] ⚠️ Tidak ada tombol untuk klik setelah delay.")
            return

        else:
            print("[BOT] 🔍 Tidak ada aksi yang cocok. Menunggu...")

def parse_buff_targets(text):
    matches = re.findall(
        r'(/cc_buff_FH_\d+).*?\(HP:\s*([\d,]+)/([\d,]+)\)\s*([\d.]+)%',
        text, re.DOTALL
    )
    low_hp = []
    for cmd, hp_now, hp_max, percent in matches:
        if float(percent) < 25.0:
            low_hp.append((cmd, percent))
    return low_hp


async def handle_buff_response(event, user_id):
    targets = parse_buff_targets(event.raw_text)

    if not targets:
        print("[BUFF] ✅ Tidak ada kru HP <25%. Kirim /cc_battle")
        await asyncio.sleep(2)
        await event.client.send_message(bot_username, '/cc_battle')
        return

    for cmd, percent in targets:
        print(f"[BUFF] 💊 Kirim: {cmd} ({percent}%)")
        await event.client.send_message(bot_username, cmd)
        await asyncio.sleep(2)

    print("[BUFF] ✅ Semua kru low HP selesai. Kirim /cc_battle")
    await asyncio.sleep(2)
    await event.client.send_message(bot_username, '/cc_battle')


async def get_config_from_saved(client):
    async for msg in client.iter_messages('me', search='tier'):
        tier_match = re.search(r'tier=\s*(.+)', msg.raw_text, re.IGNORECASE)
        ally_match = re.search(r'ally=\s*(.+)', msg.raw_text, re.IGNORECASE)

        if tier_match and ally_match:
            tiers = set(map(str.strip, tier_match.group(1).split(',')))
            groups = set(map(str.strip, ally_match.group(1).split(',')))
            print("[CONFIG] ✅ Konfigurasi ditemukan di Saved Messages:")
            print(f" - Tier yang dihindari : {tiers}")
            print(f" - Group yang dihindari: {groups}")
            return tiers, groups

    print("[CONFIG] ❌ Tidak menemukan konfigurasi 'tier:' & 'ally:' di Saved Messages.")
    return set(), set()


async def run_cc_battle(user_id, client):
    tiers, groups = await get_config_from_saved(client)

    running_flags[user_id] = True
    user_state[user_id] = {
        "buff_event": asyncio.Event(),
        "is_attacking": False,
        "valid_tiers": set(tiers),
        "blocked_groups": set(groups)
    }

    print(f"[CC] ▶️ Memulai Auto CC Battle untuk user {user_id}")

    try:
        while running_flags.get(user_id, False):
            await asyncio.sleep(600)
            print("[CC] 🕒 Waktu buff 10 menit. Cek status serangan...")

            while user_state[user_id].get("is_attacking", False):
                print("[CC] ⚔️ Sedang menyerang. Tunggu selesai...")
                await asyncio.sleep(1)

            print("[CC] 💎 Kirim /cc_buff_FH sekarang...")
            await client.send_message(bot_username, '/cc_buff_FH')
    except asyncio.CancelledError:
        print(f"❌ Auto CC Battle dihentikan untuk user {user_id}")
        raise
    finally:
        running_flags[user_id] = False
        logging.info(f"✅ Auto CC Battle selesai untuk user {user_id}")
