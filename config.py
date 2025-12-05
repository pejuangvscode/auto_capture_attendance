"""
Konfigurasi untuk Sistem Presensi GKI Karawaci
"""

# Pengaturan Kamera
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30

# Pengaturan Deteksi Wajah (YOLO)
YOLO_MODEL = "yolov8n-face.pt"  # yolov8n-face = nano (paling ringan), yolov8s-face = small
FACE_DETECTION_THRESHOLD = 0.5  # Confidence threshold untuk deteksi YOLO
FACE_RECOGNITION_THRESHOLD = 0.42  # Cosine similarity threshold untuk ArcFace (0-1, semakin tinggi semakin strict)
MIN_FACE_SIZE = (50, 50)  # Ukuran minimum wajah yang dideteksi

# Pengaturan Pengambilan Data Wajah Baru
FRAMES_TO_CAPTURE = 5  # Jumlah frame untuk wajah tidak dikenali
CAPTURE_INTERVAL = 3  # Interval frame antara pengambilan (untuk variasi pose)
MIN_FRAMES_FOR_TRAINING = 1  # Minimum frame yang valid untuk training (minimal 1, tidak wajib 5)

# Pengaturan Model
ARCFACE_MODEL = "buffalo_sc"  # buffalo_sc (ringan), buffalo_l (akurat)
USE_GPU = False  # Set True jika ada GPU CUDA
EMBEDDING_SIZE = 512  # Ukuran embedding ArcFace

# Path File
DATA_DIR = "data"
FACES_DIR = f"{DATA_DIR}/faces"
UNKNOWN_DIR = f"{DATA_DIR}/unknown"
MODEL_FILE = f"{DATA_DIR}/face_encodings.pkl"
ATTENDANCE_FILE = f"{DATA_DIR}/attendance.csv"
LOG_FILE = f"{DATA_DIR}/system.log"

# Pengaturan Presensi
ATTENDANCE_COOLDOWN = 3600  # Cooldown dalam detik (1 jam) sebelum bisa absen lagi
DISPLAY_ATTENDANCE_DURATION = 3  # Durasi menampilkan notifikasi presensi (detik)

# Pengaturan UI
FONT_SCALE = 0.6
FONT_THICKNESS = 2
BOX_COLOR_KNOWN = (0, 255, 0)  # Hijau untuk wajah dikenali
BOX_COLOR_UNKNOWN = (0, 0, 255)  # Merah untuk wajah tidak dikenali
BOX_COLOR_CAPTURING = (255, 165, 0)  # Orange untuk sedang capture
TEXT_COLOR = (255, 255, 255)
