import asyncio
from telethon import events

running_flags = {}
click_count = {}
handlers = {}

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

async def run_judi_10(user_id, client):
    click_count[user_id] = 0
    running_flags[user_id] = True

    total_play = await get_total_play_config(client, user_id)
    if total_play is None:
        print("[CONFIG] ❌ total_play tidak ditemukan.")
        return

    print(f"[JUDI] ▶️ total_play: {total_play}")

    async def handler(event):
        if not running_flags.get(user_id):
            return
        if not hasattr(event, "message"):
            return

        msg = event.message
        text = event.raw_text

        # Jika sudah mencapai batas
        if click_count[user_id] >= total_play:
            print(f"[JUDI] ✅ total_play tercapai: {click_count[user_id]}")
            return

        if ("Rainbase: RainDinners" in text or "VIPArea: CasinoKing" in text) and msg.buttons:
            try:
                target_text = msg.buttons[1][0].text
                if "Play" in target_text:
                    await asyncio.sleep(1)
                    await msg.click(1, 0)
                    click_count[user_id] += 1
                    print(f"[✓] Klik #{click_count[user_id]}")
                    await asyncio.sleep(1)
                else:
                    print(f"[✗] Tombol (1,0) bukan Play: {target_text}")
            except IndexError:
                print("[✗] Tombol (1,0) tidak ditemukan.")
            except Exception as e:
                print(f"[✗] Gagal klik tombol: {e}")

    # Pasang handler sebelum /adv
    event_filter = events.NewMessage(from_users="GrandPiratesBot")
    client.add_event_handler(handler, event_filter)
    handlers[user_id] = (handler, event_filter)

    # Kirim /adv awal
    await asyncio.sleep(1)
    await client.send_message("GrandPiratesBot", "/adv")
    await asyncio.sleep(1)

    try:
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
    finally:
        if user_id in handlers:
            handler_func, filter_ = handlers.pop(user_id)
            client.remove_event_handler(handler_func, filter_)
        running_flags.pop(user_id, None)
        print(f"[JUDI] 🛑 Selesai untuk user {user_id}")
