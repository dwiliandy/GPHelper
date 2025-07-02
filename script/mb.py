# === marinebase.py ===

import asyncio
import logging
import re
from telethon import events
from telethon.errors import FloodWaitError

bot_username = 'GrandPiratesBot'

running_flags = {}
user_state = {}
locks = {}  # Lock per user untuk mencegah overlap

priority_mission = ['SSS', 'SS', 'S', 'A', 'B', 'C', 'D', 'E']
priority_role = ['Fighter', 'Navigator', 'Doctor', 'Shooter', 'All Role', 'Captain']

def init(client):
    if getattr(client, '_marinebase_handler_registered', False):
        return

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        try:
            user = await event.client.get_me()
            user_id = user.id
            if not running_flags.get(user_id, False):
                return

            state = user_state[user_id]
            text = event.raw_text

            if 'maksimal 50 misi aktif' in text:
                logging.warning("❌ Misi penuh, kirim /mb_removeall dan matikan bot.")
                await asyncio.sleep(2)
                await client.send_message(bot_username, '/mb_removeall')
                await asyncio.sleep(4)
                await client.disconnect()
                return

            if state['current_phase'] == 'start' and "marineBase_Misi" in text:
                await process_mission_classes(event, client, state)

            elif state['current_phase'] == 'detail' and re.search(fr'MarineBase: Misi Kelas {state["current_class"]}\b', text):
                await extract_mission_ids(event, client, state)

            elif state['current_phase'] == 'add' and state['waiting_for_add_response']:
                if 'Berhasil menambahkan kru ke Misi Kelas' in text:
                    logging.info("✅ Respon berhasil menambahkan kru")
                    state['add_response_ready'].set()

                if 'Kru-kru dikeluarkan' in text:
                    logging.info("✅ Kru dikeluarkan, lanjut")
                    state['removal_confirmed'].set()

                if event.buttons:
                    for row in event.buttons:
                        for button in row:
                            if 'Mulai Misi' in button.text:
                                logging.info("▶️ Tekan tombol 'Mulai Misi'")
                                await asyncio.sleep(2)
                                await event.click(0, 0)
                                await asyncio.sleep(3)
                                state['removal_confirmed'].set()

            if 'Belum ada kru yang dipilih' in text:
                logging.info("ℹ️ Tidak ada kru, lanjut ke kelas berikutnya.")
                await add_next_mission(client, state)

        except Exception as e:
            logging.error(f"[MarineBase ERROR] {e}")

    client._marinebase_handler_registered = True
    logging.info("[INIT] Handler MarineBase berhasil didaftarkan")

async def process_mission_classes(event, client, state):
    lines = event.raw_text.splitlines()
    state['class_commands'] = []

    for line in lines:
        match = re.match(r'🗒 (/marineBase_Misi_([A-Z]+))', line)
        if match:
            state['class_commands'].append((match.group(2), match.group(1)))

    state['class_commands'].sort(key=lambda x: priority_mission.index(x[0]))
    state['current_phase'] = 'detail'
    await call_next_class(client, state)

async def call_next_class(client, state):
    if not state['class_commands']:
        logging.info("✅ Semua kelas selesai.")
        running_flags[state['user_id']] = False
        return

    state['current_class'], cmd = state['class_commands'].pop(0)
    state['current_phase'] = 'detail'
    logging.info(f"➡️ Memproses kelas: {state['current_class']} | Cmd: {cmd}")
    await asyncio.sleep(4)
    await client.send_message(bot_username, cmd)

async def extract_mission_ids(event, client, state):
    state['mission_ids'] = []

    for line in event.raw_text.splitlines():
        if re.search(r'\d{2}:\d{2}:\d{2} ⏳', line):
            continue

        match = re.match(r'🗒 (/marineBase_Misi_\w+_(\d+)) --- (.+)', line)
        if match:
            role = match.group(3).strip()
            index = priority_role.index(role) if role in priority_role else 999
            state['mission_ids'].append((index, match.group(1)))

    state['mission_ids'].sort()
    state['current_phase'] = 'add'
    await add_next_mission(client, state)

async def add_next_mission(client, state):
    if not state['mission_ids']:
        state['current_phase'] = 'start'
        await call_next_class(client, state)
        return

    _, cmd = state['mission_ids'].pop(0)
    logging.info(f"➕ Kirim misi: {cmd}_Add")
    state['waiting_for_add_response'] = True
    state['add_response_ready'].clear()
    state['removal_confirmed'].clear()

    await asyncio.sleep(2)
    await client.send_message(bot_username, f"{cmd}_Add")

    try:
        await asyncio.wait_for(state['add_response_ready'].wait(), timeout=10)
    except asyncio.TimeoutError:
        logging.warning("⚠️ Tidak ada respon _Add, ulangi")
        await asyncio.sleep(2)
        await client.send_message(bot_username, f"{cmd}_Add")
        await asyncio.sleep(4)
        await add_next_mission(client, state)
        return

    try:
        await asyncio.wait_for(state['removal_confirmed'].wait(), timeout=15)
    except asyncio.TimeoutError:
        logging.warning("⚠️ Tidak ada tombol 'Mulai Misi', kirim /mb_removeall")
        await client.send_message(bot_username, '/mb_removeall')
        await asyncio.sleep(4)

    await add_next_mission(client, state)

async def run_mb(client):
    me = await client.get_me()
    user_id = me.id

    if user_id not in locks:
        locks[user_id] = asyncio.Lock()

    async with locks[user_id]:
        running_flags[user_id] = True
        user_state[user_id] = {
            'user_id': user_id,
            'current_phase': 'start',
            'waiting_for_add_response': False,
            'add_response_ready': asyncio.Event(),
            'removal_confirmed': asyncio.Event(),
            'class_commands': [],
            'mission_ids': [],
            'current_class': ''
        }

        logging.info(f"🚀 Memulai MarineBase untuk user {user_id}")
        try:
            await client.send_message(bot_username, '/mb')
            while running_flags.get(user_id, False):
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            logging.warning(f"❌ MarineBase dibatalkan untuk user {user_id}")
            raise
        except FloodWaitError as e:
            logging.warning(f"[FLOOD] Tunggu {e.seconds} detik")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            running_flags[user_id] = False
            logging.error(f"[FATAL] MarineBase error: {e}")