import asyncio
import re
import logging
import random
from telethon import events
from telethon.errors import FloodWaitError

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

bot_username = 'GrandPiratesBot'

running_flags = {}
user_state = {}
handlers = {}

async def update_config_from_saved(client, user_id):
    state = user_state[user_id]
    async for message in client.iter_messages('me', limit=10):
        if not message.text:
            continue
        lines = message.text.strip().splitlines()
        if not lines:
            continue
        if lines[0].strip().startswith("===EVENT==="):
            for line in lines[1:]:
                line = line.strip()
                if line.startswith("event_cmd"):
                    match = re.search(r"event_cmd\s*=\s*['\"]?([^\s'\"]+)", line)
                    if match:
                        state["event_cmd"] = f"/{match.group(1)}"
                elif line.startswith("skip_enemies"):
                    match = re.search(r"skip_enemies\s*=\s*(.+)", line)
                    if match:
                        raw = match.group(1)
                        enemies = [e.strip() for e in raw.split(",") if e.strip()]
                        state["skip_enemies"] = enemies
            break
    logging.info(f"🔧 Konfigurasi EVENT diperbarui untuk user {user_id}: {state}")

def has_button(event, label):
    return any(button.text == label for row in (event.buttons or []) for button in row)

async def click_button(event, label):
    for row in event.buttons or []:
        for button in row:
            if button.text == label:
                try:
                    await event.click(text=label)
                    logging.info(f"[CLICK] {label}")
                    return True
                except Exception as e:
                    logging.warning(f"[CLICK ERROR] {label} gagal: {e}")
    return False

def init(client):
    if client in handlers:
        return

    async def handler(event):
        try:
            user = await event.client.get_me()
            user_id = user.id

            if not running_flags.get(user_id):
                return

            state = user_state[user_id]
            text = event.raw_text

            # Saat membuka /kapal
            if "EXP:" in text and "Kapasitas:" in text:
                match = re.search(r'EXP:\s+\(([\d,]+)/([\d,]+)\)', text)
                if match:
                    state["current_exp"] = int(match.group(1).replace(",", ""))
                    state["need_exp"] = int(match.group(2).replace(",", ""))
                    logging.info(f"[EXP] {state['current_exp']} / {state['need_exp']}")
                    await asyncio.sleep(1)
                    await event.client.send_message(bot_username, state["event_cmd"])
                return

            # Petualangan dimulai
            if ("Masing-masing adventure terdiri dari" in text or "Pilih maksimal 14 kru" in text) and event.buttons:
                await asyncio.sleep(1)
                await event.click(0)
                return

            # Musuh muncul
            if "dihadang oleh" in text:
                match = re.search(r'👿 (.+)', text)
                if match:
                    enemy = match.group(1).strip()
                    logging.info(f"[MUSUH] {enemy}")
                    await asyncio.sleep(1)
                    if enemy in state["skip_enemies"]:
                        logging.info("[AKSI] Skip musuh")
                        await event.click(1, 0)
                    else:
                        logging.info("[AKSI] Lawan musuh")
                        await event.click(0, 0)
                return

            # Restore energy
            if "saat energi di bawah 10%" in text and event.buttons:
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, f"{state['event_cmd']}_restore")
                return

            if "Apa kamu yakin ingin menggunakan" in text and event.buttons:
                await asyncio.sleep(1)
                await event.click(0)
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, state["event_cmd"])
                return

            # Menang
            if "KAMU MENANG!!" in text:
                match = re.search(r'❇️ ([\d,]+) EXP Kapal', text)
                if match:
                    gained = int(match.group(1).replace(",", ""))
                    state["current_exp"] += gained
                    logging.info(f"[EXP] +{gained} → {state['current_exp']} / {state['need_exp']}")
                    if state["current_exp"] >= state["need_exp"]:
                        logging.info("[LEVEL UP] Mengirim /levelupkapal_DEF")
                        await asyncio.sleep(1)
                        await event.client.send_message(bot_username, "/levelupkapal_DEF")
                await asyncio.sleep(1)
                await event.click(0)
                return

            if "Musuh menang..." in text and event.buttons:
                logging.info("[INFO] Musuh menang")
                await asyncio.sleep(1)
                await event.click(0)
                return

        except Exception as e:
            logging.error(f"[EVENT ERROR] {e}")

    client.add_event_handler(handler, events.NewMessage(from_users=bot_username))
    handlers[client] = handler
    logging.info("[INIT] Handler A7S berhasil didaftarkan")

async def run_ev(client):
    me = await client.get_me()
    user_id = me.id

    running_flags[user_id] = True
    user_state[user_id] = {
        "event_cmd": "/a7s_3",
        "skip_enemies": [],
        "current_exp": 0,
        "need_exp": 9999999
    }

    logging.info(f"🚀 Mulai A7S untuk user {user_id}")
    try:
        await update_config_from_saved(client, user_id)
        await client.send_message(bot_username, "/kapal")
        while running_flags.get(user_id):
            await asyncio.sleep(2)
            if asyncio.current_task().cancelled():
                break
    except asyncio.CancelledError:
        logging.warning(f"❌ A7S dibatalkan untuk user {user_id}")
        raise
    except FloodWaitError as e:
        logging.warning(f"[FLOOD] Tunggu {e.seconds} detik")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logging.error(f"[FATAL] A7S error: {e}")
    finally:
        running_flags.pop(user_id, None)
        user_state.pop(user_id, None)
        if client in handlers:
            client.remove_event_handler(handlers[client], events.NewMessage(from_users=bot_username))
            del handlers[client]
            logging.info(f"[HANDLER] Dihapus untuk client {user_id}")
        logging.info(f"✅ A7S selesai untuk user {user_id}")
