# scripts/judi10.py

from telethon import events
import asyncio
import logging

bot_username = 'GrandPiratesBot'

# Tracking per user
running_flags = {}     # user_id: bool
user_state = {}        # user_id: { total_play, counter, total_reward, reward_log }
handler_registered = False


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
                        try:
                            total_play = int(parts[1].strip())
                            print(f"[CONFIG] total_play ditemukan: {total_play}")
                            return total_play
                        except ValueError:
                            print("[CONFIG] ❌ Format total_play tidak valid.")
                            return None
    print("[CONFIG] ❌ Tidak menemukan konfigurasi total_play di Saved Messages.")
    return None

async def detect_location_and_send_command(client):
    async for msg in client.iter_messages("GrandPiratesBot", limit=10):
        if not msg.raw_text:
            continue

        text = msg.raw_text.lower()

        if "viparea: casinoking" in text:
            print("[JUDI] 🎲 Deteksi lokasi: CasinoKing, mengirim /casinoKing...")
            await asyncio.sleep(1.5)
            await client.send_message("GrandPiratesBot", "/casinoKing")
            return True

        elif "alabasta: rainbase" in text:
            print("[JUDI] 💎 Deteksi lokasi: RainDinners, mengirim /v_rainDinners...")
            await asyncio.sleep(1.5)
            await client.send_message("GrandPiratesBot", "/v_rainDinners")
            return True

    print("❌ Lokasi tidak dikenali! Silakan pergi ke VIPArea: CasinoKing atau Rainbase di Alabasta dulu.")
    return False


def init(client):
    global handler_registered
    if handler_registered:
        return

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        user = await event.client.get_me()
        user_id = user.id
        if not running_flags.get(user_id, False):
            return

        state = user_state[user_id]
        text = event.raw_text

        # TODO: logika deteksi pesan hadiah
        # TODO: logika klik tombol Play jika ada

    handler_registered = True


async def run_judi_10(user_id, client, event=None):
    running_flags[user_id] = True

    total_play = await get_total_play_config(client, user_id)
    if total_play is None:
        print("❌ Tidak bisa menjalankan script tanpa konfigurasi total_play.")
        running_flags[user_id] = False
        return

    # Kirim /adv untuk dapatkan pesan lokasi
    await client.send_message(bot_username, "/adv")
    await asyncio.sleep(2.5)  # Tunggu bot balas lokasi

    # Deteksi lokasi dari pesan /adv
    location_ready = await detect_location_and_send_command(client)
    if not location_ready:
        running_flags[user_id] = False
        return

    user_state[user_id] = {
        "total_play": total_play,
        "counter": 0,
        "total_reward": 0,
        "reward_log": [],
    }

    print(f"▶️ Memulai script auto Judi 10 untuk user {user_id} sebanyak {total_play}x")

    try:
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
            if asyncio.current_task().cancelled():
                break
    except asyncio.CancelledError:
        print(f"❌ Script dibatalkan untuk user {user_id}")
        raise
    finally:
        running_flags[user_id] = False
        logging.info(f"✅ Script selesai untuk user {user_id}")
