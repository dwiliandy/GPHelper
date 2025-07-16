import logging
from telethon import events
import asyncio
import re

# Logging hanya ke console
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

bot_username = 'GrandPiratesBot'

running_flags = {}     # user_id: bool
user_state = {}        # user_id: { tmp, ssf }
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
        state = user_state.get(user_id)
        if not state:
            return

        logging.debug(f"[SSF:{user_id}] Pesan diterima:\n{text}")

        # 1. Saat daftar incubator muncul
        if 'Kalahkan musuh-musuh yang ada di Zou untu mendapatkannya.' in text:
            state["tmp"] = 0
            state["ssf"] = [x for x in event.text.split() if '/ssf_incubator' in x]
            logging.info(f"[SSF:{user_id}] Ditemukan {len(state['ssf'])} inkubator.")
            if state["ssf"]:
                await process_all_incubators(event, user_id)
            else:
                logging.warning(f"[SSF:{user_id}] Tidak ditemukan command /ssf_incubator.")
            return

        # 2. SeaSnail dalam status berkembang atau bisa dipanen
        if any(msg in text for msg in [
            'SeaSnail masih belum berkembang',
            'SeaSnail akan bertambah besar',
            'SeaSnail sudah mencapai versi paling besar'
        ]):
            match = re.search(r'(/ssf_incubator_\d+_ambil)', text)
            if match:
                logging.info(f"[SSF:{user_id}] Melakukan panen: {match.group(1)}")
                await asyncio.sleep(1)
                await event.respond(match.group(1))
            else:
                logging.info(f"[SSF:{user_id}] Tidak ada tombol ambil ditemukan.")
            return

        # 3. Jika kru dikembalikan
        if 'Kru peternak dikembalikan' in text:
            match = re.search(r'/ssf_incubator_(\d+)_(\d+)', text)
            if match:
                logging.info(f"[SSF:{user_id}] Kru dikembalikan, jalankan ulang: {match.group(0)}")
                await asyncio.sleep(1)
                await event.respond(match.group(0))
            return

        # 4. Konfirmasi mempekerjakan kru
        if 'Apa kamu yakin ingin mempekerjakan' in text:
            logging.info(f"[SSF:{user_id}] Konfirmasi mempekerjakan kru")
            await asyncio.sleep(1)
            await event.click(0)
            return

        # 5. Setelah berhasil mempekerjakan
        if 'Berhasil mempekerjakan' in text:
            match = re.search(r'(/ssf_incubator_\d+)', text)
            if match:
                logging.info(f"[SSF:{user_id}] Lanjut setelah mempekerjakan: {match.group(1)}")
                await asyncio.sleep(1)
                await event.respond(match.group(1))
            return

        # 6. Jika muncul petunjuk cek /seaSnailFarm, lanjut ke item berikutnya
        if 'cek /seaSnailFarm' in text:
            state["tmp"] += 1
            if state["tmp"] < len(state["ssf"]):
                next_cmd = state["ssf"][state["tmp"]]
                logging.info(f"[SSF:{user_id}] Lanjut ke inkubator berikutnya: {next_cmd}")
                await asyncio.sleep(1)
                await event.respond(next_cmd)
            else:
                logging.info(f"[SSF:{user_id}] Semua inkubator sudah diproses.")
            return

    handler_registered = True


async def process_all_incubators(event, user_id):
    state = user_state[user_id]
    for idx, cmd in enumerate(state["ssf"]):
        state["tmp"] = idx
        logging.info(f"[SSF:{user_id}] Kirim command [{idx + 1}/{len(state['ssf'])}]: {cmd}")
        await asyncio.sleep(1.5)
        await event.respond(cmd)
        await asyncio.sleep(3)


async def run_ssf(user_id, client):
    running_flags[user_id] = True
    user_state[user_id] = {
        "tmp": 0,
        "ssf": []
    }

    logging.info(f"⚙️ Memulai Script SSF untuk user {user_id}")
    try:
        await client.send_message(bot_username, "/ssf")
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
            if asyncio.current_task().cancelled():
                break
    except asyncio.CancelledError:
        logging.warning(f"❌ Script SSF dibatalkan untuk user {user_id}")
        raise
    finally:
        running_flags[user_id] = False
        logging.info(f"✅ SSF selesai untuk user {user_id}")
