# 📖 PANDUAN LENGKAP - Sistem Presensi Otomatis GKI Karawaci

## 🎯 Deskripsi Sistem
Sistem presensi otomatis berbasis pengenalan wajah menggunakan teknologi:
- **YOLOv8-face**: Deteksi wajah yang akurat dan ringan
- **ArcFace (InsightFace)**: Pengenalan wajah dengan akurasi tinggi
- **OpenCV**: Pemrosesan video dan gambar
- Optimized untuk Raspberry Pi dan komputer biasa

---

## 📂 Struktur Folder

```
pkm/
│
├── 📁 SETUP AWAL (Jalankan sekali)
│   ├── 00_setup_venv.sh           # Setup virtual environment
│   └── 01_setup_directories.py    # Buat struktur folder
│
├── 📁 PROGRAM UTAMA (Yang sering dipakai)
│   ├── 07_main_system.py          # ⭐ Presensi live camera
│   ├── 07_main_system_video.py    # ⭐ Proses video rekaman
│   ├── 08_retrain_model.py        # ⭐ Training model (tambah wajah baru)
│   └── 09_batch_process_videos.py # ⭐ Proses banyak video sekaligus
│
├── 📁 MODUL SISTEM (Jangan diubah)
│   ├── config.py                  # Konfigurasi threshold & parameter
│   ├── face_detector_yolo.py      # Deteksi wajah YOLO
│   ├── face_encoder_arcface.py    # Encoding wajah ArcFace
│   ├── face_recognizer_arcface.py # Pengenalan wajah
│   ├── attendance_manager.py      # Manajemen presensi CSV
│   └── unknown_face_collector.py  # Auto-capture wajah baru
│
├── 📁 TEST/DEBUG (Opsional - untuk testing)
│   ├── 02_face_detector_yolo.py   # Test deteksi wajah
│   ├── 03_face_encoder_arcface.py # Test encoding
│   ├── 04_face_recognizer_arcface.py # Test recognition
│   ├── 05_attendance_manager.py   # Test attendance
│   └── 06_unknown_face_collector.py # Test unknown collector
│
├── 📁 DATA & OUTPUT
│   └── data/
│       ├── yolov8n-face.pt        # Model YOLO (auto-download)
│       ├── face_encodings.pkl     # Model wajah terlatih ⭐ PENTING
│       ├── attendance.csv         # Hasil presensi ⭐ OUTPUT
│       ├── faces/                 # Wajah yang sudah diberi nama
│       │   └── [nama_orang]/
│       │       ├── face_000.jpg
│       │       └── ...
│       └── unknown/               # Wajah belum dikenali (auto-capture)
│           └── unknown_X_[timestamp]/
│               ├── face_000.jpg
│               └── ...
│
├── 📁 ENVIRONMENT & DEPENDENCIES
│   ├── venv/                      # Virtual environment Python
│   └── requirements.txt           # Daftar library yang dibutuhkan
│
└── 📁 DOKUMENTASI
    ├── PANDUAN_LENGKAP.md         # ⭐ Baca file ini!
    ├── INSTALL.md                 # Panduan instalasi
    ├── VIDEO_GUIDE.md             # Panduan khusus video
    └── README.md                  # Overview singkat
```

---

## 🚀 QUICK START - Langkah Cepat

### 1️⃣ Setup Awal (Hanya Sekali)

```bash
# 1. Masuk ke folder project
cd /home/teo/Documents/pkm

# 2. Setup virtual environment
bash 00_setup_venv.sh

# 3. Buat struktur folder
source venv/bin/activate
python 01_setup_directories.py
```

### 2️⃣ Menggunakan Sistem

#### A. Mode Live Camera (Presensi Real-time)
```bash
source venv/bin/activate
python 07_main_system.py
```
- Sistem akan membuka kamera
- Deteksi dan kenali wajah secara real-time
- Auto-save presensi ke `data/attendance.csv`
- Auto-capture wajah baru ke `data/unknown/`

#### B. Mode Video File (Proses Rekaman)
```bash
source venv/bin/activate
python 07_main_system_video.py video_ibadah.mp4 -o hasil.mp4
```
- Proses file video
- Output video dengan label nama
- Auto-capture wajah baru

#### C. Training Model (Tambah Wajah Baru)
```bash
source venv/bin/activate
python 08_retrain_model.py
```
- Proses wajah dari `data/unknown/`
- Beri nama untuk setiap orang
- Model otomatis diupdate

#### D. Batch Processing (Banyak Video)
```bash
source venv/bin/activate
python 09_batch_process_videos.py
```
- Proses semua video dalam folder
- Output otomatis dengan prefix

---

## 📋 WORKFLOW LENGKAP

### Skenario 1: Pertama Kali Setup Sistem
```bash
# 1. Setup environment
bash 00_setup_venv.sh
source venv/bin/activate

# 2. Buat struktur folder
python 01_setup_directories.py

# 3. Jalankan pada video pertama (untuk capture wajah)
python 07_main_system_video.py rekaman1.mp4 -o output1.mp4

# 4. Training model dengan wajah yang ter-capture
python 08_retrain_model.py
# Ikuti instruksi untuk beri nama setiap orang

# 5. Jalankan lagi, sekarang wajah sudah dikenali!
python 07_main_system_video.py rekaman2.mp4 -o output2.mp4
```

### Skenario 2: Menambah Wajah Baru
```bash
source venv/bin/activate

# 1. Jalankan sistem (akan auto-capture wajah baru)
python 07_main_system_video.py video_baru.mp4 -o output.mp4

# 2. Cek folder unknown
ls -l data/unknown/

# 3. Training ulang model
python 08_retrain_model.py
# Pilih opsi 1 untuk beri nama satu per satu

# 4. Sistem siap dengan wajah baru!
```

### Skenario 3: Presensi Ibadah Mingguan
```bash
source venv/bin/activate

# Setiap minggu:
python 07_main_system_video.py ibadah_minggu_21nov.mp4 -o hasil_21nov.mp4

# Cek hasil presensi
cat data/attendance.csv
# atau buka dengan Excel/LibreOffice
```

---

## ⚙️ Konfigurasi (modules/config.py)

### Parameter Penting
```python
# Deteksi
YOLO_CONFIDENCE = 0.5           # Threshold deteksi wajah (0.3-0.7)
FACE_RECOGNITION_THRESHOLD = 0.45  # Threshold pengenalan (0.4-0.6)

# Auto-capture
FRAMES_TO_CAPTURE = 15          # Jumlah foto per orang
CAPTURE_INTERVAL = 5            # Jarak antar capture (frames)
TRACK_SIMILARITY_THRESHOLD = 0.45  # Threshold tracking

# Presensi
ATTENDANCE_COOLDOWN = 3600      # Cooldown presensi (detik)
```

**Cara edit:** Buka file `config.py` dengan text editor

### Tuning Performance
- **Terlalu banyak false positive?** → Naikkan `YOLO_CONFIDENCE` atau `FACE_RECOGNITION_THRESHOLD` di `config.py`
- **Banyak yang tidak terdeteksi?** → Turunkan `YOLO_CONFIDENCE` di `config.py`
- **Capture terlalu sedikit?** → Naikkan `FRAMES_TO_CAPTURE` di `config.py`
- **Wajah tidak dikenali padahal sudah di-train?** → Turunkan `FACE_RECOGNITION_THRESHOLD` (coba 0.35-0.40)

---

## 🔍 Troubleshooting

### Problem: Wajah tidak terdeteksi
**Solusi:**
1. Turunkan `YOLO_CONFIDENCE` di `config.py` (coba 0.3 atau 0.4)
2. Pastikan pencahayaan video cukup baik
3. Pastikan resolusi video minimal 480p
4. Wajah harus menghadap kamera (tidak terlalu miring)

### Problem: Wajah terdeteksi tapi tidak dikenali
**Solusi:**
1. Turunkan `FACE_RECOGNITION_THRESHOLD` di `config.py` (coba 0.35 atau 0.40)
2. Jalankan ulang training: `python 08_retrain_model.py`
3. Tambah foto training - minimal 15 foto per orang dengan berbagai angle
4. Pastikan foto training berkualitas baik (tidak blur, pencahayaan cukup)

### Problem: Orang yang sama masuk ke folder berbeda
**Solusi:**
- Sudah ada tracking otomatis, seharusnya tidak terjadi lagi
- Jika masih terjadi, naikkan `TRACK_SIMILARITY_THRESHOLD`

### Problem: Video processing lambat
**Solusi:**
1. Gunakan opsi `--no-display` untuk tidak tampilkan preview
2. Turunkan FPS processing (edit code di 07_main_system_video.py)
3. Resize video ke resolusi lebih kecil (720p)

### Problem: Error "No module named..."
**Solusi:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Output Files

### 1. attendance.csv
Format CSV dengan kolom:
- Nama
- Waktu (timestamp)
- Tanggal
- Jam

### 2. face_encodings.pkl
Binary file berisi:
- Embeddings wajah (512-d vectors)
- Nama-nama orang terdaftar

### 3. Video Output
Video dengan:
- Bounding box wajah (hijau = dikenal, merah = unknown)
- Label nama di atas wajah
- FPS counter

---

## 🎓 Tips & Best Practices

### 1. Kualitas Foto Training
- **Minimal 15 foto** per orang
- **Variasi angle** (depan, kiri, kanan)
- **Variasi ekspresi** (normal, senyum)
- **Pencahayaan baik** (tidak gelap/backlight)
- **Fokus tajam** (tidak blur)

### 2. Video Processing
- **Resolusi optimal**: 720p-1080p
- **FPS**: 30-60 fps
- **Format**: MP4, AVI, MOV
- **Encoding**: H.264 recommended

### 3. Manajemen Dataset
- Hapus foto blur/gelap dari `data/faces/`
- Review folder `data/unknown/` secara berkala
- Backup `data/face_encodings.pkl` secara rutin
- Clean up `data/unknown/` setelah training

### 4. Optimasi Raspberry Pi
- Gunakan `--no-display` untuk hemat resource
- Process video offline, bukan real-time
- Gunakan Raspberry Pi 4 dengan 4GB+ RAM
- Overclock jika perlu (dengan cooling)

---

## 📞 Bantuan Lebih Lanjut

### File Dokumentasi
- `INSTALL.md` - Panduan instalasi detail
- `VIDEO_GUIDE.md` - Panduan khusus video processing
- `README.md` - Overview singkat

### Struktur Code
- Semua modul core: `config.py`, `face_*.py`, `attendance_manager.py`, `unknown_face_collector.py`
- Program utama: `07_*.py`, `08_*.py`, `09_*.py`
- Test scripts: `02_*.py` sampai `06_*.py` (opsional, untuk debugging)
- Setup scripts: `00_*.sh`, `01_*.py`

### Informasi Teknis
- Python: 3.8+
- YOLO Model: YOLOv8n-face
- ArcFace Model: buffalo_sc (InsightFace)
- Framework: OpenCV 4.8+, Ultralytics, ONNX Runtime

---

## ✅ Checklist Harian

Sebelum menjalankan sistem:
- [ ] Virtual environment aktif (`source venv/bin/activate`)
- [ ] File video sudah ada di folder
- [ ] Model sudah di-training (ada `data/face_encodings.pkl`)
- [ ] Folder output sudah disiapkan
- [ ] Cek space disk (minimal 1GB free)

Setelah processing:
- [ ] Cek `data/attendance.csv` untuk hasil presensi
- [ ] Review folder `data/unknown/` untuk wajah baru
- [ ] Backup attendance.csv jika perlu
- [ ] Training ulang jika ada wajah baru

---

**Versi:** 1.0  
**Terakhir Update:** 21 November 2025  
**Author:** Sistem Presensi GKI Karawaci
