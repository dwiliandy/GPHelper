from telethon import events
import asyncio
import re

bot_username = 'GrandPiratesBot'

# Per-user tracking
running_flags = {}     # user_id: bool
user_state = {}        # user_id: { defeated_enemies, max_enemy, adv_event }
handler_registered = False

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

        if "Kalahkan semua musuh" in text or "samurai-samurai di ShimotsukiCastle" in text:
            await get_config_from_saved(event.client, user_id)
            state["defeated_enemies"] = parse_defeated_enemies(text)
            print(f"\033[91m[DEFEATED] {state['defeated_enemies']}\033[0m")
            await asyncio.sleep(1)
            await event.click(0, 0)
            return

        if "dihadang oleh" in text or "Kamu menelusuri ShimotsukiCastle" in text:
            enemies = parse_encounter(text)
            print(f"\033[94m[ENCOUNTER] {enemies}\033[0m")

            if len(enemies) > state["max_enemy"]:
                print("\033[93m[INFO] Lawan terlalu banyak, skip\033[0m")
                await asyncio.sleep(1)
                await event.click(1, 0)
                return

            if any(enemy not in state["defeated_enemies"] for enemy in enemies):
                print("\033[92m[INFO] Musuh baru ditemukan, menunggu /adv...\033[0m")
                await state["adv_event"].wait()
                state["adv_event"].clear()
            else:
                print("\033[93m[INFO] Semua musuh sudah dikalahkan, skip\033[0m")
                await asyncio.sleep(1)
                await event.click(1, 0)
            return

        if "Energi untuk bertarung telah habis" in text:
            print("[INFO] Energi habis, kirim restore_x dan adv")
            await asyncio.sleep(1)
            await event.client.send_message(bot_username, '/restore_x')
            await asyncio.sleep(1)
            await event.client.send_message(bot_username, '/adv')
            return

    handler_registered = True


def parse_defeated_enemies(text):
    defeated = set()
    for line in text.splitlines():
        if '✅' in line:
            match = re.search(r'😈 (.+?) ✅', line)
            if match:
                defeated.add(match.group(1))
    return defeated

def parse_encounter(text):
    enemies = []
    for line in text.splitlines():
        if '😈' in line:
            match = re.search(r'😈 (.+)', line)
            if match:
                name_with_plus = match.group(1)
                name = name_with_plus.split('+')[0].strip()
                enemies.append(name)
    return enemies

async def get_config_from_saved(client, user_id):
    async for msg in client.iter_messages('me', search='max_enemy'):
        match = re.search(r'max_enemy\s*=\s*(\d+)', msg.raw_text)
        if match:
            user_state[user_id]["max_enemy"] = int(match.group(1))
            print(f'[CONFIG] Max musuh: {user_state[user_id]["max_enemy"]}')
            break

async def run_search(user_id, client):
    running_flags[user_id] = True
    user_state[user_id] = {
        "defeated_enemies": set(),
        "max_enemy": 0,
        "adv_event": asyncio.Event(),
    }

    print(f"🔍 Memulai Script Search untuk user {user_id}")
    try:
        await client.send_message(bot_username, '/adv')
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        running_flags[user_id] = False
        print(f"❌ Script Search dihentikan untuk user {user_id}")
        raise
