# GPHelper - Telegram Bot Automation Grand Pirates

GPHelper adalah bot automation.  
Bot ini memiliki berbagai script untuk grinding, eksplorasi musuh, menjalankan misi Marine Base, dan script event musiman yang dapat disesuaikan.

## ✨ Fitur

- 🔁 Auto Grinding (lawan musuh secara otomatis)
- 🔍 Auto Search Musuh (eksplorasi area baru)
- 🐌 Auto Claim Sea Snail Farm
- 🐌 Auto Pakai Golden Snail saat dibutuhkan
- ⚔️ Auto Naval Battle (serang musuh di laut)
- 🏴 Auto Misi Marine Base
- 📆 Script Event (berubah sesuai event aktif)

## ⚙️ Teknologi

- Python
- Telethon (Telegram Client Library)

---

## 🚀 Instalasi

1. Clone repository:

   ```bash
   git clone https://github.com/dwiliandy/GPHelper.git
   cd GPHelper
   ```

2. Install dependency:

   ```bash
   pip install -r requirements.txt
   ```

3. Salin file `.env.example` menjadi `.env`, lalu isi dengan:

   - `APP_ID`
   - `APP_HASH`
   - `BOT_TOKEN`

4. Tambahkan session akun Telegram kamu ke folder `sessions/`

5. Update file `sessions/sessions_map.json` dengan format:

   ```json
   {
   	"123456789": "namasession"
   }
   ```

6. Jalankan bot:
   ```bash
   python main.py
   ```

---

## 📁 Struktur Folder

```
GPHelper/
├── main.py               # Entry point utama
├── script/               # Berisi script automation seperti:
│   ├── auto_search.py
│   ├── naval.py
│   ├── mb.py
│   └── ...
├── utils/                # Helper function umum
├── sessions/             # File session Telethon
└── .env                  # Konfigurasi kredensial bot
```

---

## 📄 Lisensi

Project ini open-source untuk keperluan belajar.  
Tidak untuk diperjualbelikan atau digunakan dalam skala publik tanpa izin.

---

## ✨ Kontributor

Made with 🧠 by [Dwiliandi Omega](https://github.com/dwiliandy)
