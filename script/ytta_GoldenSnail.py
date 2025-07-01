import asyncio
import random
import re
from telethon import events

bot_username = 'GrandPiratesBot'

running_flags = {}
registered_handlers = {}
user_state = {}  # ✅ Simpan data per user

# Ambil batas_gs dari Saved Messages
async def baca_batas_dari_saved(client):
    async for msg in client.iter_messages('me', search='batas_gs'):
        lines = msg.text.splitlines()
        for line in lines:
            match = re.search(r'batas_gs\s*=\s*(\d+)', line)
            if match:
                return int(match.group(1))
        break
    return None

async def get_ship_info(bot_response, user_id):
    match_exp = re.search(r'EXP: ([\d,]+)/([\d,]+)', bot_response)
    match_ship = re.search(r'🛳 (.+?) - Level (\d+)', bot_response)

    if not match_ship:
        return

    ship_name = match_ship.group(1)
    ship_level = int(match_ship.group(2))
    exp_now = 0
    exp_expected = ship_level * 5000

    if match_exp:
        exp_now = int(match_exp.group(1).replace(',', ''))
        exp_max = int(match_exp.group(2).replace(',', ''))
    else:
        exp_max = exp_expected

    user_state[user_id].update({
        "ship_name": ship_name,
        "ship_level": ship_level,
        "exp_now": exp_now,
        "exp_max": exp_max,
    })

async def get_golden_snail_count(text):
    match = re.search(r'GoldenSnail dimiliki: (\d+)', text)
    return int(match.group(1)) if match else 0

async def get_exp_gain(text):
    match = re.search(r'❇️ ([\d,]+) EXP Kapal', text)
    return int(match.group(1).replace(',', '')) if match else 0

def init(client, user_id):
    if user_id in registered_handlers:
        return

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        if not running_flags.get(user_id, False):
            return

        text = event.raw_text
        state = user_state[user_id]

        if 'EXP:' in text and 'Level' in text:
            await get_ship_info(text, user_id)
            s = user_state[user_id]
            print(f"{s['ship_name']} Lv.{s['ship_level']}: {s['exp_now']}/{s['exp_max']}")
            await asyncio.sleep(1)
            await client.send_message(bot_username, '/i_GoldenSnail')

        elif 'GoldenSnail dimiliki:' in text:
            await asyncio.sleep(1)
            gs = await get_golden_snail_count(text)
            state["golden_snail"] = gs
            print(f"GoldenSnail tersedia: {gs}")
            await asyncio.sleep(1)
            await client.send_message(bot_username, '/use_GoldenSnail')

        elif 'Apa kamu yakin ingin melakukan panggilan' in text and event.buttons:
            await asyncio.sleep(1)
            await event.click(0)

        elif 'BUSTER CALL DILAKSANAKAN' in text:
            await asyncio.sleep(1)
            gain = await get_exp_gain(text)
            state["exp_now"] += gain
            state["golden_snail"] -= 1

            print(f'+{gain} EXP -> Total: {state["exp_now"]}/{state["exp_max"]}, GoldenSnail: {state["golden_snail"]}')
            await asyncio.sleep(1)

            if state["exp_now"] >= state["exp_max"]:
                print("[INFO] EXP maksimal, lakukan level up")
                await asyncio.sleep(2)
                await client.send_message(bot_username, '/levelupKapal')
                await asyncio.sleep(1)
                cmd = random.choice(['/levelupkapal_ATK', '/levelupkapal_DEF', '/levelupkapal_HP'])
                await client.send_message(bot_username, cmd)

            elif state["golden_snail"] <= 0 or (state["batas_gs"] is not None and state["golden_snail"] <= state["batas_gs"]):
                print("[INFO] GoldenSnail habis / sudah di bawah batas, script dihentikan.")
                running_flags[user_id] = False
            else:
                await client.send_message(bot_username, '/use_GoldenSnail')

        elif 'Apa kamu yakin ingin meningkatkan' in text and event.buttons:
            await asyncio.sleep(1)
            await event.click(0)

        elif 'Berhasil meningkatkan level' in text:
            await asyncio.sleep(1)
            state["ship_level"] += 1
            print(f"Level Up! {state['ship_name']} -> Lv.{state['ship_level']}")
            if state["golden_snail"] <= 0 or (state["batas_gs"] is not None and state["golden_snail"] <= state["batas_gs"]):
                print("Selesai. GS habis atau sudah sampai batas.")
                running_flags[user_id] = False
            else:
                await asyncio.sleep(1)
                await client.send_message(bot_username, 'kapal')

    registered_handlers[user_id] = handler

async def run_gs(user_id, client):
    running_flags[user_id] = True
    user_state[user_id] = {
        "ship_name": "",
        "ship_level": 0,
        "exp_now": 0,
        "exp_max": 0,
        "golden_snail": 0,
        "batas_gs": None,
    }

    print("🚀 Memulai Script GoldenSnail...")
    try:
        batas = await baca_batas_dari_saved(client)
        user_state[user_id]["batas_gs"] = batas

        if batas is not None:
            print(f"✅ Batas GS: {batas}")
        else:
            print("✅ Tidak ada batas GS. Akan gunakan semuanya.")

        await client.send_message(bot_username, 'kapal')

        while running_flags.get(user_id, False):
            await asyncio.sleep(2)

    except asyncio.CancelledError:
        print(f"❌ Script GoldenSnail dibatalkan untuk user {user_id}")
        running_flags[user_id] = False
        raise
