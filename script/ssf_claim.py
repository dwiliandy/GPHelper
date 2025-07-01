from telethon import events
import asyncio
import re

bot_username = 'GrandPiratesBot'

running_flags = {}     # user_id: bool
user_state = {}        # user_id: { tmp, ssf }
handler_registered = False

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

        if 'Bayi-bayi siput laut 🐌BabySeaSnail disedot' in text:
            state["tmp"] = 0
            state["ssf"] = [x for x in event.text.split() if '/ssf_incubator' in x]
            await asyncio.sleep(1)
            if state["ssf"]:
                await event.respond(state["ssf"][state["tmp"]])
            return

        if any(msg in text for msg in [
            'SeaSnail masih belum berkembang',
            'SeaSnail akan bertambah besar',
            'SeaSnail sudah mencapai versi paling besar'
        ]):
            match = re.search(r'(/ssf_incubator_\d+_ambil)', text)
            if match:
                await asyncio.sleep(1)
                await event.respond(match.group(1))
            return

        if 'Kru peternak dikembalikan' in text:
            match = re.search(r'/ssf_incubator_(\d+)_(\d+)', text)
            if match:
                await asyncio.sleep(1)
                await event.respond(match.group(0))
            return

        if 'Apa kamu yakin ingin mempekerjakan' in text:
            await asyncio.sleep(1)
            await event.click(0)
            return

        if 'Berhasil mempekerjakan' in text:
            match = re.search(r'(/ssf_incubator_\d+)', text)
            if match:
                await asyncio.sleep(1)
                await event.respond(match.group(1))
            return

        if 'cek /seaSnailFarm' in text:
            state["tmp"] += 1
            if state["tmp"] < len(state["ssf"]):
                await asyncio.sleep(1)
                await event.respond(state["ssf"][state["tmp"]])
            return

    handler_registered = True


async def run_ssf(user_id, client):
    running_flags[user_id] = True
    user_state[user_id] = {
        "tmp": 0,
        "ssf": []
    }

    print(f"⚙️ Memulai Script SSF untuk user {user_id}")
    try:
        while running_flags.get(user_id, False):
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        running_flags[user_id] = False
        print(f"❌ Script SSF dihentikan untuk user {user_id}")
        raise
