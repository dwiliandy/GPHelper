from telethon import events
import asyncio
import re
import time

running_flags = {}
bot_username = 'GrandPiratesBot'

def init(client,user_id):
    """Mendaftarkan event handler ke user_client"""
    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        
    
      if not running_flags.get(user_id, False):
            return
      
      text = event.raw_text
      if 'Bayi-bayi siput laut 🐌BabySeaSnail disedot' in event.raw_text:
          tmp = 0
          ssf = [x for x in event.text.split() if '/ssf_incubator' in x]
          time.sleep(1)
          await event.respond(ssf[tmp])
          return
      if 'SeaSnail masih belum berkembang'or 'SeaSnail akan bertambah besar 'or 'SeaSnail sudah mencapai versi paling besar' in text:
          match = re.search(r'(/ssf_incubator_\d+_ambil)', text)
          if match:
              command = match.group(1)
              time.sleep(1)
              await event.respond(command)
      
      if 'Kru peternak dikembalikan' in text:
          match = re.search(r'/ssf_incubator_(\d+)_(\d+)', text)
          if match:
              mesin = match.group(1)
              id_kru = match.group(2)
              command = match.group(0)
              time.sleep(1)
              await event.respond(command)
      
      if 'Apa kamu yakin ingin mempekerjakan' in event.raw_text:
          time.sleep(1)
          await event.click(0)
          return
      
      if 'Berhasil mempekerjakan' in event.raw_text:
          match = re.search(r'(/ssf_incubator_\d+)', text)
          if match:
              command = match.group(1)
              time.sleep(1)
              await event.respond(command)
          return
      
      if 'cek /seaSnailFarm' in event.raw_text:
          tmp += 1  # Tambahkan 1 agar ke incubator berikutnya
          if tmp < len(ssf):
              time.sleep(1)
              await event.respond(ssf[tmp])
          return


async def run_ssf(user_id, client):
    running_flags[user_id] = True
    print("⚔️ Memulai Script Auto Claim SSF...")
    try:
        while True:
            await asyncio.sleep(2)  # delay agar tidak terlalu cepat
    except asyncio.CancelledError:
        
        print(f"❌ Script Auto Claim SSF dihentikan untuk user {user_id}.")
        running_flags[user_id] = False
        raise  # 