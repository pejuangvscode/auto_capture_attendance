"""
ArcFace Encoder
Modul untuk membuat dan menyimpan embedding wajah menggunakan ArcFace
ArcFace lebih ringan dan akurat dibanding face_recognition
"""

import cv2
import numpy as np
import pickle
import os
from pathlib import Path
import config
from insightface.app import FaceAnalysis

class ArcFaceEncoder:
    """Class untuk encoding wajah menggunakan ArcFace dari InsightFace"""
    
    def __init__(self):
        print("Loading ArcFace model...")
        self.app = FaceAnalysis(
            name=config.ARCFACE_MODEL,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] if config.USE_GPU else ['CPUExecutionProvider']
        )
        self.app.prepare(ctx_id=0 if config.USE_GPU else -1, det_size=(640, 640))
        print("✓ ArcFace model loaded")
        
        self.known_embeddings = []
        self.known_names = []
        
    def get_embedding(self, face_img, skip_detection=False):
        """
        Mendapatkan embedding dari gambar wajah
        
        Args:
            face_img: Gambar wajah (BGR format)
            skip_detection: Jika True, gambar sudah di-crop wajah dari detector lain (YOLO)
            
        Returns:
            Embedding vector (512-d) atau None jika tidak ada wajah
        """
        # Convert BGR to RGB
        rgb_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        
        if skip_detection:
            # Gambar sudah di-crop dari YOLO
            # Strategy: Add padding dan resize ke ukuran yang lebih besar
            h, w = rgb_img.shape[:2]
            
            # Add padding untuk memberi context (15% di setiap sisi)
            padding_h = int(h * 0.15)
            padding_w = int(w * 0.15)
            
            # Add border dengan replicate (copy edge pixels)
            rgb_img = cv2.copyMakeBorder(
                rgb_img,
                padding_h, padding_h,  # top, bottom
                padding_w, padding_w,  # left, right
                cv2.BORDER_REPLICATE
            )
            
            # Update dimensions after padding
            h, w = rgb_img.shape[:2]
            
            # Resize ke target size yang lebih besar untuk detection yang lebih baik
            target_size = 640  # Ukuran lebih besar = detection lebih baik
            if h < target_size or w < target_size:
                scale = max(target_size / h, target_size / w)
                new_h, new_w = int(h * scale), int(w * scale)
                rgb_img = cv2.resize(rgb_img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
        # Detect and get embedding
        faces = self.app.get(rgb_img)
        
        if len(faces) == 0:
            return None
        
        # Ambil wajah dengan confidence tertinggi
        face = max(faces, key=lambda x: x.det_score)
        
        # Flatten untuk konsistensi dimensi
        return face.embedding.flatten()
    
    def encode_faces_from_directory(self, directory=config.FACES_DIR):
        """
        Encode semua wajah dari direktori
        
        Struktur direktori:
        faces/
            nama_orang_1/
                foto1.jpg
                foto2.jpg
            nama_orang_2/
                foto1.jpg
        
        Args:
            directory: Path ke direktori yang berisi folder per orang
        """
        print(f"Memproses wajah dari: {directory}\n")
        
        known_embeddings = []
        known_names = []
        
        # Iterasi setiap folder (setiap orang)
        for person_dir in Path(directory).iterdir():
            if not person_dir.is_dir():
                continue
                
            person_name = person_dir.name
            print(f"Memproses: {person_name}")
            
            image_count = 0
            encoding_count = 0
            
            # Iterasi setiap foto dalam folder orang tersebut
            # Support multiple image formats
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
            image_files = []
            for ext in image_extensions:
                image_files.extend(person_dir.glob(ext))
            
            for image_path in image_files:
                image_count += 1
                
                # Load gambar
                image = cv2.imread(str(image_path))
                
                if image is None:
                    print(f"  ⚠ Gagal membaca {image_path.name}")
                    continue
                
                # Get embedding - skip detection karena gambar sudah di-crop wajah
                embedding = self.get_embedding(image, skip_detection=True)
                
                if embedding is not None:
                    known_embeddings.append(embedding)
                    known_names.append(person_name)
                    encoding_count += 1
                else:
                    print(f"  ⚠ Tidak ada wajah terdeteksi di {image_path.name}")
            
            print(f"  ✓ {encoding_count}/{image_count} gambar berhasil diencode\n")
        
        self.known_embeddings = known_embeddings
        self.known_names = known_names
        
        print(f"Total: {len(known_embeddings)} embedding dari {len(set(known_names))} orang")
        return known_embeddings, known_names
    
    def save_encodings(self, filepath=config.MODEL_FILE):
        """Simpan embeddings ke file"""
        data = {
            "embeddings": self.known_embeddings,
            "names": self.known_names
        }
        
        with open(filepath, "wb") as f:
            pickle.dump(data, f)
        
        print(f"\n✓ Embeddings disimpan ke: {filepath}")
    
    def load_encodings(self, filepath=config.MODEL_FILE):
        """Load embeddings dari file"""
        if not os.path.exists(filepath):
            print(f"⚠ File {filepath} tidak ditemukan")
            return [], []
        
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        
        self.known_embeddings = data["embeddings"]
        self.known_names = data["names"]
        
        print(f"✓ Loaded {len(self.known_embeddings)} embeddings dari {filepath}")
        return self.known_embeddings, self.known_names
