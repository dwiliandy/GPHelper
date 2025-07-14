import asyncio
import re
import logging
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
        if lines[0].strip().startswith("===GRANDPIRATES CONFIGURATION==="):
            for line in lines[1:]:
                line = line.strip()
                if line.startswith("event_cmd"):
                    print(f"🔧 Memperbarui konfigurasi untuk user {user_id}: {line}")
                    match = re.search(r"event_cmd\s*=\s*['\"]?([^\s'\"]+)", line)
                    if match:
                        state["event_cmd"] = f"/{match.group(1)}"
                elif line.startswith("skip_enemies"):
                    match = re.search(r"skip_enemies\s*=\s*(.+)", line)
                    if match:
                        state["skip_enemies"] = [e.strip() for e in match.group(1).split(",") if e.strip()]
                elif line.startswith("max_enemy_event"):
                    match = re.search(r"max_enemy_event\s*=\s*(\d+)", line)
                    if match:
                        state["max_enemy"] = int(match.group(1))
            break
    logging.info(f"🔧 Konfigurasi EVENT diperbarui: {state}")

def parse_encounter(text):
    enemies = []
    for line in text.splitlines():
        if '👿' in line:
            match = re.search(r'👿 (.+)', line)
            if match:
                name = match.group(1).split('+')[0].strip()
                enemies.append(name)
    return enemies

async def click_button(event, label):
    for row in event.buttons or []:
        for button in row:
            if button.text == label:
                try:
                    await event.click(text=label)
                    logging.info(f"[CLICK] {label}")
                    return True
                except Exception as e:
                    logging.warning(f"[CLICK ERROR] Gagal klik {label}: {e}")
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

            if "EXP:" in text and "Kapasitas:" in text:
                match = re.search(r'EXP:\s+\(([\d,]+)/([\d,]+)\)', text)
                if match:
                    state["current_exp"] = int(match.group(1).replace(",", ""))
                    state["need_exp"] = int(match.group(2).replace(",", ""))
                    logging.info(f"[EXP] {state['current_exp']} / {state['need_exp']}")
                    await asyncio.sleep(1)
                    await event.client.send_message(bot_username, state["event_cmd"])
                return
            elif "Berhasil memulihkan energi Kelompok Adventure" in text:
                await asyncio.sleep(2)
                await event.client.send_message(bot_username, state["event_cmd"])
                return

            elif ("Masing-masing adventure terdiri dari" in text or "Stat sudah termasuk perhitungan sisa energi" in text) and event.buttons:
                await asyncio.sleep(1)
                await event.click(0)
                return

            elif "dihadang oleh" in text:
                enemies = parse_encounter(text)
                state["encountered_enemies"].update(enemies)
                logging.info(f"[ENCOUNTER] {enemies}")

                if len(enemies) > state["max_enemy"]:
                    logging.info("[SKIP] Terlalu banyak musuh")
                    await asyncio.sleep(1)
                    await event.click(1, 0)
                    return

                if all(enemy not in state["skip_enemies"] for enemy in enemies):
                    logging.info("[FIGHT] Musuh baru ditemukan, lawan!")
                    await asyncio.sleep(1)
                    await event.click(0, 0)
                else:
                    logging.info("[SKIP] Semua musuh dalam skip list")
                    await asyncio.sleep(1)
                    await event.click(1, 0)
                return

            elif "saat energi di bawah 10%" in text and event.buttons:
                await asyncio.sleep(1)
                await update_config_from_saved(client, user_id)
                await event.client.send_message(bot_username, f"{state['event_cmd']}_restore")
                return

            elif "Apa kamu yakin ingin menggunakan" in text and event.buttons:
                await asyncio.sleep(1)
                await event.click(0)
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, state["event_cmd"])
                return

            elif "KAMU MENANG!!" in text:
                match = re.search(r'❇️ ([\d,]+) EXP Kapal', text)
                if match:
                    gained = int(match.group(1).replace(",", ""))
                    state["current_exp"] += gained
                    logging.info(f"[EXP] +{gained} → {state['current_exp']} / {state['need_exp']}")
                    if state["current_exp"] >= state["need_exp"]:
                        logging.info("[LEVEL UP] Kirim /levelupkapal_DEF")
                        await asyncio.sleep(2)
                        await event.client.send_message(bot_username, "/levelupkapal_DEF")
                await asyncio.sleep(1)
                await event.click(0)
                return
            
            elif "Apa kamu yakin ingin meningkatkan" in text and event.buttons:
                await asyncio.sleep(1)
                await event.click(0)
                await asyncio.sleep(1)
                return
            
            elif "Berhasil meningkatkan level" in text:
                logging.info("[INFO] Berhasil meningkatkan level kapal")
                await client.send_message(bot_username, "/kapal")
                await asyncio.sleep(1)

            elif "Musuh menang..." in text and event.buttons:
                logging.info("[INFO] Kamu kalah")
                await asyncio.sleep(1)
                await event.click(0)
                return
            else:
                logging.info("[INFO] Balasan tidak dikenali, kirim")
                await client.send_message(bot_username, "/kapal")
                await asyncio.sleep(1)
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
        "max_enemy": 1,
        "current_exp": 0,
        "need_exp": 9999999,
        "encountered_enemies": set()
    }

    logging.info(f"🚀 Mulai A7S untuk user {user_id}")
    try:
        await update_config_from_saved(client, user_id)
        await client.send_message(bot_username, "/kapal")
        while running_flags.get(user_id):
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        logging.warning(f"❌ A7S dibatalkan untuk user {user_id}")
        raise
    except FloodWaitError as e:
        logging.warning(f"[FLOOD] Tunggu {e.seconds} detik")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logging.error(f"[FATAL] A7S error: {e}")
    finally:
        state = user_state[user_id]
        all_enemies = state["encountered_enemies"]
        skip = set(state["skip_enemies"])
        can_fight = sorted(all_enemies - skip)

        logging.info(f"📊 Total musuh ditemui: {len(all_enemies)}")
        logging.info(f"📛 Skip enemies: {', '.join(sorted(skip))}")
        logging.info(f"⚔️ Musuh yang bisa dilawan: {', '.join(can_fight)}")

        running_flags.pop(user_id, None)
        user_state.pop(user_id, None)
        if client in handlers:
            client.remove_event_handler(handlers[client], events.NewMessage(from_users=bot_username))
            del handlers[client]
        logging.info(f"✅ A7S selesai untuk user {user_id}")
