import asyncio
import time
from telethon import events

running_flags = {}
click_count = {}
last_click_time = {}
current_area = {}
user_state = {}
area_triggered = {}
handlers = {}

def init(client):
    pass  # Kosongkan kalau tidak dibutuhkan

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
                        return parts[1].strip()
    return "_"

async def update_config_periodically(client, user_id):
    while running_flags.get(user_id, False):
        config = await get_total_play_config(client, user_id)
        user_state[user_id]['total_play'] = config
        print(f"[CONFIG] 🔄 total_play diperbarui: {config}")
        await asyncio.sleep(60)

async def run_judi_10(user_id, client):
    click_count[user_id] = 0
    last_click_time[user_id] = time.time()
    current_area[user_id] = None
    user_state[user_id] = {}
    area_triggered[user_id] = set()
    running_flags[user_id] = True

    total_play = await get_total_play_config(client, user_id)
    user_state[user_id]['total_play'] = total_play or "_"
    print(f"[JUDI] total_play awal: {user_state[user_id]['total_play']}")

    # Handler event pesan dari GrandPiratesBot
    async def handler(event):
        if not running_flags.get(user_id):
            return

        if not hasattr(event, "message"):
            print("[JUDI] ⛔ Event tanpa message, dilewati.")
            return

        msg = event.message
        text = event.raw_text

        # Debug tombol
        if msg.buttons:
            for row in msg.buttons:
                for btn in row:
                    print(f"[JUDI] 🔘 Tombol ditemukan: {btn.text}")

        # Deteksi lokasi dari text
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
                print("[JUDI] 💎 Deteksi RainDinners, mengirim /rainDinners...")
                await asyncio.sleep(1.5)
                await client.send_message("GrandPiratesBot", "/v_rainDinners")
                await asyncio.sleep(1.5)

        # Batas klik
        total_play = user_state[user_id].get("total_play", "_")
        if total_play != "_" and click_count[user_id] >= int(total_play):
            print(f"[JUDI] ✅ total_play {total_play} tercapai.")
            return

        if not msg.buttons:
            return

        try:
            target_text = msg.buttons[1][0].text  # Baris kedua, kolom pertama
            if "Play" in target_text:
                await msg.click(1, 0)
                click_count[user_id] += 1
                now = time.time()
                elapsed = now - last_click_time[user_id]
                last_click_time[user_id] = now
                print(f"[✓] Klik #{click_count[user_id]} | Jeda {elapsed:.2f}s")
                await asyncio.sleep(1)
            else:
                print(f"[✗] Tombol (1,0) bukan tombol Play: {target_text}")
        except IndexError:
            print("[✗] Tombol (1,0) tidak tersedia.")
        except Exception as e:
            print(f"[✗] Gagal klik tombol: {e}")

    # ✅ Pasang handler sebelum kirim /adv
    event_filter = events.NewMessage(from_users="GrandPiratesBot")
    client.add_event_handler(handler, event_filter)
    handlers[user_id] = (handler, event_filter)

    # 🚀 Kirim /adv setelah pasang handler
    await asyncio.sleep(1.5)
    await client.send_message("GrandPiratesBot", "/adv")
    await asyncio.sleep(1.5)

    # ⏳ Update config jalan terus
    config_task = asyncio.create_task(update_config_periodically(client, user_id))

    try:
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
    finally:
        # 🧹 Bersihkan handler dan task
        if user_id in handlers:
            handler_func, filter_ = handlers.pop(user_id)
            client.remove_event_handler(handler_func, filter_)
        config_task.cancel()
        running_flags.pop(user_id, None)
        print(f"[JUDI] 🛑 Selesai & handler dibersihkan untuk user {user_id}")
