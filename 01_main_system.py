"""
07 - Main System
Sistem utama presensi otomatis GKI Karawaci
Menggabungkan semua modul untuk sistem yang lengkap
Optimized dengan multi-threading untuk FPS lebih tinggi
"""

import cv2
import os
import time
from datetime import datetime
from threading import Thread, Lock
from queue import Queue
import config
from face_detector_yolo import YOLOFaceDetector
from face_recognizer_arcface import ArcFaceRecognizer
from attendance_manager import AttendanceManager
from unknown_face_collector import UnknownFaceCollector

class AttendanceSystem:
    """Sistem Presensi Otomatis - Optimized dengan Multi-Threading"""
    
    def __init__(self):
        print("=== Inisialisasi Sistem Presensi GKI Karawaci ===")
        print("Menggunakan YOLO + ArcFace (Multi-threaded Optimized)\n")
        
        # Inisialisasi komponen
        print("Loading YOLO detector...")
        self.detector = YOLOFaceDetector()
        print("✓ YOLO Face model loaded")
        
        print("Loading ArcFace recognizer...")
        self.recognizer = ArcFaceRecognizer()
        self.attendance_manager = AttendanceManager()
        self.unknown_collector = UnknownFaceCollector()
        
        # Load model
        print("Loading trained model...")
        if not self.recognizer.load_model():
            print("⚠ Model belum dilatih. Wajah akan di-capture sebagai 'Unknown'")
            print("  Jalankan 08_retrain_model.py untuk melatih model\n")
            self.model_loaded = False
        else:
            num_people = len(set(self.recognizer.known_names))
            print(f"✓ Model loaded: {num_people} orang dikenal\n")
            self.model_loaded = True
        
        # State
        self.unknown_tracking = {}  # Track wajah unknown per frame
        self.notification_queue = []  # Queue untuk notifikasi
        self.recently_captured = []  # Blacklist wajah yang baru selesai di-capture (cooldown 60 detik)
        
        # Threading untuk optimasi
        self.frame_queue = Queue(maxsize=2)  # Queue untuk frame dari kamera
        self.result_queue = Queue(maxsize=2)  # Queue untuk hasil deteksi
        self.attendance_queue = Queue()  # Queue untuk async attendance processing
        self.lock = Lock()
        self.stopped = False
        
        # Skip frame untuk optimasi (process setiap N frame)
        self.frame_skip = 2  # Process setiap 2 frame, skip 1 frame
        self.frame_counter = 0
        
        print("✓ Sistem siap dengan multi-threading!\n")
    
    def _draw_face_box(self, frame, face_location, name, confidence, status="recognized"):
        """Gambar kotak dan label di wajah - Modern & Clean UI"""
        top, right, bottom, left = face_location
        
        # Tentukan warna berdasarkan status (RGB format untuk lebih modern)
        if status == "recognized":
            color = (46, 204, 113)  # Green modern
            accent_color = (39, 174, 96)  # Darker green
        elif status == "capturing":
            color = (52, 152, 219)  # Blue modern
            accent_color = (41, 128, 185)  # Darker blue
        else:  # unknown
            color = (231, 76, 60)  # Red modern
            accent_color = (192, 57, 43)  # Darker red
        
        # Gambar bounding box tipis dengan corner highlights
        thickness = 1  # Garis tipis
        corner_length = 20  # Panjang corner highlight
        corner_thickness = 2  # Ketebalan corner
        
        # Corner top-left
        cv2.line(frame, (left, top), (left + corner_length, top), accent_color, corner_thickness)
        cv2.line(frame, (left, top), (left, top + corner_length), accent_color, corner_thickness)
        
        # Corner top-right
        cv2.line(frame, (right, top), (right - corner_length, top), accent_color, corner_thickness)
        cv2.line(frame, (right, top), (right, top + corner_length), accent_color, corner_thickness)
        
        # Corner bottom-left
        cv2.line(frame, (left, bottom), (left + corner_length, bottom), accent_color, corner_thickness)
        cv2.line(frame, (left, bottom), (left, bottom - corner_length), accent_color, corner_thickness)
        
        # Corner bottom-right
        cv2.line(frame, (right, bottom), (right - corner_length, bottom), accent_color, corner_thickness)
        cv2.line(frame, (right, bottom), (right, bottom - corner_length), accent_color, corner_thickness)
        
        # Bounding box utama (tipis)
        cv2.rectangle(frame, (left, top), (right, bottom), color, thickness)
        
        # Label dengan background semi-transparent modern
        if status == "capturing":
            label = f"Capturing: {name}"
            font_scale = 0.5
        elif name == "Unknown":
            label = "Unknown"
            font_scale = 0.5
        else:
            label = f"{name}"
            font_scale = 0.6
        
        # Hitung ukuran text
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1
        )
        
        # Background dengan rounded corners effect (semi-transparent)
        padding = 8
        label_top = top - text_height - padding * 2 - 5
        if label_top < 0:
            label_top = bottom + 5
        
        # Background dengan opacity
        overlay = frame.copy()
        cv2.rectangle(
            overlay, 
            (left, label_top), 
            (left + text_width + padding * 2, label_top + text_height + padding * 2),
            accent_color, 
            -1
        )
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        
        # Text putih bersih
        cv2.putText(
            frame, 
            label, 
            (left + padding, label_top + text_height + padding),
            cv2.FONT_HERSHEY_SIMPLEX, 
            font_scale, 
            (255, 255, 255),  # White text
            1,  # Thickness 1 untuk clean look
            cv2.LINE_AA  # Anti-aliased
        )
    
    def _draw_notifications(self, frame):
        """Gambar notifikasi di layar - DISABLED untuk clean UI"""
        # Notifikasi disabled untuk UI yang lebih clean
        pass
    
    def _add_notification(self, text, color=(0, 255, 0)):
        """Tambah notifikasi"""
        self.notification_queue.append({
            'text': text,
            'color': color,
            'time': time.time()
        })
    
    def _process_recognized_face(self, name, confidence):
        """Proses wajah yang dikenali - async untuk menghindari freeze"""
        # Kirim ke queue untuk diproses di background thread
        self.attendance_queue.put((name, confidence))
    
    def _attendance_worker(self):
        """Background worker untuk process attendance tanpa blocking UI"""
        processed_recently = {}  # Cache untuk avoid duplicate dalam waktu dekat
        cooldown = 5  # seconds
        
        while not self.stopped:
            try:
                # Ambil dari queue dengan timeout
                name, confidence = self.attendance_queue.get(timeout=1)
                
                current_time = time.time()
                
                # Cek apakah baru saja diproses (dalam 5 detik terakhir)
                if name in processed_recently:
                    last_time = processed_recently[name]
                    if current_time - last_time < cooldown:
                        continue  # Skip, baru saja diproses
                
                # Process attendance (blocking operation, tapi di background thread)
                if self.attendance_manager.mark_attendance(name, confidence):
                    print(f"✓ Kehadiran tercatat: {name}")
                
                # Update cache
                processed_recently[name] = current_time
                
                # Cleanup cache lama
                to_remove = [k for k, v in processed_recently.items() 
                           if current_time - v > cooldown * 2]
                for k in to_remove:
                    del processed_recently[k]
                
            except:
                # Queue kosong atau timeout, lanjutkan
                continue
    
    def _process_unknown_face(self, frame, face_location):
        """Proses wajah yang tidak dikenali"""
        top, right, bottom, left = face_location
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        
        # Cek apakah wajah ini baru saja di-capture (dalam cooldown)
        current_time = time.time()
        for captured_data in self.recently_captured[:]:  # Copy list untuk iterasi aman
            captured_x, captured_y, capture_time = captured_data
            # Hapus dari blacklist jika sudah lewat 60 detik
            if current_time - capture_time > 60:
                self.recently_captured.remove(captured_data)
                continue
            
            # Cek jarak dengan wajah yang baru di-capture
            distance = ((center_x - captured_x)**2 + (center_y - captured_y)**2)**0.5
            if distance < 80:  # Wajah yang sama dalam cooldown
                return "SKIP"  # Skip capture untuk wajah ini
        
        # Cari tracking terdekat (dalam radius 80 pixel)
        closest_key = None
        min_distance = 80  # threshold jarak
        
        for key, data in self.unknown_tracking.items():
            old_x, old_y = map(int, key.split('_'))
            distance = ((center_x - old_x)**2 + (center_y - old_y)**2)**0.5
            if distance < min_distance:
                min_distance = distance
                closest_key = key
        
        # Gunakan tracking yang ada atau buat baru
        if closest_key:
            location_key = closest_key
            tracking_data = self.unknown_tracking[location_key]
            person_id = tracking_data['person_id']
            tracking_data['last_seen'] = time.time()
        else:
            # Mulai capture baru
            location_key = f"{center_x}_{center_y}"
            person_id = self.unknown_collector.start_capture()
            self.unknown_tracking[location_key] = {
                'person_id': person_id,
                'last_seen': time.time()
            }
        
        # Tambah frame
        self.unknown_collector.add_frame(person_id, frame, face_location)
        
        # Cek jika capture selesai
        if self.unknown_collector.is_capture_complete(person_id):
            save_path = self.unknown_collector.save_captured_faces(person_id)
            if save_path:
                self._add_notification("Capture selesai! Silakan latih ulang model", (0, 255, 255))
                print(f"\n✓ Wajah baru tersimpan: {save_path}")
                print("  Jalankan 08_retrain_model.py untuk melatih ulang model\n")
                
                # Tambahkan ke blacklist dengan cooldown 60 detik
                self.recently_captured.append((center_x, center_y, current_time))
            
            # Hapus dari tracking
            del self.unknown_tracking[location_key]
            return None
        
        # Return progress untuk ditampilkan
        current, total, percentage = self.unknown_collector.get_capture_progress(person_id)
        return f"{current}/{total}"
    
    def _cleanup_old_tracking(self):
        """Bersihkan tracking yang sudah lama tidak terlihat"""
        current_time = time.time()
        timeout = 3  # 3 detik
        
        to_remove = []
        for location_key, data in self.unknown_tracking.items():
            if current_time - data['last_seen'] > timeout:
                # Cancel capture
                self.unknown_collector.cancel_capture(data['person_id'])
                to_remove.append(location_key)
        
        for key in to_remove:
            del self.unknown_tracking[key]
    
    def _capture_frames(self, cap):
        """Thread untuk capture frame dari kamera"""
        while not self.stopped:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Resize frame untuk processing lebih cepat (opsional)
            # Uncomment jika perlu lebih cepat lagi
            # frame = cv2.resize(frame, (640, 480))
            
            if not self.frame_queue.full():
                self.frame_queue.put(frame)
    
    def _process_faces(self):
        """Thread untuk deteksi dan recognisi wajah"""
        last_processed_results = []  # Cache hasil terakhir
        
        while not self.stopped:
            if self.frame_queue.empty():
                time.sleep(0.001)
                continue
            
            frame = self.frame_queue.get()
            
            # Skip frame untuk optimasi
            self.frame_counter += 1
            if self.frame_counter % self.frame_skip != 0:
                # Skip processing, gunakan hasil terakhir
                if not self.result_queue.full():
                    self.result_queue.put((frame, last_processed_results))
                continue
            
            # Deteksi wajah
            face_locations = self.detector.detect_faces(frame)
            
            # Process hasil deteksi
            results = []
            if len(face_locations) > 0:
                for face_location in face_locations:
                    result = {'location': face_location}
                    
                    if self.model_loaded:
                        # Recognize wajah
                        name, confidence = self.recognizer.recognize_face(frame, bbox=face_location)
                        result['name'] = name
                        result['confidence'] = confidence
                        
                        if name != "Unknown":
                            result['status'] = 'recognized'
                            # Process attendance di thread utama
                        else:
                            result['status'] = 'unknown'
                    else:
                        result['name'] = "Unknown"
                        result['confidence'] = 0
                        result['status'] = 'unknown'
                    
                    results.append(result)
            
            # Simpan hasil untuk digunakan di frame yang di-skip
            last_processed_results = results
            
            # Kirim hasil ke main thread
            if not self.result_queue.full():
                self.result_queue.put((frame, results))
    
    def run(self):
        """Jalankan sistem dengan multi-threading"""
        print("Sistem berjalan dengan multi-threading...")
        print("Tekan 'q' untuk keluar")
        print("Tekan 's' untuk melihat statistik hari ini")
        print("Tekan 'f' untuk toggle fullscreen")
        print("Tekan '+' untuk kurangi skip (lebih akurat, lebih lambat)")
        print("Tekan '-' untuk tambah skip (lebih cepat, kurang akurat)\n")
        
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer lag
        
        # Setup window dengan fullscreen
        window_name = 'GKI Karawaci - Attendance System'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        self.is_fullscreen = True
        
        # Start threads
        capture_thread = Thread(target=self._capture_frames, args=(cap,), daemon=True)
        process_thread = Thread(target=self._process_faces, daemon=True)
        attendance_thread = Thread(target=self._attendance_worker, daemon=True)
        
        capture_thread.start()
        process_thread.start()
        attendance_thread.start()
        
        frame_count = 0
        fps_time = time.time()
        fps = 0
        last_results = []
        
        while True:
            # Ambil hasil dari queue
            if not self.result_queue.empty():
                frame, results = self.result_queue.get()
                last_results = results
            else:
                # Jika tidak ada hasil baru, skip
                time.sleep(0.001)
                continue
            
            # Hitung FPS
            frame_count += 1
            if frame_count % 10 == 0:
                current_time = time.time()
                fps = 10 / (current_time - fps_time)
                fps_time = current_time
            
            # Draw hasil
            for result in last_results:
                face_location = result['location']
                name = result['name']
                confidence = result.get('confidence', 0)
                status = result.get('status', 'unknown')
                
                if status == 'recognized':
                    self._draw_face_box(frame, face_location, name, confidence, "recognized")
                    # Kirim ke attendance queue (non-blocking)
                    self._process_recognized_face(name, confidence)
                else:
                    # Process unknown face
                    with self.lock:
                        progress = self._process_unknown_face(frame, face_location)
                    
                    if progress == "SKIP":
                        self._draw_face_box(frame, face_location, "Already Captured", 0, "unknown")
                    elif progress:
                        self._draw_face_box(frame, face_location, progress, 0, "capturing")
                    else:
                        self._draw_face_box(frame, face_location, "Unknown", 0, "unknown")
            
            # Cleanup tracking lama
            with self.lock:
                self._cleanup_old_tracking()
            
            # Clean UI - No system info displayed
            
            # Tampilkan frame
            cv2.imshow(window_name, frame)
            
            # Handle keyboard
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                self._show_statistics()
            elif key == ord('f'):
                # Toggle fullscreen
                self.is_fullscreen = not self.is_fullscreen
                if self.is_fullscreen:
                    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                    print("Fullscreen: ON")
                else:
                    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                    print("Fullscreen: OFF")
            elif key == ord('+') or key == ord('='):
                # Kurangi skip untuk lebih akurat
                self.frame_skip = max(1, self.frame_skip - 1)
                print(f"Frame skip: {self.frame_skip}")
            elif key == ord('-') or key == ord('_'):
                # Tambah skip untuk lebih cepat
                self.frame_skip = min(5, self.frame_skip + 1)
                print(f"Frame skip: {self.frame_skip}")
        
        # Stop threads
        self.stopped = True
        capture_thread.join(timeout=1)
        process_thread.join(timeout=1)
        attendance_thread.join(timeout=1)
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n✓ Sistem berhenti")
    
    def _show_statistics(self):
        """Tampilkan statistik presensi hari ini"""
        print("\n" + "="*50)
        print("STATISTIK PRESENSI HARI INI")
        print("="*50)
        
        stats = self.attendance_manager.get_attendance_stats()
        print(f"Tanggal: {stats['date']}")
        print(f"Total kehadiran: {stats['unique_attendees']} orang")
        print(f"Total records: {stats['total_records']}")
        
        if stats['names']:
            print("\nDaftar Hadir:")
            for idx, name in enumerate(stats['names'], 1):
                print(f"  {idx}. {name}")
        
        print("="*50 + "\n")

# Main program
if __name__ == "__main__":
    try:
        system = AttendanceSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\n✓ Program dihentikan oleh user")
    except Exception as e:
        print(f"\n⚠ Error: {e}")
        import traceback
        traceback.print_exc()
