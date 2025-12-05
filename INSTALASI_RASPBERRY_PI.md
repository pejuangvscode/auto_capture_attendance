# Panduan Instalasi - Sistem Presensi GKI Karawaci
## Instalasi di Raspberry Pi 5

---

## Persyaratan Sistem

### Hardware
- **Raspberry Pi 5** (4GB atau 8GB RAM recommended)
- **Storage**: Minimal 16GB microSD (32GB recommended)
- **Kamera**: USB Webcam atau Raspberry Pi Camera Module
- **Internet**: Untuk download dependencies

### Software
- **OS**: Raspberry Pi OS (Bookworm atau lebih baru)
- **Python**: 3.11 atau lebih baru (biasanya sudah terinstall)

---

## Tahap 1: Setup Virtual Environment

### 1.1 Clone atau Copy Project ke Raspberry Pi

```bash
# Jika menggunakan git
git clone <repository-url>
cd pkm

# Atau copy manual ke Raspberry Pi
```

### 1.2 Jalankan Setup Script

```bash
# Berikan permission execute
chmod +x 00_setup_venv.sh

# Jalankan setup
bash 00_setup_venv.sh
```

**Proses ini akan:**
- Install `python3-venv` jika belum ada
- Membuat virtual environment di folder `venv/`
- Install semua dependencies (OpenCV, PyTorch, InsightFace, dll)
- Estimasi waktu: 10-30 menit (tergantung koneksi internet)

### 1.3 Aktivasi Virtual Environment

```bash
source venv/bin/activate
```

Anda akan melihat `(venv)` di awal prompt terminal.

---

## Tahap 2: Setup Direktori Data

### 2.1 Buat Folder Data (Otomatis)

Folder akan otomatis dibuat saat pertama kali menjalankan sistem:
```
data/
├── faces/          # Foto wajah yang sudah diberi nama
├── unknown/        # Foto wajah yang belum dikenali
├── face_encodings.pkl  # Model wajah (dibuat saat retrain)
└── attendance.csv      # Data kehadiran
```

### 2.2 Setup Supabase (Opsional)

Jika ingin menggunakan database Supabase:

1. Edit file `.env`:
```bash
nano .env
```

2. Isi dengan kredensial Supabase Anda:
```env
# Supabase Database Configuration
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
DB_PASSWORD=your-password-here

# Konfigurasi Ibadah
JENIS_KEBAKTIAN=Minggu Pagi
SESI_IBADAH=1
```

3. Pastikan schema sudah di-migrate di Supabase:
```bash
# Di project Prisma Anda
npx prisma db push
```

> **Catatan**: Jika tidak setup Supabase, sistem akan otomatis menggunakan CSV saja.

---

## Tahap 3: Training Model Pertama Kali

### 3.1 Capture Wajah Pertama

```bash
# Pastikan virtual environment aktif
source venv/bin/activate

# Jalankan sistem (wajah akan di-capture sebagai "Unknown")
python 01_main_system.py
```

**Cara kerja:**
1. Sistem akan otomatis detect wajah
2. Capture 5 foto dalam beberapa detik
3. Tekan `q` untuk keluar setelah capture selesai

### 3.2 Retrain Model

```bash
python 02_retrain_model.py
```

**Proses:**
1. Pilih `y` untuk lanjutkan
2. Pilih opsi **`1`** untuk memberi nama satu per satu, atau
3. Pilih opsi **`2`** untuk gunakan nama folder (jika sudah ada nama)

**Input data jemaat:**
- Tekan **Enter** untuk gunakan nilai default
- Atau isi data lengkap (nama, jabatan, tanggal lahir, dll)

**Output:**
```
Model berhasil dilatih ulang!
Jemaat terdaftar ke database (jika Supabase aktif)
```

---

## Tahap 4: Menjalankan Sistem Presensi

### 4.1 Jalankan Sistem

```bash
# Aktifkan virtual environment
source venv/bin/activate

# Jalankan sistem
python 01_main_system.py
```

### 4.2 Kontrol Keyboard

Saat sistem berjalan:

| Tombol | Fungsi |
|--------|--------|
| `q` | Keluar dari sistem |
| `s` | Tampilkan statistik hari ini |
| `+` | Kurangi frame skip (lebih akurat, lebih lambat) |
| `-` | Tambah frame skip (lebih cepat, kurang akurat) |

### 4.3 Fitur Sistem

**Deteksi & Recognisi:**
- Face Detection: YOLO (cepat & akurat)
- Face Recognition: ArcFace (akurat dengan confidence score)
- Auto Capture: Wajah unknown otomatis di-capture
- Multi-threading: Smooth 15-25 FPS

**UI Modern:**
- Bounding box tipis dengan corner highlights
- Nama wajah di atas kotak
- Clean & minimal interface

**Attendance:**
- Auto-save ke CSV (`data/attendance.csv`)
- Auto-save ke Supabase (jika aktif)
- Cooldown 1 jam (tidak bisa absen 2x dalam 1 jam)

---

## Tahap 5: Monitoring & Maintenance

### 5.1 Cek Kehadiran Hari Ini

```bash
# Tekan 's' saat sistem berjalan
# Atau lihat file CSV
cat data/attendance.csv
```

### 5.2 Tambah Wajah Baru

**Cara 1: Auto Capture (Recommended)**
1. Jalankan sistem: `python 01_main_system.py`
2. Orang baru akan di-capture otomatis sebagai "Unknown"
3. Keluar dengan `q`
4. Retrain model: `python 02_retrain_model.py`

**Cara 2: Manual Copy**
1. Buat folder baru di `data/faces/NamaOrang/`
2. Copy minimal 5 foto wajah (format: .jpg)
3. Retrain model: `python 02_retrain_model.py`

### 5.3 Update Model

Setiap kali ada wajah baru atau perubahan:
```bash
python 02_retrain_model.py
```

---

## Konfigurasi Lanjutan

### Edit Konfigurasi

File: `config.py`

```python
# Kamera
CAMERA_INDEX = 0  # 0 untuk USB webcam, ubah jika ada multiple camera
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Deteksi
FACE_DETECTION_THRESHOLD = 0.5  # Threshold deteksi YOLO (0-1)
FACE_RECOGNITION_THRESHOLD = 0.42  # Threshold recognition ArcFace (0-1)

# Capture
FRAMES_TO_CAPTURE = 5  # Jumlah foto per wajah
CAPTURE_INTERVAL = 3  # Interval capture (frame)

# Attendance
ATTENDANCE_COOLDOWN = 3600  # Cooldown dalam detik (default: 1 jam)
```

### Optimasi untuk Raspberry Pi

Jika FPS terlalu rendah, edit `01_main_system.py`:

```python
# Line ~246: Uncomment untuk resize frame
frame = cv2.resize(frame, (640, 480))  # Processing lebih cepat

# Line ~61: Tambah frame skip
self.frame_skip = 3  # Skip lebih banyak frame
```

---

## Troubleshooting

### Error: NumPy Version Conflict (Raspberry Pi 5)

Jika muncul error `numpy.core.multiarray failed to import`:

```bash
# Jalankan fix script
chmod +x fix_numpy.sh
bash fix_numpy.sh
```

Atau manual:
```bash
source venv/bin/activate
pip uninstall -y numpy opencv-python opencv-contrib-python
pip install numpy==1.24.3
pip install --no-cache-dir opencv-contrib-python==4.8.1.78
```

### Error: OpenCV cvNamedWindow (Raspberry Pi 5)

Install system dependencies:

```bash
sudo apt update
sudo apt install -y libopencv-dev python3-opencv libgtk-3-dev
```

Lalu reinstall:
```bash
source venv/bin/activate
pip uninstall -y opencv-python opencv-contrib-python
pip install --no-cache-dir opencv-contrib-python==4.8.1.78
```

### Kamera Tidak Terdeteksi

```bash
# Cek kamera tersedia
ls /dev/video*

# Test kamera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.read()[0] else 'FAIL')"
```

Jika FAIL, coba ubah `CAMERA_INDEX` di `config.py`

### Error: Module 'cv2' Not Found

```bash
# Reinstall OpenCV
source venv/bin/activate
pip uninstall -y opencv-python opencv-python-headless
pip install opencv-contrib-python
```

### Error: No module 'psycopg2'

```bash
source venv/bin/activate
pip install psycopg2-binary python-dotenv
```

### FPS Terlalu Rendah

1. **Kurangi resolusi kamera** di `config.py`:
   ```python
   FRAME_WIDTH = 640
   FRAME_HEIGHT = 480
   ```

2. **Tambah frame skip** dengan tekan `-` saat running

3. **Disable Supabase** jika tidak perlu (edit `attendance_manager.py`)

### Wajah Tidak Terdeteksi

1. **Pastikan pencahayaan cukup**
2. **Kurangi threshold** di `config.py`:
   ```python
   FACE_DETECTION_THRESHOLD = 0.3  # Lebih sensitive
   ```

---

## Auto-Start saat Boot (Opsional)

### Buat Service Systemd

1. Buat file service:
```bash
sudo nano /etc/systemd/system/presensi.service
```

2. Isi dengan:
```ini
[Unit]
Description=Sistem Presensi GKI Karawaci
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pkm
Environment="DISPLAY=:0"
ExecStart=/home/pi/pkm/venv/bin/python /home/pi/pkm/01_main_system.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable & start:
```bash
sudo systemctl enable presensi.service
sudo systemctl start presensi.service

# Cek status
sudo systemctl status presensi.service
```

---

## Struktur File Project

```
pkm/
├── 00_setup_venv.sh           # Setup script
├── 01_main_system.py          # Main program
├── 02_retrain_model.py        # Training script
├── config.py                  # Konfigurasi
├── face_detector_yolo.py      # YOLO detector
├── face_encoder_arcface.py    # ArcFace encoder
├── face_recognizer_arcface.py # ArcFace recognizer
├── attendance_manager.py      # Attendance handler
├── unknown_face_collector.py  # Auto capture handler
├── supabase_manager.py        # Database handler
├── requirements.txt           # Python dependencies
├── .env                       # Environment config
├── .env.example               # Template .env
├── INSTALASI_RASPBERRY_PI.md  # Dokumentasi ini
├── README.md                  # Dokumentasi utama
├── PANDUAN_LENGKAP.md         # Panduan lengkap
├── SUPABASE_SETUP.md          # Setup database
├── venv/                      # Virtual environment
└── data/                      # Data folder
    ├── faces/                 # Training images
    ├── unknown/               # Captured unknown faces
    ├── face_encodings.pkl     # Trained model
    └── attendance.csv         # Attendance records
```

---

## Dukungan

Jika mengalami masalah:

1. **Cek log error** dengan detail
2. **Pastikan semua dependencies terinstall**: `pip list`
3. **Cek kamera**: `ls /dev/video*`
4. **Test koneksi database** (jika pakai Supabase)

---

## Lisensi

Sistem Presensi GKI Karawaci
(c) 2025 - Untuk keperluan gereja

---

Selamat! Sistem presensi Anda sudah siap digunakan!
