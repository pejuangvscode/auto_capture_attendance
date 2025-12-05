"""
YOLO Face Detector
Modul untuk deteksi wajah menggunakan YOLOv8
Lebih ringan dan akurasi tinggi untuk Raspberry Pi
"""

import cv2
import numpy as np
from ultralytics import YOLO
import config
import os

class YOLOFaceDetector:
    """Class untuk mendeteksi wajah menggunakan YOLO"""
    
    def __init__(self):
        model_path = os.path.join(config.DATA_DIR, config.YOLO_MODEL)
        
        # Download model jika belum ada
        if not os.path.exists(model_path):
            print(f"Downloading YOLO Face model ke {model_path}...")
            # Gunakan YOLOv8 face detection model
            # Model ini HANYA deteksi wajah, bukan body
            import urllib.request
            face_model_url = "https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8n-face.pt"
            try:
                urllib.request.urlretrieve(face_model_url, model_path)
                print("✓ YOLO Face model downloaded")
            except:
                print("⚠ Download gagal, gunakan YOLOv8n standard (class 0 = person)")
                self.model = YOLO('yolov8n.pt')
                self.use_person_class = True
                return
            
        self.model = YOLO(model_path)
        self.use_person_class = False
        print("✓ YOLO Face model loaded")
        
        self.conf_threshold = config.FACE_DETECTION_THRESHOLD
        self.min_face_size = config.MIN_FACE_SIZE
        
        # Untuk tracking wajah antar frame
        self.prev_faces = []
        
    def detect_faces(self, frame):
        """
        Deteksi wajah dalam frame menggunakan YOLO
        
        Args:
            frame: Frame BGR dari OpenCV
            
        Returns:
            List of face locations (top, right, bottom, left)
        """
        # YOLO inference
        results = self.model(frame, verbose=False, conf=self.conf_threshold)
        
        face_locations = []
        
        # Parse hasil deteksi
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                
                # Convert ke format (top, right, bottom, left)
                top = int(y1)
                right = int(x2)
                bottom = int(y2)
                left = int(x1)
                
                # Filter berdasarkan ukuran minimum
                width = right - left
                height = bottom - top
                
                if width >= self.min_face_size[0] and height >= self.min_face_size[1]:
                    face_locations.append((top, right, bottom, left))
        
        return face_locations
    
    def get_face_images(self, frame, face_locations):
        """
        Crop gambar wajah dari lokasi yang dideteksi
        
        Args:
            frame: Frame BGR dari OpenCV
            face_locations: List lokasi wajah
            
        Returns:
            List of cropped face images
        """
        face_images = []
        
        for (top, right, bottom, left) in face_locations:
            # Tambah margin sedikit
            margin = 10
            top = max(0, top - margin)
            left = max(0, left - margin)
            bottom = min(frame.shape[0], bottom + margin)
            right = min(frame.shape[1], right + margin)
            
            face_img = frame[top:bottom, left:right]
            face_images.append(face_img)
        
        return face_images
