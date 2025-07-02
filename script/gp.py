import asyncio
import re
import random
import logging
from telethon import events

bot_username = 'GrandPiratesBot'

# Global tracking
handler_registered = False
running_flags = {}     # user_id: bool
user_state = {}        # user_id: dict
cek_kapal_event = asyncio.Event()

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

        if not cek_kapal_event.is_set():
            print("🔄 Menunggu cekKapal selesai...")
            await cek_kapal_event.wait()

        state = user_state[user_id]
        text = event.raw_text

        if state["buff"] <= 0:
            print(f"🔥 Buff habis, menggunakan item {state['buff_item']}")
            await event.client.send_message(bot_username, state['buff_item'])
            state["buff"] = state["buff_max"]
            await asyncio.sleep(1)
            await event.client.send_message(bot_username, "/adv")
            return

        if 'Kamu menelusuri' in text:
            await asyncio.sleep(1)
            await event.click(0)
            return

        if 'KAMU MENANG!!' in text:
            state["buff"] -= 1
            print(f"💢 Buff tersisa: {state['buff']}")
            match = re.search(r'❇️ (\d[\d,]*) EXP Kapal\*\*', text)
            if match:
                exp = int(match.group(1).replace(',', ''))
                state["exp_now"] += exp
                print(f"🚢 EXP +{exp} ➡️ Total: {state['exp_now']}/{state['exp_max']}")
                if state["exp_now"] >= state["exp_max"]:
                    print("🚨 EXP cukup untuk level up. Memanggil cekKapal()")
                    await cekKapal(event.client, user_id)
            await asyncio.sleep(1)
            await event.click(0)
            return

        if 'Musuh menang' in text or 'Energi untuk bertarung telah habis' in text:
            state["buff"] -= 1
            print("🔄 Energi habis, restore + adv")
            await event.client.send_message(bot_username, "/restore_x")
            await asyncio.sleep(1)
            await event.client.send_message(bot_username, "/adv")
            return

        await asyncio.sleep(1)
        await event.client.send_message(bot_username, "/adv")
        print("📨 Kirim ulang /adv")
        return

    handler_registered = True


async def cekKapal(client, user_id):
    state = user_state[user_id]
    cek_kapal_event.clear()

    await client.send_message(bot_username, "/kapal")
    await asyncio.sleep(2)

    async for msg in client.iter_messages(bot_username, limit=1):
        text = msg.text

        if "EXP: (MAX)" in text:
            print("🚨 EXP Kapal MAX - Naik Level")
            cmd = random.choice(['/levelupkapal_ATK', '/levelupkapal_DEF', '/levelupkapal_HP'])
            await client.send_message(bot_username, cmd)
            for _ in range(10):
                async for m in client.iter_messages(bot_username, limit=1):
                    if m.buttons:
                        await m.click(0)
                        await asyncio.sleep(2)
                        await cekKapal(client, user_id)
                        return
                await asyncio.sleep(0.5)
        else:
            match = re.search(r'EXP: \*\*\(([\d,]+)/([\d,]+)\)\*\*', text)
            if match:
                state["exp_now"] = int(match.group(1).replace(',', ''))
                state["exp_max"] = int(match.group(2).replace(',', ''))
                print(f"🚢 EXP Kapal: {state['exp_now']}/{state['exp_max']}")

    cek_kapal_event.set()


async def run_attack(user_id, client):
    running_flags[user_id] = True
    user_state[user_id] = {
        "buff": 25,
        "buff_max": 25,
        "buff_item": "use_Yubashiri_10",
        "exp_now": 0,
        "exp_max": 0
    }

    print(f"⚔️ Memulai Script Attack untuk user {user_id}")
    try:
        await cekKapal(client, user_id)
        await client.send_message(bot_username, "/adv")
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)    
            if asyncio.current_task().cancelled():
              break
    except asyncio.CancelledError:
        print(f"❌ Script Attack dihentikan untuk user {user_id}")
        running_flags[user_id] = False
        raise

    finally:
        running_flags[user_id] = False
        logging.info(f"✅ Auto Grinding selesai untuk user {user_id}")