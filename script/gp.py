from telethon import events
import asyncio
import re
import random

bot_username = 'GrandPiratesBot'
buff_item = "use_Yubashiri_10"
buff_max = 25
buff = 25

curr_exp = 0
need_exp = 0
running_flags = {}
cek_kapal_event = asyncio.Event()


def init(client,user_id):
    """Mendaftarkan event handler ke user_client"""
    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
      global curr_exp, need_exp, buff  # Pastikan mengakses variabel global

      if not running_flags.get(user_id, False):
            return
      
      if not cek_kapal_event.is_set():  # Jika cekKapal belum selesai, tunggu dulu
          print("🔄 Menunggu cekKapal selesai...")
          await cek_kapal_event.wait()  # Tunggu sampai cekKapal selesai
      if event.text:
          # Cek buff, jika 0
          if buff <= 0:
              print(f"🔥 Buff habis, menggunakan item {buff_item}")
              await client.send_message(bot_username, buff_item)
              buff = buff_max  # Reset buff
              await client.send_message(bot_username, "/adv")
              await asyncio.sleep(1)

          match = re.search(r'Sisa energi: \*\*(\d+)%\*\*', event.text)
          if match:
              sisa_energi = int(match.group(1))
              print(f"Sisa Energi: {sisa_energi}%")
              
          if 'Kamu menelusuri' in event.text:
              await asyncio.sleep(1)  # Jeda sebelum klik, bisa disesuaikan
              await event.buttons[0][0].click()  # 🔥 Jalankan klik paralel
          elif 'KAMU MENANG!!' in event.text:
              buff -= 1
              print(f"💢 Buff tersisa: {buff}")
              # Tambahkan EXP Kapal
              exp_kapal_match = re.search(r'❇️ (\d[\d,]*) EXP Kapal\*\*', event.text)
              if exp_kapal_match:
                  exp_kapal = int(exp_kapal_match.group(1).replace(',', ''))
                  curr_exp += exp_kapal
                  print(f"🚢 EXP Kapal + {exp_kapal} ➡️ Total: {curr_exp}/{need_exp}")
                  # Cek apakah cukup untuk naik level
                  if curr_exp >= need_exp and need_exp != 0:
                      print("🚨 EXP cukup untuk level up! Memanggil cekKapal() lagi.")
                      await cekKapal()
                      await asyncio.sleep(2)

              await asyncio.sleep(1)
              await event.buttons[0][0].click()  # 🔥 Jalankan klik paralel
              await asyncio.sleep(1)
          elif 'Energi untuk bertarung telah habis' in event.text:
              print("🔄 Energi rendah, mengirim 'restore_x' dan '/adv'")
              await client.send_message(bot_username, "restore_x")
              await asyncio.sleep(1)
          elif 'Musuh menang' in event.text:
              buff -= 1
              await asyncio.sleep(1)
              print("🔄 Energi rendah, mengirim 'restore_x' dan '/adv'")
              await client.send_message(bot_username, "restore_x")
              await asyncio.sleep(1)
              await client.send_message(bot_username, "/adv")
              await asyncio.sleep(2)
          else:
            await asyncio.sleep(1)
            await client.send_message(bot_username, "/adv")
            print("📨 /adv dikirim, menunggu balasan...")

            # Tunggu hingga 10 detik untuk balasan dari bot
            for i in range(20):  # Coba 20x dengan interval 0.5 detik (total 10 detik)
                async for msg in client.iter_messages(bot_username, limit=1):
                    if msg.buttons and "Telusuri" in msg.buttons[0][0].text:
                        await msg.click(0)
                        print("🖱️ Tombol Telusuri diklik")
                        break
                else:
                    await asyncio.sleep(0.5)
                    continue
                break
            else:
                print("⏰ Tidak ada tombol 'Telusuri' dalam 10 detik")

            await asyncio.sleep(2)


async def cekKapal(client):
    global curr_exp, need_exp
    await client.send_message(bot_username, "/kapal")
    await asyncio.sleep(2)

    async for message in client.iter_messages(bot_username, limit=1):
        text = message.text
        
        # Cek EXP MAX
        if "EXP: (MAX)" in text:
            print("🚨 EXP Kapal sudah MAX, naik level sekarang!")
            bot_id = (await client.get_entity(bot_username)).id
            random_update = random.choice([ 
                '/levelupkapal_ATK', '/levelupkapal_DEF',
                '/levelupkapal_HP', '/levelupkapal_SPEED'
            ])
            await client.send_message(bot_username, random_update)

            for _ in range(10):
                async for msg in client.iter_messages(bot_username, limit=1):
                    if msg.sender_id == bot_id and msg.buttons:
                        print(f"🆙 Klik tombol level up {random_update}")
                        await msg.click(0)
                        await asyncio.sleep(2)
                        await cekKapal()  # Cek kapal lagi setelah naik level
                        return
                await asyncio.sleep(0.5)
            else:
                print("⏰ Timeout saat menunggu tombol level up")

        else:
            match = re.search(r'EXP: \*\*\(([\d,]+)/([\d,]+)\)\*\*', text)
            if match:
                curr_exp = int(match.group(1).replace(',', ''))
                need_exp = int(match.group(2).replace(',', ''))
                print(f"🚢 EXP Kapal: {curr_exp}/{need_exp}")
            else:
                print("❓ Tidak menemukan data EXP")

    # Set Event untuk menandakan cekKapal selesai
    cek_kapal_event.set()


async def run_attack(user_id, client):
    running_flags[user_id] = True
    print("⚔️ Memulai Script Attack...")
    try:
        await cekKapal(client)
        await client.send_message(bot_username, "/adv")
        while True:
            await asyncio.sleep(2)  # delay agar tidak terlalu cepat
    except asyncio.CancelledError:
        
        print(f"❌ Script Attack dihentikan untuk user {user_id}.")
        running_flags[user_id] = False
        raise  # ⬅️ ini penting untuk benar-benar menghentikan task