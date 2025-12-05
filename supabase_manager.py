"""
Supabase Database Manager
Mengelola koneksi dan operasi database ke Supabase
"""

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

class SupabaseManager:
    """Class untuk mengelola koneksi dan operasi database Supabase"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL tidak ditemukan di .env file")
        
        # Ganti [YOUR-PASSWORD] dengan password dari .env
        db_password = os.getenv('DB_PASSWORD', '')
        if db_password:
            self.database_url = self.database_url.replace('[YOUR-PASSWORD]', db_password)
        
        # Connection pool untuk performa lebih baik
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=self.database_url
            )
            print("✓ Supabase connection pool created")
        except Exception as e:
            print(f"✗ Error creating connection pool: {e}")
            self.pool = None
        
        # Cache untuk ibadah hari ini
        self.today_ibadah_id = None
    
    def get_connection(self):
        """Mendapatkan koneksi dari pool"""
        if self.pool:
            return self.pool.getconn()
        return None
    
    def return_connection(self, conn):
        """Mengembalikan koneksi ke pool"""
        if self.pool and conn:
            self.pool.putconn(conn)
    
    def get_or_create_ibadah_today(self):
        """
        Mendapatkan atau membuat Ibadah untuk hari ini
        
        Returns:
            id_ibadah atau None jika gagal
        """
        # Return cached jika sudah ada
        if self.today_ibadah_id:
            return self.today_ibadah_id
        
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cur = conn.cursor()
            
            # Ambil konfigurasi dari .env
            jenis_kebaktian = os.getenv('JENIS_KEBAKTIAN', 'Minggu Pagi')
            sesi_ibadah = int(os.getenv('SESI_IBADAH', '1'))
            today = datetime.now().date()
            
            # Cari ibadah untuk hari ini
            cur.execute("""
                SELECT id_ibadah FROM "Ibadah" 
                WHERE DATE(tanggal_ibadah) = %s 
                AND jenis_kebaktian = %s 
                AND sesi_ibadah = %s
                LIMIT 1
            """, (today, jenis_kebaktian, sesi_ibadah))
            
            result = cur.fetchone()
            
            if result:
                self.today_ibadah_id = result[0]
                print(f"  ✓ Ibadah ditemukan: {jenis_kebaktian} Sesi {sesi_ibadah} - {today}")
            else:
                # Buat ibadah baru untuk hari ini
                self.today_ibadah_id = str(uuid.uuid4())
                
                cur.execute("""
                    INSERT INTO "Ibadah" 
                    (id_ibadah, jenis_kebaktian, sesi_ibadah, tanggal_ibadah)
                    VALUES (%s, %s, %s, %s)
                """, (
                    self.today_ibadah_id,
                    jenis_kebaktian,
                    sesi_ibadah,
                    datetime.now()
                ))
                
                conn.commit()
                print(f"  ✓ Ibadah baru dibuat: {jenis_kebaktian} Sesi {sesi_ibadah} - {today}")
                print(f"     ID: {self.today_ibadah_id}")
            
            cur.close()
            return self.today_ibadah_id
            
        except Exception as e:
            print(f"  ✗ Error get_or_create_ibadah_today: {e}")
            conn.rollback()
            return None
        finally:
            self.return_connection(conn)
    
    def get_user_by_name(self, name):
        """
        Mencari user berdasarkan nama di tabel User
        
        Args:
            name: Nama user (dari face recognition)
            
        Returns:
            user_id (as string) atau None jika tidak ditemukan
        """
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cur = conn.cursor()
            
            # Cari user berdasarkan nama (case-insensitive)
            cur.execute("""
                SELECT user_id FROM "User" 
                WHERE LOWER(nama) = LOWER(%s)
                LIMIT 1
            """, (name,))
            
            result = cur.fetchone()
            cur.close()
            
            if result:
                user_id = str(result[0])  # Convert ke string untuk compatibility dengan schema
                print(f"  ✓ User ditemukan: {name} (user_id: {user_id})")
                return user_id
            else:
                print(f"  ⚠ User tidak ditemukan di database: {name}")
                print(f"     Pastikan user sudah terdaftar di tabel User")
                return None
            
        except Exception as e:
            print(f"  ✗ Error get_user_by_name: {e}")
            return None
        finally:
            self.return_connection(conn)
    
    def get_jemaat_by_name(self, name):
        """
        Cari Jemaat berdasarkan name (case-insensitive).
        
        Args:
            name: Nama jemaat
            
        Returns:
            id_jemaat jika ditemukan, None jika tidak ada
        """
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cur = conn.cursor()
            
            # Query Jemaat berdasarkan name
            cur.execute("""
                SELECT id_jemaat FROM "Jemaat" 
                WHERE LOWER(name) = LOWER(%s) 
                LIMIT 1
            """, (name,))
            
            result = cur.fetchone()
            cur.close()
            
            if result:
                id_jemaat = result[0]
                print(f"  ✓ Jemaat ditemukan: {name} (ID: {id_jemaat})")
                return id_jemaat
            else:
                print(f"  ✗ Jemaat tidak ditemukan: {name}")
                return None
            
        except Exception as e:
            print(f"  ✗ Error get_jemaat_by_name: {e}")
            return None
        finally:
            self.return_connection(conn)
    
    def save_kehadiran(self, name, waktu_presensi=None):
        """
        Menyimpan kehadiran ke database Supabase
        Workflow: Auto-create Ibadah hari ini → Sync User→Jemaat → Save Kehadiran
        
        Args:
            name: Nama user (dari face recognition)
            waktu_presensi: Waktu presensi (optional, default sekarang)
            
        Returns:
            True jika berhasil, False jika gagal
        """
        # Gunakan waktu sekarang jika tidak disediakan
        if not waktu_presensi:
            waktu_presensi = datetime.now()
        
        # 1. Get atau buat Ibadah untuk hari ini
        id_ibadah = self.get_or_create_ibadah_today()
        if not id_ibadah:
            print("  ✗ Gagal mendapatkan/membuat Ibadah")
            return False
        
        # 2. Cari Jemaat berdasarkan name
        id_jemaat = self.get_jemaat_by_name(name)
        
        if not id_jemaat:
            print(f"  ✗ Jemaat tidak ditemukan untuk: {name}")
            return False
        
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cur = conn.cursor()
            
            # Cek apakah sudah ada kehadiran untuk ibadah ini
            cur.execute("""
                SELECT id_kehadiran FROM "Kehadiran" 
                WHERE id_ibadah = %s AND id_jemaat = %s
            """, (id_ibadah, id_jemaat))
            
            result = cur.fetchone()
            
            if result:
                # Update waktu presensi jika sudah ada
                cur.execute("""
                    UPDATE "Kehadiran"
                    SET waktu_presensi = %s, status = 'Hadir', name = %s
                    WHERE id_kehadiran = %s
                """, (waktu_presensi, name, result[0]))
                
                print(f"  ✓ Kehadiran diupdate: {name} pada {waktu_presensi.strftime('%H:%M:%S')}")
            else:
                # Insert kehadiran baru
                id_kehadiran = str(uuid.uuid4())
                
                cur.execute("""
                    INSERT INTO "Kehadiran"
                    (id_kehadiran, id_ibadah, id_jemaat, waktu_presensi, status, name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    id_kehadiran,
                    id_ibadah,
                    id_jemaat,
                    waktu_presensi,
                    'Hadir',
                    name
                ))
                
                print(f"  ✓ Kehadiran baru disimpan: {name} pada {waktu_presensi.strftime('%H:%M:%S')}")
            
            conn.commit()
            cur.close()
            return True
            
        except Exception as e:
            print(f"  ✗ Error save_kehadiran: {e}")
            conn.rollback()
            return False
        finally:
            self.return_connection(conn)
    
    def get_kehadiran_hari_ini(self, id_ibadah=None):
        """
        Mendapatkan daftar kehadiran hari ini
        
        Args:
            id_ibadah: ID ibadah (optional)
            
        Returns:
            List of (name, waktu_presensi) tuples
        """
        if not id_ibadah:
            id_ibadah = os.getenv('IBADAH_ID', 'default-ibadah-id')
        
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cur = conn.cursor()
            
            # Ambil kehadiran untuk ibadah ini
            cur.execute("""
                SELECT k.name, k.waktu_presensi
                FROM "Kehadiran" k
                WHERE k.id_ibadah = %s AND k.status = 'Hadir'
                ORDER BY k.waktu_presensi DESC
            """, (id_ibadah,))
            
            results = cur.fetchall()
            cur.close()
            
            return results
            
        except Exception as e:
            print(f"  ✗ Error get_kehadiran_hari_ini: {e}")
            return []
        finally:
            self.return_connection(conn)
    
    def close(self):
        """Menutup semua koneksi dalam pool"""
        if self.pool:
            self.pool.closeall()
            print("✓ Connection pool closed")
