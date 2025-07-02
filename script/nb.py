import asyncio
import random
import re
import logging
from telethon import events
from telethon.errors import FloodWaitError

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

bot_username = 'GrandPiratesBot'

running_flags = {}
user_state = {}
handler_registered = False

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
                if line.startswith("snail"):
                    match = re.search(r"snail\s*=\s*(\d+|_)", line)
                    if match:
                        state["snail"] = match.group(1)
                elif line.startswith("use_grand_snail"):
                    match = re.search(r"use_grand_snail\s*=\s*(yes|no)", line)
                    if match:
                        state["use_grand_snail"] = match.group(1)
            break
    logging.info(f"🔧 Konfigurasi diperbarui untuk user {user_id}: {state}")

def parse_stage_hp(text):
    stage = re.search(r"Stage (\d+)", text)
    hp = re.search(r"HP musuh tersisa: ([\d,]+)", text)
    return stage.group(1) if stage else None, hp.group(1) if hp else None

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
                    logging.warning(f"[CLICK ERROR] Gagal klik {label}: {e}")
    return False

async def keep_alive(client):
    while True:
        try:
            await client.get_me()
            logging.debug("[KeepAlive] Ping sukses")
        except Exception as e:
            logging.warning(f"[KeepAlive] Ping gagal: {e}")
        await asyncio.sleep(300)  # 5 menit

def init(client):
    global handler_registered
    if handler_registered:
        return

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        try:
            user = await event.client.get_me()
            user_id = user.id
            if not running_flags.get(user_id, False):
                return

            text = event.raw_text
            state = user_state[user_id]

            # Navigasi area
            if has_button(event, "Area Sebelumnya") or has_button(event, "Area Selanjutnya"):
                await asyncio.sleep(1)
                await click_button(event, random.choice(["Area Sebelumnya", "Area Selanjutnya"]))
                return

            if has_button(event, "Berangkat"):
                await asyncio.sleep(1)
                await click_button(event, "Berangkat")
                return

            if "kamu berangkat menuju" in text:
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, "/callGrandFleet")
                return

            if "Apa kamu yakin ingin memanggil GrandFleet" in text:
                await asyncio.sleep(1)
                await click_button(event, "Confirm")
                return

            if "GrandFleet telah ikut berjuang" in text:
                if state["use_grand_snail"] == "yes":
                    await asyncio.sleep(1)
                    await event.client.send_message(bot_username, "/use_GrandSnail")
                else:
                    logging.info("[SKIP] use_grand_snail = no")
                return

            if "Apa kamu yakin ingin menggunakan 🐌GrandSnail" in text:
                await asyncio.sleep(1)
                await click_button(event, "Confirm")
                return

            if "GrandFleet dipanggil untuk membantu menyerang" in text:
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, "/nb")
                return

            if "Pertempuran habis-habisan di laut lepas" in text:
                await asyncio.sleep(1)
                await click_button(event, "Attack")
                return

            if "NavalBattle: Stage" in text:
                stage, hp = parse_stage_hp(text)
                if stage and hp:
                    logging.info(f"[INFO] Stage {stage} | HP Musuh: {hp}")
                await asyncio.sleep(1)
                await click_button(event, "Attack")
                return

            if "Kamu menyerang dan berhasil memberikan" in text:
                if "💥 GrandFleet kamu membantu serangan" in text or "Kamu tidak memiliki 🐌GrandSnail" in text:
                    await asyncio.sleep(1)
                    await click_button(event, "Attack")
                else:
                    if state["use_grand_snail"] == "yes":
                        await asyncio.sleep(1)
                        await event.client.send_message(bot_username, "/use_GrandSnail")
                    else:
                        await asyncio.sleep(1)
                        await click_button(event, "Attack")
                return

            if "Kesempatan serang telah habis" in text:
                await update_config_from_saved(event.client, user_id)
                snail = state["snail"]
                await asyncio.sleep(1)
                command = "/use_SeaSnail" if snail == "_" else f"/use_SeaSnail{snail}"
                await event.client.send_message(bot_username, command)
                return

            if "Apa kamu yakin ingin menggunakan 🐌SeaSnail" in text:
                await asyncio.sleep(1)
                await click_button(event, "Confirm")
                return

            if "Kesempatan serang NavalBattle dipulihkan" in text:
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, "/nb")
                return

            if "NavalBattle hanya bisa dilakukan saat dalam perjalanan di laut" in text:
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, "Adventure")
                return

            if "Saat ini GrandFleet kamu telah hadir untuk" in text:
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, "/nb")
                return

            if "STAGE" in text and "DISELESAIKAN" in text and "Kru baru ditambahkan ke NavalShop" in text:
                stage_match = re.search(r"STAGE (\d+) DISELESAIKAN", text)
                kru_matches = re.findall(r"[👑🔎👊🔫⚔️💊] ([^\n]+)", text)
                if stage_match and kru_matches:
                    kru_list = ", ".join(kru_matches)
                    logging.info(f"[DROP] Stage {stage_match.group(1)}: {kru_list}")
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, "/nb")
                return

            if "Kamu tidak memiliki 🐌SeaSnail" in text:
                logging.info("❌ Tidak punya SeaSnail, menghentikan script dan menutup koneksi.")
                running_flags[user_id] = False
                await event.client.disconnect()
                return

        except Exception as e:
            logging.error(f"[EVENT ERROR] {e}")

    handler_registered = True
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
        await update_config_from_saved(client, user_id)
        await client.send_message(bot_username, "/nb")
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
        running_flags[user_id] = False
        logging.error(f"[FATAL] NavalBattle error: {e}")
