import asyncio
import random
import re
import logging
from telethon import events

bot_username = 'GrandPiratesBot'

# Variabel global
snail = "_"
use_grand_snail = "no"
running_flags = {}
registered_handlers = {}  # ✅ Perubahan baru

async def update_config_from_saved(client):
    global snail, use_grand_snail
    async for message in client.iter_messages('me', limit=10):
        if not message.text:
            continue
        lines = message.text.strip().splitlines()
        for line in lines:
            line = line.strip().lower()
            if line.startswith("snail"):
                match = re.search(r"snail\s*=\s*(\d+|_)", line)
                if match:
                    snail = match.group(1).strip()
            elif line.startswith("use_grand_snail"):
                match = re.search(r"use_grand_snail\s*=\s*(yes|no)", line)
                if match:
                    use_grand_snail = match.group(1)
        break

    print(f"[CONFIG] snail = {snail}")
    print(f"[CONFIG] use_grand_snail = {use_grand_snail}")

def parse_stage_hp(text):
    stage = re.search(r"Stage (\d+)", text)
    hp = re.search(r"HP musuh tersisa: ([\d,]+)", text)
    return stage.group(1) if stage else None, hp.group(1) if hp else None

def has_button(event, label):
    return any(button.text == label for row in (event.buttons or []) for button in row)

async def click_button(event, label):
    for row in event.buttons:
        for button in row:
            if button.text == label:
                await event.click(text=label)
                logging.info(f"[CLICK] {label}")
                return True
    return False

def init(client, user_id):
    # ✅ Cek apakah handler sudah didaftarkan sebelumnya
    if user_id in registered_handlers:
        return  # sudah terdaftar, hindari dobel handler

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        if not running_flags.get(user_id, False):
            return

        text = event.raw_text
        logging.info(f"[BOT] {text.splitlines()[0]}")

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
            if use_grand_snail == "yes":
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
            if "💥 GrandFleet kamu membantu serangan" in text:
                await asyncio.sleep(1)
                await click_button(event, "Attack")
            elif "Kamu tidak memiliki 🐌GrandSnail" in text:
                await asyncio.sleep(1)
                await click_button(event, "Attack")
            else:
                if use_grand_snail == "yes":
                    await asyncio.sleep(1)
                    await event.client.send_message(bot_username, "/use_GrandSnail")
                else:
                    await asyncio.sleep(1)
                    await click_button(event, "Attack")
            return

        if "Kesempatan serang telah habis" in text:
            await asyncio.sleep(1)
            await update_config_from_saved(event.client)
            if snail == "_":
                await event.client.send_message(bot_username, "/use_SeaSnail")
            else:
                await event.client.send_message(bot_username, f"/use_SeaSnail{snail}")
            return

        if "Apa kamu yakin ingin menggunakan 🐌SeaSnail" in text:
            await asyncio.sleep(1)
            await click_button(event, "Confirm")
            return

        if "Kesempatan serang NavalBattle dipulihkan" in text:
            await asyncio.sleep(1)
            await event.client.send_message(bot_username, "/nb")
            return

        if "Kamu berangkat ke area berikutnya" in text or "Kamu berangkat ke area sebelumnya" in text:
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
            logging.info("❌ Tidak punya SeaSnail, menghentikan script.")
            running_flags[user_id] = False
            return

    # ✅ Simpan handler yang sudah terdaftar agar tidak ganda
    registered_handlers[user_id] = handler


# Fungsi utama dipanggil dari main.py
async def run_nb(user_id, client):
    running_flags[user_id] = True
    await update_config_from_saved(client)
    await client.send_message(bot_username, "/nb")

    async def periodic_config_update():
        while running_flags.get(user_id, False):
            await update_config_from_saved(client)
            await asyncio.sleep(10)

    config_task = asyncio.create_task(periodic_config_update())

    try:
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        running_flags[user_id] = False
        config_task.cancel()
        logging.info(f"❌ Script NavalBattle dihentikan untuk user {user_id}")
        raise
