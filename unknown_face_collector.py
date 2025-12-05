"""
Unknown Face Collector
Modul untuk mengumpulkan frame wajah yang tidak dikenali
untuk nantinya dilatih
"""

import cv2
import os
from datetime import datetime
from pathlib import Path
import config

class UnknownFaceCollector:
    """Class untuk mengumpulkan wajah yang tidak dikenali"""
    
    def __init__(self):
        self.unknown_dir = config.UNKNOWN_DIR
        self.frames_to_capture = config.FRAMES_TO_CAPTURE
        self.capture_interval = config.CAPTURE_INTERVAL
        self.min_frames = config.MIN_FRAMES_FOR_TRAINING
        
        # State untuk setiap wajah yang sedang di-capture
        self.active_captures = {}  # {person_id: {'frames': [], 'count': 0, 'interval_counter': 0}}
        self.next_person_id = 0
        
    def start_capture(self, person_id=None):
        """
        Mulai capture untuk wajah baru
        
        Args:
            person_id: ID unik untuk orang ini. Jika None, akan auto-generate
            
        Returns:
            person_id yang digunakan
        """
        if person_id is None:
            person_id = f"unknown_{self.next_person_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.next_person_id += 1
        
        self.active_captures[person_id] = {
            'frames': [],
            'count': 0,
            'interval_counter': 0,
            'session_dir': None
        }
        
        return person_id
    
    def add_frame(self, person_id, frame, face_location):
        """
        Tambahkan frame untuk person_id tertentu
        
        Args:
            person_id: ID orang yang sedang di-capture
            frame: Frame dari kamera
            face_location: Lokasi wajah (top, right, bottom, left)
            
        Returns:
            True jika frame ditambahkan, False jika skip (interval)
        """
        if person_id not in self.active_captures:
            return False
        
        capture_data = self.active_captures[person_id]
        
        # Cek interval
        capture_data['interval_counter'] += 1
        if capture_data['interval_counter'] < self.capture_interval:
            return False
        
        # Reset interval counter
        capture_data['interval_counter'] = 0
        
        # Crop wajah dari frame (dengan margin lebih besar untuk training)
        top, right, bottom, left = face_location
        
        # Pastikan koordinat dalam bounds
        height, width = frame.shape[:2]
        
        # Convert to int and ensure within bounds
        top = max(0, int(top))
        left = max(0, int(left))
        bottom = min(height, int(bottom))
        right = min(width, int(right))
        
        # Crop face dengan margin 20% untuk memastikan wajah terdeteksi saat training
        # Margin lebih besar dari saat display supaya ArcFace bisa deteksi
        face_height = bottom - top
        face_width = right - left
        margin_v = int(face_height * 0.20)
        margin_h = int(face_width * 0.20)
        
        top = max(0, top - margin_v)
        left = max(0, left - margin_h)
        bottom = min(height, bottom + margin_v)
        right = min(width, right + margin_h)
        
        # Crop face
        face_image = frame[top:bottom, left:right].copy()
        
        # Resize ke ukuran minimum 112x112 (requirement ArcFace)
        if face_image.shape[0] < 112 or face_image.shape[1] < 112:
            import cv2
            # Maintain aspect ratio, scale to minimum 112
            scale = max(112 / face_image.shape[0], 112 / face_image.shape[1])
            new_width = int(face_image.shape[1] * scale)
            new_height = int(face_image.shape[0] * scale)
            face_image = cv2.resize(face_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Tambahkan ke list
        capture_data['frames'].append(face_image)
        capture_data['count'] += 1
        
        return True
    
    def is_capture_complete(self, person_id):
        """Cek apakah capture sudah selesai"""
        if person_id not in self.active_captures:
            return False
        
        return self.active_captures[person_id]['count'] >= self.frames_to_capture
    
    def get_capture_progress(self, person_id):
        """
        Mendapatkan progress capture
        
        Returns:
            (current_count, total_needed, percentage)
        """
        if person_id not in self.active_captures:
            return (0, self.frames_to_capture, 0.0)
        
        count = self.active_captures[person_id]['count']
        percentage = (count / self.frames_to_capture) * 100
        
        return (count, self.frames_to_capture, percentage)
    
    def save_captured_faces(self, person_id, name=None):
        """
        Simpan wajah yang sudah di-capture
        
        Args:
            person_id: ID orang yang di-capture
            name: Nama untuk folder (opsional, default pakai person_id)
            
        Returns:
            Path ke folder yang berisi wajah, atau None jika gagal
        """
        if person_id not in self.active_captures:
            return None
        
        capture_data = self.active_captures[person_id]
        
        # Cek minimum frames
        if capture_data['count'] < self.min_frames:
            print(f"⚠ Tidak cukup frame: {capture_data['count']}/{self.min_frames}")
            return None
        
        # Buat folder
        if name is None:
            name = person_id
        
        session_dir = os.path.join(self.unknown_dir, name)
        os.makedirs(session_dir, exist_ok=True)
        
        # Simpan semua frame
        for idx, face_image in enumerate(capture_data['frames']):
            filename = f"face_{idx:03d}.jpg"
            filepath = os.path.join(session_dir, filename)
            cv2.imwrite(filepath, face_image)
        
        capture_data['session_dir'] = session_dir
        
        print(f"✓ {capture_data['count']} frame disimpan ke: {session_dir}")
        
        return session_dir
    
    def cancel_capture(self, person_id):
        """Batalkan capture untuk person_id"""
        if person_id in self.active_captures:
            del self.active_captures[person_id]
    
    def get_active_captures(self):
        """Mendapatkan list person_id yang sedang di-capture"""
        return list(self.active_captures.keys())
