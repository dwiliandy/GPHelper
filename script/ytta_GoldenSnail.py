import asyncio
import random
import re
from telethon import events

bot_username = 'GrandPiratesBot'

running_flags = {}
user_state = {}  # user_id: dict
handler_registered = False

async def baca_batas_dari_saved(client, user_id):
    async for msg in client.iter_messages('me', search='batas_gs'):
        for line in msg.text.splitlines():
            match = re.search(r'batas_gs\s*=\s*(\d+)', line)
            if match:
                user_state[user_id]["batas_gs"] = int(match.group(1))
                return
        break
    user_state[user_id]["batas_gs"] = None

async def get_ship_info(text, user_id):
    match_ship = re.search(r'🛳 (.+?) - Level (\d+)', text)
    match_exp = re.search(r'EXP: ([\d,]+)/([\d,]+)', text)

    if match_ship:
        user_state[user_id]["ship_name"] = match_ship.group(1)
        user_state[user_id]["ship_level"] = int(match_ship.group(2))

    if match_exp:
        user_state[user_id]["exp_now"] = int(match_exp.group(1).replace(',', ''))
        user_state[user_id]["exp_max"] = int(match_exp.group(2).replace(',', ''))
    else:
        level = user_state[user_id]["ship_level"]
        user_state[user_id]["exp_now"] = 0
        user_state[user_id]["exp_max"] = level * 5000

async def get_golden_snail_count(text):
    match = re.search(r'GoldenSnail dimiliki: (\d+)', text)
    return int(match.group(1)) if match else 0

async def get_exp_gain(text):
    match = re.search(r'❇️ ([\d,]+) EXP Kapal', text)
    return int(match.group(1).replace(',', '')) if match else 0

def init(client):
    global handler_registered
    if handler_registered:
        return

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        user_id = event.sender_id
        if not running_flags.get(user_id, False):
            return

        text = event.raw_text
        state = user_state[user_id]

        if 'EXP:' in text and 'Level' in text:
            await get_ship_info(text, user_id)
            print(f'{state["ship_name"]} Lv.{state["ship_level"]}: {state["exp_now"]}/{state["exp_max"]}')
            await asyncio.sleep(1)
            await event.client.send_message(bot_username, '/i_GoldenSnail')

        elif 'GoldenSnail dimiliki:' in text:
            state["golden_snail"] = await get_golden_snail_count(text)
            print(f'GoldenSnail tersedia: {state["golden_snail"]}')
            await asyncio.sleep(1)
            await event.client.send_message(bot_username, '/use_GoldenSnail')

        elif 'Apa kamu yakin ingin melakukan panggilan' in text and event.buttons:
            await asyncio.sleep(1)
            await event.click(0)

        elif 'BUSTER CALL DILAKSANAKAN' in text:
            gain = await get_exp_gain(text)
            state["exp_now"] += gain
            state["golden_snail"] -= 1
            print(f'+{gain} EXP ➡️ Total: {state["exp_now"]}/{state["exp_max"]}, GS: {state["golden_snail"]}')

            if state["exp_now"] >= state["exp_max"]:
                print("[INFO] Level up dimulai")
                await asyncio.sleep(2)
                await event.client.send_message(bot_username, '/levelupKapal')
                cmd = random.choice(['/levelupkapal_ATK', '/levelupkapal_DEF', '/levelupkapal_HP'])
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, cmd)

            elif state["golden_snail"] <= 0 or (
                state["batas_gs"] is not None and state["golden_snail"] <= state["batas_gs"]
            ):
                print("[SELESAI] GoldenSnail habis / batas tercapai.")
                running_flags[user_id] = False
            else:
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, '/use_GoldenSnail')

        elif 'Apa kamu yakin ingin meningkatkan' in text and event.buttons:
            await asyncio.sleep(1)
            await event.click(0)

        elif 'Berhasil meningkatkan level' in text:
            state["ship_level"] += 1
            print(f'Level Up! {state["ship_name"]} -> Lv.{state["ship_level"]}')
            if state["golden_snail"] <= 0 or (
                state["batas_gs"] is not None and state["golden_snail"] <= state["batas_gs"]
            ):
                print("Selesai. GS habis atau mencapai batas.")
                running_flags[user_id] = False
            else:
                await asyncio.sleep(1)
                await event.client.send_message(bot_username, 'kapal')

    handler_registered = True

async def run_gs(user_id, client):
    running_flags[user_id] = True
    user_state[user_id] = {
        "exp_now": 0,
        "exp_max": 0,
        "ship_name": "",
        "ship_level": 0,
        "golden_snail": 0,
        "batas_gs": None,
    }

    print(f"🐌 Mulai GoldenSnail untuk user {user_id}")
    try:
        await baca_batas_dari_saved(client, user_id)
        await client.send_message(bot_username, "kapal")
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        print(f"❌ Script GS dibatalkan untuk user {user_id}")
        running_flags[user_id] = False
        raise
