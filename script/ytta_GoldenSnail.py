import asyncio
import random
import re
import time
from telethon import events

bot_username = 'GrandPiratesBot'

# Variabel global
running_flags = {}
exp_now = exp_max = ship_level = golden_snail = 0
ship_name = ""
batas_gs = None

# Ambil batas_gs dari 1 pesan di Saved Messages
async def baca_batas_dari_saved(client):
    async for msg in client.iter_messages('me', search='batas_gs'):
        lines = msg.text.splitlines()
        for line in lines:
            if 'batas_gs' in line:
                match = re.search(r'batas_gs\s*=\s*(\d+)', line)
                if match:
                    return int(match.group(1))
        break
    return None

async def get_ship_info(bot_response):
    global exp_now, exp_max, ship_name, ship_level

    exp_match = re.search(r'EXP: ([\d,]+)/([\d,]+)', bot_response)
    ship_match = re.search(r'🛳 (.+?) - Level (\d+)', bot_response)

    if not ship_match:
        return None

    ship_name = ship_match.group(1)
    ship_level = int(ship_match.group(2))
    exp_now = 0
    exp_max_expected = ship_level * 5000

    if exp_match:
        exp_now = int(exp_match.group(1).replace(',', ''))
        exp_max_real = int(exp_match.group(2).replace(',', ''))

        if exp_max_real != exp_max_expected:
            print(f"[PERINGATAN] EXP max dari bot: {exp_max_real} tidak cocok dengan {exp_max_expected} (Level x 5000)")
        exp_max = exp_max_real
    else:
        print(f"[INFO] Tidak ditemukan EXP dari bot, pakai default Level x 5000 = {exp_max_expected}")
        exp_max = exp_max_expected

    return (exp_now, exp_max, ship_name, ship_level)

async def get_golden_snail_count(bot_response):
    match = re.search(r'GoldenSnail dimiliki: (\d+)', bot_response)
    return int(match.group(1)) if match else 0

async def get_exp_gain(bot_response):
    match = re.search(r'❇️ ([\d,]+) EXP Kapal', bot_response)
    return int(match.group(1).replace(',', '')) if match else 0

# Daftarkan handler
def init(client, user_id):
    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        global exp_now, exp_max, ship_name, ship_level, golden_snail, batas_gs

        if not running_flags.get(user_id, False):
              return

        text = event.raw_text

        if 'EXP:' in text and 'Level' in text:
            info = await get_ship_info(text)
            if info:
                print(f'{ship_name} Lv.{ship_level}: {exp_now}/{exp_max}')
                time.sleep(1)
                await client.send_message(bot_username, '/i_GoldenSnail')

        elif 'GoldenSnail dimiliki:' in text:
            time.sleep(1)
            golden_snail = await get_golden_snail_count(text)
            print(f'GoldenSnail tersedia: {golden_snail}')
            time.sleep(1)
            await client.send_message(bot_username, '/use_GoldenSnail')

        elif 'Apa kamu yakin ingin melakukan panggilan' in text and event.buttons:
            time.sleep(1)
            await event.click(0)

        elif 'BUSTER CALL DILAKSANAKAN' in text:
            time.sleep(1)
            exp_gain = await get_exp_gain(text)
            exp_now += exp_gain
            golden_snail -= 1
            print(f'+{exp_gain} EXP -> Total: {exp_now}/{exp_max}, GoldenSnail tersisa: {golden_snail}')
            time.sleep(1)

            if exp_now >= exp_max:
                print("[INFO] EXP kapal mencapai maksimal. Lakukan level up.")
                time.sleep(2)
                await client.send_message(bot_username, '/levelupKapal')
                time.sleep(1)
                levelup_cmd = random.choice(['/levelupkapal_ATK', '/levelupkapal_DEF', '/levelupkapal_HP'])
                await client.send_message(bot_username, levelup_cmd)

            elif golden_snail <= 0 or (batas_gs is not None and golden_snail <= batas_gs):
                print("[INFO] GoldenSnail habis atau mencapai batas. Proses berhenti.")
                running_flags[user_id] = False
            else:
                await client.send_message(bot_username, '/use_GoldenSnail')

        elif 'Apa kamu yakin ingin meningkatkan' in text and event.buttons:
            time.sleep(1)
            await event.click(0)

        elif 'Berhasil meningkatkan level' in text:
            time.sleep(1)
            ship_level += 1
            print(f'Level Up! {ship_name} -> Lv.{ship_level}')
            if  golden_snail <= 0 or (batas_gs is not None and golden_snail <= batas_gs):
                print("Selesai. GoldenSnail habis, level maksimum tercapai, atau sudah sampai batas.")
                running_flags[user_id] = False
            else:
                time.sleep(1)
                await client.send_message(bot_username, 'kapal')

# Fungsi utama yang dipanggil dari /gs di main.py
async def run_gs(user_id, client):
    global batas_gs

    running_flags[user_id] = True
    print("Memulai Script GoldenSnail...")

    try:
        batas_gs = await baca_batas_dari_saved(client)
        if batas_gs is not None:
            print(f'Trigger diterima. Batas GoldenSnail: {batas_gs}')
        else:
            print('Trigger diterima. Tidak ada batas_gs, akan gunakan semua.')

        await client.send_message(bot_username, 'kapal')

        # ⏳ Tahan task tetap hidup selama masih aktif
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)

    except asyncio.CancelledError:
        print(f"[INFO] Script GoldenSnail dibatalkan (/q) untuk user {user_id}")
        running_flags[user_id] = False
        raise
