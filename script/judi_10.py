from telethon import events, Button
import asyncio
import re
import logging

bot_username = "GrandPiratesBot"

# Per-user state
running_flags = {}
user_state = {}
handler_registered = False

def init(client):
    global handler_registered
    if handler_registered:
        return
    handler_registered = True

    @client.on(events.NewMessage(pattern=r"^\.judi10$", from_users="me"))
    async def handler_start(event):
        user_id = event.sender_id
        if running_flags.get(user_id, False):
            await event.respond("⚠️ Proses judi sedang berjalan.")
            return

        running_flags[user_id] = True
        user_state[user_id] = {
            "counter": 0,
            "total_play": 0,
            "rewards": [],
            "summary": {},
            "event": asyncio.Event(),
        }

        await event.respond("⏳ Mengambil konfigurasi dan lokasi...")
        await run_judi_10(client, event, user_id)

    @client.on(events.NewMessage(from_users=bot_username))
    async def message_handler(event):
        user_id = event.chat_id
        if not running_flags.get(user_id):
            return

        text = event.raw_text
        state = user_state[user_id]

        # Hadiah dari hasil judi
        if "💥 Kamu mendapatkan hadiah" in text:
            match = re.search(r"💥 Kamu mendapatkan hadiah (.+)", text)
            if match:
                reward = match.group(1).strip()
                state["rewards"].append(reward)
                state["summary"][reward] = state["summary"].get(reward, 0) + 1
                state["counter"] += 1
                if state["counter"] >= state["total_play"]:
                    await send_summary(event, user_id)
                    running_flags[user_id] = False
                    return
                await asyncio.sleep(2)
                await click_play_button(event, state["current_location"])
        elif "Kamu berada di area" in text:
            # Menandakan kita sudah sampai di lokasi
            state["event"].set()
        elif "Berikut adalah status petualanganmu" in text:
            # Lokasi /adv
            if "🎰 Rainbase: RainDinners" in text or 'Alabasta: Rainbase' in text:
                state["current_location"] = "rain"
                await client.send_message(bot_username, "/v_rainDinners")
            elif "🎰 VIP Area: CasinoKing" in text:
                state["current_location"] = "casino"
                await client.send_message(bot_username, "/casinoKing")
            else:
                await event.respond("❌ Lokasi tidak ditemukan. Harap berada di RainDinners atau CasinoKing.")
                running_flags[user_id] = False
                return

async def run_judi_10(client, event, user_id):
    state = user_state[user_id]

    # Ambil total_play dari Saved Messages
    total_play = await get_total_play(client)
    if total_play is None:
        await event.respond("❌ Tidak menemukan konfigurasi total_play.")
        running_flags[user_id] = False
        return

    state["total_play"] = total_play
    await client.send_message(bot_username, "/adv")

    try:
        await asyncio.wait_for(state["event"].wait(), timeout=10)
    except asyncio.TimeoutError:
        await event.respond("❌ Gagal Akses lokasi.")
        running_flags[user_id] = False
        return

    # Setelah sampai lokasi, klik tombol pertama
    await asyncio.sleep(2)
    await click_play_button(event, state["current_location"])

async def get_total_play(client):
    async for msg in client.iter_messages("me", limit=10):
        if msg.raw_text and "total_play" in msg.raw_text:
            match = re.search(r"total_play\s*=\s*(\d+)", msg.raw_text)
            if match:
                return int(match.group(1))
    return None

async def click_play_button(event, location):
    if location == "rain":
        button_filter = lambda b: "Play (-10💎)" in b.text
    elif location == "casino":
        button_filter = lambda b: "Play (-10" in b.text and "Coin" in b.text
    else:
        return

    try:
        await event.click(text=button_filter)
    except Exception as e:
        logging.error(f"Gagal klik tombol: {e}")

async def send_summary(event, user_id):
    state = user_state[user_id]
    summary_lines = [f"✅ Selesai {state['counter']} kali judi."]
    for item, count in state["summary"].items():
        summary_lines.append(f"- {item}: {count}")
    await event.respond("\n".join(summary_lines))
