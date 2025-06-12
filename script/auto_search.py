from telethon import events
import asyncio
import re
import random

max_enemy_count = 0
defeated_enemies = set()
running_flags = {}
bot_username = 'GrandPiratesBot'
adv_event = asyncio.Event()

# Ambil setting dari Saved Messages
async def get_config_from_saved(client):
    global max_enemy_count
    async for msg in client.iter_messages('me', search='max_enemy'):
        match = re.search(r'max_enemy\s*=\s*(\d+)', msg.raw_text)
        if match:
            max_enemy_count = int(match.group(1))
            print(f'[CONFIG] Max musuh: {max_enemy_count}')
            break

# Kirim /adv
async def send_adv(client):
    await client.send_message(bot_username, '/adv')

# Cek musuh yang sudah ✅
def parse_defeated_enemies(text):
    global defeated_enemies
    defeated_enemies.clear()
    lines = text.splitlines()
    for line in lines:
        if '✅' in line:
            match = re.search(r'😈 (.+?) ✅', line)
            if match:
                defeated_enemies.add(match.group(1))
    print(f'\033[91m[DEFEATED] {defeated_enemies}\033[0m')


# Cek musuh di encounter
def parse_encounter(text):
    lines = text.splitlines()
    enemies = []
    for line in lines:
        if '😈' in line:
            match = re.search(r'😈 (.+)', line)
            if match:
                enemies.append(match.group(1))
    return enemies


def init(client,user_id):
    """Mendaftarkan event handler ke user_client"""
    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
      if not running_flags.get(user_id, False):
              return
        
      text = event.raw_text

      # Jika pesan mengandung daftar ✅ musuh yang sudah dilawan
      if 'Kalahkan semua musuh yang ada di sini masing-masing minimal 5x untuk bisa lanjut ke area berikutnya.'in text:
          await get_config_from_saved(client)
          parse_defeated_enemies(text)
          await asyncio.sleep(1)
          await event.click(0, 0)  
          return

      # Jika muncul encounter dengan musuh
      if 'dihadang oleh' in text:
          enemies = parse_encounter(text)
          print(f'\033[94m[ENCOUNTER] {enemies}\033[0m')
          if len(enemies) > max_enemy_count:
              print("\033[93m[INFO] Lawan terlalu banyak\033[0m")
              await asyncio.sleep(1)
              await event.click(1, 0)  # Skip
              return

          new_enemy_found = any(enemy not in defeated_enemies for enemy in enemies)
          if new_enemy_found:
              print("\033[92m[INFO] Musuh ditemukan, menunggu /adv dari user...\033[0m")
              await adv_event.wait()  
              adv_event.clear()       
          else:
              print("\033[93m[INFO] Semua musuh sudah dikalahkan, skip\033[0m")
              await asyncio.sleep(1)
              await event.click(1, 0)  

      if 'Energi untuk bertarung telah habis' in text:
          print("[INFO] Energi habis,kirim restore_x")
          await asyncio.sleep(1)
          await client.send_message(bot_username, '/restore_x')
          await asyncio.sleep(1)
          await client.send_message(bot_username, '/adv')
          await asyncio.sleep(1)
          return


async def run_search(user_id, client):
    running_flags[user_id] = True
    print("🔍 Memulai Script Search...")
    print(f"""Petunjuk Penggunaan: \n
          1. Pastikan sudah di adventure paling jauh.\n
          2. Kirim /adv ke bot untuk memulai script ini.\n
          3. Setelah Musuh ketemu silahkan lakukan apapun.\n
          4. Setelah selesai, kirim /adv lagi untuk melanjutkan.\n
          5. Gunakan perintah /q untuk menghentikan script ini.""")
    try:
        await client.start()
        await send_adv(client)
        print("[READY] Script berjalan...")
        while True:
            await asyncio.sleep(2)  # delay agar tidak terlalu cepat
    except asyncio.CancelledError:
        
        print(f"❌ Script Search dihentikan untuk user {user_id}.")
        running_flags[user_id] = False
        raise  # ⬅️ ini penting untuk benar-benar menghentikan task