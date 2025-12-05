# Setup Supabase Integration

Sistem presensi sekarang mendukung penyimpanan ke database Supabase secara otomatis.

## 🔧 Langkah Setup

### 1. Install Dependencies

```bash
source venv/bin/activate
pip install psycopg2-binary python-dotenv
```

### 2. Konfigurasi Database

Edit file `.env` dan ganti dengan kredensial Supabase Anda:

```env
# Ganti YOUR-PASSWORD dengan password database Supabase Anda
DATABASE_URL=postgresql://postgres.yhoziipnyenmtcbqupnb:YOUR-PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
DB_PASSWORD=your-actual-password-here

# Konfigurasi Ibadah (otomatis dibuat saat program jalan)
JENIS_KEBAKTIAN=Minggu Pagi
SESI_IBADAH=1
```

### 3. Pastikan User Sudah Terdaftar

**PENTING**: Nama dari face recognition harus **match** dengan `User.nama` di database!

Contoh data User:
```json
{
  "user_id": 9,
  "nama": "fil",
  "email": "teoinsani@gmail.com",
  "role": "user"
}
```

Maka training wajah harus diberi nama: **"fil"** (lowercase, exact match)

### 4. Test Koneksi

Test apakah koneksi ke Supabase berhasil:

```bash
python -c "from supabase_manager import SupabaseManager; m = SupabaseManager(); print('✓ Koneksi berhasil!')"
```

## 📊 Cara Kerja (UPDATED)

### Workflow Otomatis

1. **Program pertama kali jalan** hari ini:
   - Auto-create Ibadah baru untuk hari ini
   - Simpan: jenis_kebaktian, sesi_ibadah, tanggal_ibadah

2. **Wajah terdeteksi dan dikenali**:
   - Nama dari face recognition: `"fil"`
   - Cari di tabel `User` WHERE `nama = 'fil'` → dapat `user_id = 9`
   - Simpan Kehadiran: `id_ibadah` + `user_id` (sebagai id_jemaat)

3. **Fallback** (jika user tidak ditemukan):
   - Cari/buat di tabel `Jemaat`
   - Warning: "User tidak ditemukan di database: fil"

### Dual Storage (CSV + Supabase)

Sistem akan menyimpan presensi ke **2 tempat**:

1. **File CSV** (`data/attendance.csv`) - Lokal backup
2. **Supabase Database** - Terpusat, bisa diakses dari mana saja

Jika Supabase gagal, data tetap tersimpan di CSV.

### Data yang Disimpan

**Tabel Ibadah** (auto-created pertama kali hari ini):
```sql
INSERT INTO "Ibadah" (
  id_ibadah,           -- UUID auto-generated
  jenis_kebaktian,     -- Dari .env: "Minggu Pagi"
  sesi_ibadah,         -- Dari .env: 1
  tanggal_ibadah       -- Hari ini
)
```

**Tabel Kehadiran** (composite: Ibadah + User):
```sql
INSERT INTO "Kehadiran" (
  id_kehadiran,        -- UUID auto-generated
  id_ibadah,          -- Link ke Ibadah hari ini
  id_jemaat,          -- User.user_id yang ditemukan
  waktu_presensi,     -- Timestamp otomatis
  status,             -- "Hadir"
  name                -- Nama dari face recognition
)
```

## 🎯 Cara Pakai

### Jalankan Sistem Biasa

```bash
python 07_main_system.py
```

Sistem akan **otomatis**:
1. Deteksi wajah
2. Recognize nama (misal: "fil")
3. **Auto-create Ibadah** untuk hari ini (jika belum ada)
4. Cari User dengan nama "fil" → dapat user_id
5. Simpan Kehadiran (id_ibadah + user_id)
6. Simpan ke CSV

Output di console:
```
✓ Presensi tercatat (CSV): fil pada 13:54:26
  ✓ Ibadah baru dibuat: Minggu Pagi Sesi 1 - 2025-11-21
     ID: xxx-xxx-xxx
  ✓ User ditemukan: fil (user_id: 9)
  ✓ Kehadiran baru disimpan: fil pada 13:54:26
✓ Presensi tersimpan ke Supabase: fil
```

## 📝 Schema Database

```sql
-- Tabel yang digunakan:

Jemaat
  - id_jemaat (PK)
  - name
  - jabatan
  - status
  - dll...

Ibadah
  - id_ibadah (PK)
  - jenis_kebaktian
  - sesi_ibadah
  - tanggal_ibadah

Kehadiran
  - id_kehadiran (PK)
  - id_ibadah (FK → Ibadah)
  - id_jemaat (FK → Jemaat)
  - waktu_presensi
  - status
  - name
```

## ⚠️ Troubleshooting

### Error: "DATABASE_URL tidak ditemukan"

**Solusi**: Pastikan file `.env` ada dan berisi `DATABASE_URL`

### Error: "relation 'Jemaat' does not exist"

**Solusi**: Pastikan schema Prisma sudah di-migrate ke database:
```bash
npx prisma db push
# atau
npx prisma migrate deploy
```

### Error: "password authentication failed"

**Solusi**: Cek password di `.env` sudah benar

### Supabase skip, pakai CSV saja

**Normal behavior**: Jika Supabase tidak configured atau error, sistem otomatis fallback ke CSV saja.

## 🔍 Cek Data

### Lihat Kehadiran di Database

```bash
python << 'EOF'
from supabase_manager import SupabaseManager
manager = SupabaseManager()
kehadiran = manager.get_kehadiran_hari_ini()
for name, waktu in kehadiran:
    print(f"{name}: {waktu}")
EOF
```

### Query Manual

```python
from supabase_manager import SupabaseManager
manager = SupabaseManager()
conn = manager.get_connection()
cur = conn.cursor()

# Query apa saja
cur.execute('SELECT * FROM "Kehadiran" LIMIT 10')
results = cur.fetchall()
print(results)

cur.close()
manager.return_connection(conn)
```

## 🎉 Keuntungan Supabase

✅ **Terpusat** - Semua device bisa akses database yang sama  
✅ **Real-time** - Data langsung sync  
✅ **Backup otomatis** - Supabase handle backup  
✅ **Scalable** - Bisa diakses dari web/mobile apps  
✅ **Fallback safe** - Jika error, masih ada CSV  

## 📌 Catatan Penting

1. **Jangan commit** file `.env` ke Git (sudah ada di `.gitignore`)
2. **Password aman** - Jangan share password database
3. **Connection pooling** - Sistem pakai pool untuk performa
4. **Auto-cleanup** - Connection pool otomatis di-close saat program exit

---

**Happy coding!** 🚀
