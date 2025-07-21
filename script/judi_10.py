from telethon import events
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
    handler_registered = True

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        user_id = event.message.peer_id.user_id
        if user_id not in running_flags or not running_flags[user_id]:
            return

        text = event.raw_text

        # Deteksi lokasi
        if "Lokasi kamu saat ini:" in text:
            location = detect_location(text)
            if location:
                user_state[user_id]["current_location"] = location
                user_state[user_id]["event"].set()
            return

        # Deteksi hadiah dari tombol Play
        if "Kamu mendapatkan hadiah" in text:
            record_reward(user_id, text)
            await process_play(client, user_id, event)
            return

    @client.on(events.NewMessage(pattern=r'^\.judi$', from_users='me'))
    async def start_judi_command(event):
        user_id = event.sender_id
        if running_flags.get(user_id):
            await event.reply("⚠️ Proses judi sedang berjalan.")
            return

        running_flags[user_id] = True
        user_state[user_id] = {
            "event": asyncio.Event(),
            "counter": 0,
            "total_play": 0,
            "rewards": {},
            "current_location": None,
        }

        await run_judi_10(client, event, user_id)

# === LOGIC ===

async def run_judi_10(client, event, user_id):
    state = user_state[user_id]
    print(f"[JUDI] ▶️ Memulai judi untuk user {user_id}")

    # Ambil total_play dari Saved Messages
    total_play = await get_total_play(client)
    print(f"[JUDI] ▶️ total_play: {total_play}")
    if total_play is None:
        await event.respond("❌ Tidak menemukan konfigurasi total_play.")
        running_flags[user_id] = False
        return
    state["total_play"] = total_play

    # Kirim /adv dan tunggu lokasi
    state["event"].clear()
    await client.send_message(bot_username, "/adv")
    try:
        await asyncio.wait_for(state["event"].wait(), timeout=10)
    except asyncio.TimeoutError:
        await event.respond("❌ Gagal menerima info lokasi dari /adv.")
        running_flags[user_id] = False
        return

    location = state["current_location"]
    if location not in ["v_rainDinners", "casinoKing"]:
        await event.respond("❌ Lokasi tidak valid. Harap berada di RainDinners atau CasinoKing.")
        running_flags[user_id] = False
        return

    # Kirim perintah lokasi jika belum benar
    if location == "v_rainDinners":
        await client.send_message(bot_username, "/v_rainDinners")
    elif location == "casinoKing":
        await client.send_message(bot_username, "/casinoKing")

    await asyncio.sleep(2)

    # Mulai klik tombol pertama
    await event.respond(f"▶️ Mulai Judi {total_play}x di {location}")
    await click_play_button(event, location)

async def process_play(client, user_id, event):
    state = user_state[user_id]
    state["counter"] += 1

    if state["counter"] >= state["total_play"]:
        # Selesai
        summary = format_rewards(state["rewards"])
        await event.respond(f"✅ Selesai Judi {state['counter']}x\n\n🎁 Total Hadiah:\n{summary}")
        running_flags[user_id] = False
        return

    await asyncio.sleep(2)
    await click_play_button(event, state["current_location"])

async def click_play_button(event, location):
    buttons = event.message.buttons
    if not buttons:
        await event.respond("❌ Tidak menemukan tombol Play.")
        return

    for row in buttons:
        for button in row:
            if location == "v_rainDinners" and "Play (-10💎)" in button.text:
                await event.click(button)
                return
            elif location == "casinoKing" and "Play (-10🪙)" in button.text:
                await event.click(button)
                return

# === UTILITIES ===

def detect_location(text):
    if "RainDinners" in text:
        return "v_rainDinners"
    elif "CasinoKing" in text:
        return "casinoKing"
    return None

def record_reward(user_id, text):
    state = user_state[user_id]
    match = re.search(r'dengan hadiah (.+)', text)
    if match:
        reward = match.group(1).strip()
        if reward not in state["rewards"]:
            state["rewards"][reward] = 0
        state["rewards"][reward] += 1

def format_rewards(rewards):
    return "\n".join([f"- {name}: {count}x" for name, count in rewards.items()])

async def get_total_play(client):
    me = await client.get_me()
    messages = client.iter_messages(me.id, limit=20)
    async for msg in messages:
        if msg.raw_text and "total_play" in msg.raw_text:
            match = re.search(r'total_play\s*=\s*(\d+)', msg.raw_text)
            if match:
                print(f"[JUDI] 🎲 Ditemukan total_play: {match.group(1)}")
                return int(match.group(1))
            
    return None
