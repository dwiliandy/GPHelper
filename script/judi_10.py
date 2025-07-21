from telethon import events, Button
import asyncio
import re
import logging

bot_username = 'GrandPiratesBot'

running_flags = {}
user_state = {}
handler_registered = False

def init(client):
    global handler_registered
    if handler_registered:
        return

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        user_id = event.chat_id

        if not running_flags.get(user_id, False):
            return

        text = event.raw_text

        # Deteksi lokasi
        if "🎰" in text and "RainDinners" in text:
            user_state[user_id]["location"] = "RainDinners"
            user_state[user_id]["play_label"] = "Play (-10💎)"
            user_state[user_id]["found_location"].set()

        elif "🎰" in text and "CasinoKing" in text:
            user_state[user_id]["location"] = "CasinoKing"
            user_state[user_id]["play_label"] = "Play (-10🪙)"
            user_state[user_id]["found_location"].set()

        # Deteksi hasil putaran
        elif "Kamu memutar slot dan hasilnya adalah..." in text:
            await parse_reward(user_id, text)

            # Tambahkan counter
            user_state[user_id]["counter"] += 1

            # Check jika selesai
            if user_state[user_id]["counter"] >= user_state[user_id]["total_play"]:
                running_flags[user_id] = False
                await send_summary(event, user_id)
                return

            # Klik tombol lagi
            await click_play_button(event, user_id)

    handler_registered = True

async def run_judi_10(user_id, client, event):
    # Init state
    running_flags[user_id] = True
    user_state[user_id] = {
        "counter": 0,
        "total_play": 0,
        "location": None,
        "play_label": None,
        "found_location": asyncio.Event(),
        "rewards": {}
    }

    # Ambil konfigurasi total_play
    try:
        async for msg in client.iter_messages("me", limit=10):
            if "total_play" in msg.text:
                match = re.search(r"total_play\s*=\s*(\d+)", msg.text)
                if match:
                    user_state[user_id]["total_play"] = int(match.group(1))
                    break
        else:
            await event.respond("❌ Konfigurasi 'total_play' tidak ditemukan.")
            running_flags[user_id] = False
            return
    except Exception as e:
        await event.respond(f"❌ Gagal membaca konfigurasi: {e}")
        running_flags[user_id] = False
        return

    # Kirim /adv untuk deteksi lokasi
    await client.send_message(bot_username, "/adv")

    try:
        await asyncio.wait_for(user_state[user_id]["found_location"].wait(), timeout=10)
    except asyncio.TimeoutError:
        await event.respond("❌ Lokasi tidak ditemukan. Harap berada di RainDinners atau CasinoKing.")
        running_flags[user_id] = False
        return

    await event.respond(f"📍 Lokasi ditemukan: {user_state[user_id]['location']}")
    await event.respond(f"▶️ Memulai judi sebanyak {user_state[user_id]['total_play']} kali...")

    # Mulai klik tombol pertama
    await client.send_message(bot_username, "/adv")  # trigger pertama
    # selanjutnya akan diklik otomatis dari handler

async def click_play_button(event, user_id):
    btn_label = user_state[user_id]["play_label"]
    try:
        buttons = await event.get_buttons()
        for row in buttons:
            for btn in row:
                if btn.text == btn_label:
                    await event.click(button=btn)
                    return
        logging.warning(f"[{user_id}] ❌ Tombol '{btn_label}' tidak ditemukan.")
    except Exception as e:
        logging.error(f"[{user_id}] ❌ Gagal klik tombol: {e}")

async def parse_reward(user_id, text):
    match = re.search(r"Kamu memenangkan Hadiah (.+?) \(\d+X\)", text)
    if match:
        reward = match.group(1).strip()
        user_state[user_id]["rewards"].setdefault(reward, 0)
        user_state[user_id]["rewards"][reward] += 1
        print(f"[{user_id}] 🎁 Hadiah: {reward}")
    else:
        print(f"[{user_id}] ❌ Gagal parse hadiah dari:\n{text}")

async def send_summary(event, user_id):
    rewards = user_state[user_id]["rewards"]
    total = sum(rewards.values())
    lines = [f"🎉 **Judi Selesai! ({total} putaran)**", ""]
    for item, count in rewards.items():
        lines.append(f"• {item} x{count}")
    await event.respond("\n".join(lines))
