import asyncio
import time

# Penampung state per user
running_flags = {}
click_count = {}
last_click_time = {}
current_area = {}
user_state = {}

def init(client):
    pass  # Disediakan untuk konsistensi antar script

async def get_total_play_config(client, user_id):
    """Ambil konfigurasi total_play dari Saved Messages"""
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
    """Update config tiap 60 detik"""
    while running_flags.get(user_id, False):
        config = await get_total_play_config(client, user_id)
        user_state[user_id]['total_play'] = config
        print(f"[CONFIG] 🔄 total_play diperbarui: {config}")
        await asyncio.sleep(60)

async def run_judi_10(user_id, client):
    """Fungsi utama untuk menjalankan fitur judi -10"""
    click_count[user_id] = 0
    last_click_time[user_id] = time.time()
    current_area[user_id] = None
    user_state[user_id] = {}
    running_flags[user_id] = True

    # Ambil konfigurasi awal
    total_play = await get_total_play_config(client, user_id)
    user_state[user_id]['total_play'] = total_play or "_"
    print(f"[JUDI] total_play awal: {user_state[user_id]['total_play']}")

    # Jalankan updater config
    config_task = asyncio.create_task(update_config_periodically(client, user_id))

    # Handler respon dari bot
    async def handler(event):
        if not running_flags.get(user_id):
            return

        msg = event.message
        text = event.raw_text

        # Deteksi area
        if "VIPArea: CasinoKing" in text:
            current_area[user_id] = "casino"
            print("[JUDI] 🎲 Masuk area CasinoKing")
        elif "Rainbase: RainDinners" in text:
            current_area[user_id] = "rain"
            print("[JUDI] 💎 Masuk area RainDinners")

        # Cek batas main
        total_play = user_state[user_id].get("total_play", "_")
        if total_play != "_" and click_count[user_id] >= int(total_play):
            print(f"[JUDI] ✅ total_play {total_play} tercapai.")
            return

        # Pastikan ada tombol sebelum klik
        if not msg.buttons:
            return

        try:
            await msg.click(1, 0)
            click_count[user_id] += 1
            now = time.time()
            elapsed = now - last_click_time[user_id]
            last_click_time[user_id] = now
            print(f"[✓] Klik #{click_count[user_id]} | Jeda {elapsed:.2f}s")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[✗] Gagal klik tombol: {e}")

    # Daftarkan handler
    client.add_event_handler(handler)

    try:
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
    finally:
        # Cleanup
        client.remove_event_handler(handler)
        config_task.cancel()
        running_flags.pop(user_id, None)
        print(f"[JUDI] 🛑 Selesai & handler dibersihkan untuk user {user_id}")
