"""
ArcFace Recognizer
Modul untuk mengenali wajah dari embedding yang sudah dilatih
Menggunakan cosine similarity untuk perbandingan
"""

import numpy as np
import config
from face_encoder_arcface import ArcFaceEncoder

class ArcFaceRecognizer:
    """Class untuk mengenali wajah menggunakan ArcFace"""
    
    def __init__(self):
        self.encoder = ArcFaceEncoder()
        self.known_embeddings = []
        self.known_names = []
        self.threshold = config.FACE_RECOGNITION_THRESHOLD
        
    def load_model(self, filepath=config.MODEL_FILE):
        """Load model yang sudah dilatih"""
        self.known_embeddings, self.known_names = self.encoder.load_encodings(filepath)
        return len(self.known_embeddings) > 0
    
    def cosine_similarity(self, embedding1, embedding2):
        """
        Hitung cosine similarity antara dua embedding
        
        Returns:
            Similarity score (0-1, semakin tinggi semakin mirip)
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        similarity = dot_product / (norm1 * norm2)
        return similarity
    
    def recognize_face(self, face_img, bbox=None):
        """
        Mengenali satu wajah dari gambar
        
        Args:
            face_img: Full frame (BGR format) atau cropped face
            bbox: Optional (top, right, bottom, left) - jika provided, akan di-crop dari face_img
            
        Returns:
            (name, confidence) tuple
        """
        if len(self.known_embeddings) == 0:
            return ("Unknown", 0.0)
        
        # Jika ada bbox, crop dari frame
        if bbox is not None:
            top, right, bottom, left = bbox
            h, w = face_img.shape[:2]
            # Expand crop untuk detection yang lebih baik (30% padding)
            margin_y = int((bottom - top) * 0.3)
            margin_x = int((right - left) * 0.3)
            
            exp_top = max(0, top - margin_y)
            exp_bottom = min(h, bottom + margin_y)
            exp_left = max(0, left - margin_x)
            exp_right = min(w, right + margin_x)
            
            face_crop = face_img[exp_top:exp_bottom, exp_left:exp_right].copy()
        else:
            face_crop = face_img
        
        # Get embedding (skip_detection=False, biarkan InsightFace detect ulang)
        embedding = self.encoder.get_embedding(face_crop, skip_detection=False)
        
        if embedding is None:
            return ("Unknown", 0.0)
        
        # Hitung similarity dengan semua wajah yang dikenal
        similarities = []
        for known_embedding in self.known_embeddings:
            sim = self.cosine_similarity(embedding, known_embedding)
            similarities.append(sim)
        
        # Cari yang paling mirip
        best_match_idx = np.argmax(similarities)
        best_similarity = similarities[best_match_idx]
        
        # Cek threshold - cosine similarity langsung (0-1, semakin tinggi semakin mirip)
        # Threshold adalah minimum similarity yang diterima
        if best_similarity >= self.threshold:
            name = self.known_names[best_match_idx]
            confidence = best_similarity
        else:
            name = "Unknown"
            confidence = best_similarity  # Tetap return similarity untuk debugging
        
        return (name, confidence)
    
    def recognize_faces(self, face_images):
        """
        Mengenali multiple wajah
        
        Args:
            face_images: List of face images (BGR format)
            
        Returns:
            List of (name, confidence) tuples
        """
        results = []
        for face_img in face_images:
            result = self.recognize_face(face_img)
            results.append(result)
        
        return results
    
    def get_person_count(self):
        """Mendapatkan jumlah orang yang dikenal"""
        return len(set(self.known_names))
