import asyncio
import re
from telethon import events

running_flags = {}
click_count = {}
handlers = {}
current_area = {}
area_triggered = {}
reward_totals = {}

def init(client):
    pass

async def get_total_play_config(client, user_id):
    async for msg in client.iter_messages('me', limit=10):
        if not msg.text:
            continue
        lines = msg.text.strip().splitlines()
        if lines and lines[0].strip().startswith("===GRANDPIRATES CONFIGURATION==="):
            for line in lines[1:]:
                if 'total_play' in line.lower():
                    parts = line.split('=')
                    if len(parts) == 2:
                        return int(parts[1].strip())
    return None

async def run_judi_10(user_id, client, event):
    click_count[user_id] = 0
    running_flags[user_id] = True
    current_area[user_id] = None
    area_triggered[user_id] = set()
    reward_totals[user_id] = {}

    total_play = await get_total_play_config(client, user_id)
    if total_play is None:
        await event.respond("❌ Konfigurasi `total_play` tidak ditemukan.")
        return

    print(f"[JUDI] ▶️ total_play: {total_play}")

    async def handler(msg_event):
        if not running_flags.get(user_id):
            return
        if not hasattr(msg_event, "message"):
            return

        msg = msg_event.message
        text = msg_event.raw_text

        # Deteksi lokasi
        if "viparea: casinoking" in text.lower():
            current_area[user_id] = "casino"
            if "casino" not in area_triggered[user_id]:
                area_triggered[user_id].add("casino")
                print("[JUDI] 🎲 Deteksi CasinoKing, mengirim /casinoKing...")
                await asyncio.sleep(1.5)
                await client.send_message("GrandPiratesBot", "/casinoKing")
                await asyncio.sleep(1.5)

        elif "alabasta: rainbase" in text.lower():
            current_area[user_id] = "rain"
            if "rain" not in area_triggered[user_id]:
                area_triggered[user_id].add("rain")
                print("[JUDI] 💎 Deteksi RainDinners, mengirim /v_rainDinners...")
                await asyncio.sleep(1.5)
                await client.send_message("GrandPiratesBot", "/v_rainDinners")
                await asyncio.sleep(1.5)

        # Deteksi hadiah
        hadiah_match = re.search(r"Kamu memenangkan Hadiah(?: Utama)? (.+?) \((\d+)X\)", text)
        last_reward = None
        if hadiah_match:
            item = hadiah_match.group(1).strip()
            multiplier = int(hadiah_match.group(2))
            reward_totals[user_id][item] = reward_totals[user_id].get(item, 0) + multiplier
            last_reward = f"{item} x{multiplier}"

        # Klik tombol
        if msg.buttons:
            try:
                btn_text = msg.buttons[1][0].text
                if "Play" in btn_text:
                    if click_count[user_id] >= total_play:
                        print(f"[⛔] Batas total_play ({total_play}) tercapai, tidak klik lagi.")
                        return

                    await asyncio.sleep(1)
                    await msg.click(1, 0)
                    click_count[user_id] += 1

                    if last_reward:
                        print(f"[✓] Klik #{click_count[user_id]} | Hadiah: {last_reward}")
                    else:
                        print(f"[✓] Klik #{click_count[user_id]}")

                    await asyncio.sleep(1)

                    if click_count[user_id] >= total_play:
                        print(f"[⛔] Batas total_play ({total_play}) tercapai, tidak klik lagi.")
                        running_flags[user_id] = False
                else:
                    print(f"[✗] Tombol (1,0) bukan Play: {btn_text}")
            except IndexError:
                print("[✗] Tombol (1,0) tidak tersedia.")
            except Exception as e:
                print(f"[✗] Gagal klik tombol: {e}")

    # Pasang handler
    event_filter = events.NewMessage(from_users="GrandPiratesBot")
    client.add_event_handler(handler, event_filter)
    handlers[user_id] = (handler, event_filter)

    # Kirim trigger awal
    await asyncio.sleep(1)
    await client.send_message("GrandPiratesBot", "/adv")
    await asyncio.sleep(1)

    try:
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
    finally:
        # Bersihkan handler
        if user_id in handlers:
            handler_func, filter_ = handlers.pop(user_id)
            client.remove_event_handler(handler_func, filter_)
        running_flags.pop(user_id, None)

        # Kirim ringkasan hadiah
        if reward_totals.get(user_id):
            summary = f"🎁 Total Hadiah yang Kamu Dapatkan setelah {click_count[user_id]} kali percobaan:\n"
            total_summary = {}
            emoji_map = {}

            for item, count in reward_totals[user_id].items():
                summary += f"- {item} : {count}\n"

                match = re.match(r"([^\w\s])?\s?(.+?)\s(\d[\d,]*)x", item)
                if match:
                    emoji = match.group(1) or ""
                    item_name = match.group(2).strip()
                    per_unit = int(match.group(3).replace(",", ""))
                    total_summary[item_name] = total_summary.get(item_name, 0) + (per_unit * count)
                    if item_name not in emoji_map:
                        emoji_map[item_name] = emoji

            summary += "\n===Total===\n"
            for name, total in total_summary.items():
                emoji = emoji_map.get(name, "")
                summary += f"- {emoji} {name} : {total:,}\n"

            await event.respond(summary.strip())

        print(f"[JUDI] 🛑 Selesai untuk user {user_id}")
