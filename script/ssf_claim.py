from telethon import events
import asyncio
import re

running_flags = {}
state = {}
registered_handlers = {}  # ✅ Perubahan baru
bot_username = 'GrandPiratesBot'

def init(client, user_id):
    """Mendaftarkan event handler ke user_client"""
    # ✅ Cek apakah handler sudah didaftarkan sebelumnya
    if user_id in registered_handlers:
        return  # sudah terdaftar, hindari dobel handler
    
    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        if not running_flags.get(user_id, False):
            return
        
        text = event.raw_text
        
        # Inisialisasi state untuk user jika belum ada
        if user_id not in state:
            state[user_id] = {"tmp": 0, "ssf": []}
        
        user_state = state[user_id]

        if 'Bayi-bayi siput laut 🐌BabySeaSnail disedot' in text:
            user_state["tmp"] = 0
            user_state["ssf"] = [x for x in event.text.split() if '/ssf_incubator' in x]
            await asyncio.sleep(1)
            if user_state["ssf"]:
                await event.respond(user_state["ssf"][user_state["tmp"]])
            return
        
        if any(phrase in text for phrase in [
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
            user_state["tmp"] += 1
            if user_state["tmp"] < len(user_state["ssf"]):
                await asyncio.sleep(1)
                await event.respond(user_state["ssf"][user_state["tmp"]])
            return
        
    # ✅ Simpan handler yang sudah terdaftar agar tidak ganda
    registered_handlers[user_id] = handler

async def run_ssf(user_id, client):
    running_flags[user_id] = True
    print("⚔️ Memulai Script Auto Claim SSF...")
    try:
        while running_flags[user_id]:
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        print(f"❌ Script Auto Claim SSF dihentikan untuk user {user_id}.")
        running_flags[user_id] = False
        raise
