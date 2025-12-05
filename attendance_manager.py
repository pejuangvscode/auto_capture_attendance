"""
Attendance Manager
Modul untuk mengelola data presensi (CSV + Supabase)
"""

import csv
import os
from datetime import datetime, timedelta
import config

# Import Supabase manager (optional, jika tidak ada akan skip)
try:
    from supabase_manager import SupabaseManager
    SUPABASE_ENABLED = True
except ImportError:
    SUPABASE_ENABLED = False
    print("⚠ Supabase manager tidak tersedia, hanya gunakan CSV")

class AttendanceManager:
    """Class untuk mengelola presensi"""
    
    def __init__(self, use_supabase=True):
        self.attendance_file = config.ATTENDANCE_FILE
        self.cooldown = config.ATTENDANCE_COOLDOWN
        self.last_attendance = {}  # {name: timestamp}
        self._initialize_file()
        
        # Initialize Supabase
        self.supabase = None
        if use_supabase and SUPABASE_ENABLED:
            try:
                self.supabase = SupabaseManager()
                print("✓ Supabase integration enabled")
            except Exception as e:
                print(f"⚠ Supabase initialization failed: {e}")
                print("  Akan gunakan CSV saja")
                self.supabase = None
    
    def _initialize_file(self):
        """Inisialisasi file CSV jika belum ada"""
        if not os.path.exists(self.attendance_file):
            with open(self.attendance_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Nama', 'Tanggal', 'Waktu', 'Confidence'])
    
    def mark_attendance(self, name, confidence):
        """
        Tandai kehadiran seseorang (simpan ke CSV + Supabase)
        
        Args:
            name: Nama orang
            confidence: Confidence score (0-1)
            
        Returns:
            True jika berhasil ditandai, False jika masih dalam cooldown
        """
        now = datetime.now()
        
        # Cek cooldown
        if name in self.last_attendance:
            time_diff = (now - self.last_attendance[name]).total_seconds()
            if time_diff < self.cooldown:
                remaining = int(self.cooldown - time_diff)
                print(f"⏳ {name} sudah absen. Cooldown: {remaining}s")
                return False
        
        # Catat presensi ke CSV
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        with open(self.attendance_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, date_str, time_str, f"{confidence:.3f}"])
        
        self.last_attendance[name] = now
        print(f"✓ Presensi tercatat (CSV): {name} pada {time_str}")
        
        # Simpan ke Supabase jika tersedia
        if self.supabase:
            try:
                success = self.supabase.save_kehadiran(name, waktu_presensi=now)
                if success:
                    print(f"✓ Presensi tersimpan ke Supabase: {name}")
                else:
                    print(f"⚠ Gagal simpan ke Supabase (tetap tersimpan di CSV)")
            except Exception as e:
                print(f"⚠ Error Supabase: {e} (tetap tersimpan di CSV)")
        
        return True
    
    def get_today_attendance(self):
        """Mendapatkan daftar yang sudah hadir hari ini"""
        today = datetime.now().strftime("%Y-%m-%d")
        attendees = []
        
        if not os.path.exists(self.attendance_file):
            return attendees
        
        with open(self.attendance_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Tanggal'] == today:
                    attendees.append({
                        'nama': row['Nama'],
                        'waktu': row['Waktu'],
                        'confidence': float(row['Confidence'])
                    })
        
        return attendees
    
    def get_attendance_stats(self, date=None):
        """
        Mendapatkan statistik presensi
        
        Args:
            date: Tanggal dalam format YYYY-MM-DD. None untuk hari ini.
            
        Returns:
            Dictionary dengan statistik
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        attendees = []
        
        if os.path.exists(self.attendance_file):
            with open(self.attendance_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Tanggal'] == date:
                        attendees.append(row['Nama'])
        
        unique_attendees = list(set(attendees))
        
        return {
            'date': date,
            'total_records': len(attendees),
            'unique_attendees': len(unique_attendees),
            'names': unique_attendees
        }
