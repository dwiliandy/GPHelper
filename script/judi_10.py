import asyncio
import random
import re
import logging
from telethon import events
from telethon.errors import FloodWaitError

bot_username = 'GrandPiratesBot'

running_flags = {}
user_state = {}
handlers = {}  # Menyimpan handler per client

async def update_config_from_saved(client, user_id):
    state = user_state[user_id]
    async for message in client.iter_messages('me', limit=10):
        if not message.text:
            continue
        lines = message.text.strip().splitlines()
        if not lines:
            continue
        if lines[0].strip().startswith("===GRANDPIRATES CONFIGURATION==="):
            for line in lines[1:]:
                line = line.strip().lower()
                if line.startswith("total_play"):
                    match = re.search(r"total_play\s*=\s*(\d+|_)", line)
                    if match:
                        state["total_play"] = match.group(1)
            break
    logging.info(f"🔧 Konfigurasi diperbarui untuk user {user_id}: {state}")

def init(client):
    # Cek apakah handler sudah ditambahkan ke client ini
    if client in handlers:
        return

    async def handler(event):
        try:
            user = await event.client.get_me()
            user_id = user.id

            if not running_flags.get(user_id, False):
                return

            text = event.raw_text
            state = user_state[user_id]

           

            if "🎰 VIPArea: CasinoKing 🎰" in text:
                # await event.client.send_message(bot_username, "/visit_RainDinners")
            elif "🎰 Rainbase: RainDinners" in text:
                # await event.client.send_message(bot_username, "/casinoKing")
            

        except Exception as e:
            logging.error(f"[EVENT ERROR] {e}")

    # Tambahkan handler dan simpan referensinya
    client.add_event_handler(handler, events.NewMessage(from_users=bot_username))
    handlers[client] = handler
    logging.info("[INIT] Handler NavalBattle berhasil didaftarkan")

async def run_nb(client):
    me = await client.get_me()
    user_id = me.id

    running_flags[user_id] = True
    user_state[user_id] = {
        "snail": "_",
        "use_grand_snail": "no"
    }

    logging.info(f"⚓ Memulai Naval Battle untuk user {user_id}")
    client.loop.create_task(keep_alive(client))

    try:
        
        await client.send_message(bot_username, "/adv")
        text = 
        if "🎰 VIPArea: CasinoKing 🎰" in text:
                # await event.client.send_message(bot_username, "/visit_RainDinners")
            elif "🎰 Rainbase: RainDinners" in text:
                # await event.client.send_message(bot_username, "/casinoKing")
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
            if asyncio.current_task().cancelled():
                break
    except asyncio.CancelledError:
        logging.warning(f"❌ NavalBattle dibatalkan untuk user {user_id}")
        raise
    except FloodWaitError as e:
        logging.warning(f"[FLOOD] Tunggu {e.seconds} detik")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logging.error(f"[FATAL] NavalBattle error: {e}")
    finally:
        # Bersihkan semua data & handler
        running_flags.pop(user_id, None)
        user_state.pop(user_id, None)
        if client in handlers:
            client.remove_event_handler(handlers[client], events.NewMessage(from_users=bot_username))
            del handlers[client]
            logging.info(f"[HANDLER] Dihapus untuk client {user_id}")
        logging.info(f"✅ Naval Battle selesai untuk user {user_id}")
