# README - Sistem Presensi Wajah GKI Karawaci

Sistem presensi otomatis menggunakan face recognition berbasis YOLO + ArcFace untuk gereja.

---

## Fitur Utama

- Face Detection: YOLO untuk deteksi wajah cepat & akurat
- Face Recognition: ArcFace untuk pengenalan wajah dengan confidence score
- Auto Capture: Wajah tidak dikenal otomatis di-capture
- Multi-threading: Performa optimal 15-25 FPS
- Database Integration: Supabase PostgreSQL (opsional)
- CSV Export: Data kehadiran tersimpan lokal
- Modern UI: Interface clean dengan bounding box modern
- Attendance Cooldown: Cegah duplikasi absen dalam 1 jam

---

## Quick Start

### 1. Setup Environment

```bash
# Jalankan setup script
bash 00_setup_venv.sh

# Aktivasi virtual environment
source venv/bin/activate
```

### 2. Retrain Model

```bash
# Pertama kali: jalankan main system untuk capture wajah
python 07_main_system.py
# Tekan 'q' setelah wajah ter-capture

# Training model dengan wajah yang ter-capture
python 08_retrain_model.py
```

### 3. Jalankan Sistem

```bash
python 07_main_system.py
```

**Kontrol:**
- `q` - Keluar
- `s` - Tampilkan statistik
- `+/-` - Kurangi/tambah frame skip

---

## Dokumentasi Lengkap

Untuk instalasi di Raspberry Pi, lihat:
- INSTALASI_RASPBERRY_PI.md - Panduan lengkap step-by-step

Dokumentasi lainnya:
- PANDUAN_LENGKAP.md - Panduan lengkap sistem
- SUPABASE_SETUP.md - Setup database Supabase

---

## Dependencies

### Core Libraries
- **Python**: 3.8+
- **OpenCV**: 4.12.0.88 (opencv-contrib-python)
- **PyTorch**: 2.5.1
- **Ultralytics**: 8.3.235 (YOLO)
- **InsightFace**: 0.7.3 (ArcFace)
- **PostgreSQL**: psycopg2-binary 2.9.11

### Full List
Lihat `requirements.txt` untuk daftar lengkap.

---

## Struktur Project

```
pkm/
├── 00_setup_venv.sh           # Setup script
├── 07_main_system.py          # Main program
├── 08_retrain_model.py        # Training script
├── config.py                  # Konfigurasi
├── face_detector_yolo.py      # YOLO detector
├── face_encoder_arcface.py    # ArcFace encoder
├── face_recognizer_arcface.py # ArcFace recognizer
├── attendance_manager.py      # Attendance handler
├── unknown_face_collector.py  # Auto capture handler
├── supabase_manager.py        # Database handler
├── requirements.txt           # Python dependencies
├── .env.example               # Template environment config
├── README.md                  # Dokumentasi ini
├── INSTALASI_RASPBERRY_PI.md  # Panduan Raspberry Pi
├── PANDUAN_LENGKAP.md         # Panduan lengkap
├── SUPABASE_SETUP.md          # Setup database
└── data/                      # Data folder
    ├── faces/                 # Training images
    ├── unknown/               # Captured unknown faces
    ├── face_encodings.pkl     # Trained model
    └── attendance.csv         # Attendance records
```

---

## Konfigurasi

### Setup Supabase (Opsional)

1. Copy `.env.example` ke `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` dengan kredensial Supabase:
```env
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@[HOST]:6543/postgres
DB_PASSWORD=your-password
JENIS_KEBAKTIAN=Minggu Pagi
SESI_IBADAH=1
```

3. Migrate database schema (di project Prisma):
```bash
npx prisma db push
```

### Konfigurasi Kamera & Deteksi

Edit `config.py`:

```python
# Kamera
CAMERA_INDEX = 0  # Ubah jika ada multiple camera
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Threshold
FACE_DETECTION_THRESHOLD = 0.5  # YOLO (0-1)
FACE_RECOGNITION_THRESHOLD = 0.42  # ArcFace (0-1)

# Capture
FRAMES_TO_CAPTURE = 5  # Jumlah foto per wajah
ATTENDANCE_COOLDOWN = 3600  # Cooldown 1 jam

```

---

## Troubleshooting

### Import Error: ultralytics

```bash
source venv/bin/activate
pip install ultralytics
```

### OpenCV GUI Error

```bash
pip uninstall -y opencv-python opencv-python-headless
pip install opencv-contrib-python
```

### Kamera Tidak Terdeteksi

```bash
# Cek device
ls /dev/video*

# Test kamera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.read()[0] else 'FAIL')"
```

Ubah `CAMERA_INDEX` di `config.py` jika perlu.

### FPS Rendah di Raspberry Pi

1. Kurangi resolusi:
```python
# config.py
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
```

2. Tambah frame skip (tekan `-` saat running)

3. Resize frame di `07_main_system.py`:
```python
frame = cv2.resize(frame, (640, 480))
```

---

## Workflow

### 1. First Time Setup
```
Setup venv → Capture wajah → Retrain model → Run system
```

### 2. Tambah Wajah Baru
```
Run system → Wajah ter-capture → Retrain model
```

### 3. Daily Operation
```
Jalankan 07_main_system.py → Monitor kehadiran
```

---

## Algoritma

### Face Detection (YOLO)
- Model: `yolov8n-face` (lightweight, cepat)
- Threshold: 0.5 (configurable)
- Output: Bounding box coordinates

### Face Recognition (ArcFace)
- Model: `buffalo_sc` (InsightFace)
- Embedding: 512-dimensional vector
- Distance: Cosine similarity
- Threshold: 0.42 (configurable)

### Image Preprocessing
- Auto padding: 15% border
- Auto resize: 640px for encoding
- Color space: BGR (OpenCV native)

---

## Performance

### Raspberry Pi 4 (4GB)
- **FPS**: 15-25 FPS (multi-threading)
- **Detection**: Real-time
- **Recognition**: < 100ms per face
- **Attendance Save**: Async (no UI freeze)

### Optimasi
- **Frame skip**: Skip 2 frame default (configurable)
- **Multi-threading**: 3 threads (capture, process, attendance)
- **Queue system**: Non-blocking async operations

---

## Keamanan

- Environment variables di `.env` (not committed)
- Database connection pooling
- SQL injection protection (parameterized queries)
- Password hashing (jika diperlukan di masa depan)

---

## License

(c) 2025 GKI Karawaci - Internal Use Only

---

## Credits

**Libraries:**
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- [InsightFace](https://github.com/deepinsight/insightface)
- [OpenCV](https://opencv.org/)
- [PyTorch](https://pytorch.org/)

**Database:**
- [Supabase](https://supabase.com/)

---

## Support

Untuk masalah atau pertanyaan, hubungi tim IT GKI Karawaci.

---

Happy coding & God bless!