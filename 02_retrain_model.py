"""
08 - Retrain Model
Script untuk melatih ulang model dengan wajah baru yang sudah di-capture
"""

import os
import shutil
from pathlib import Path
import config
from face_encoder_arcface import ArcFaceEncoder
from datetime import datetime
import uuid

# Import Supabase manager (optional)
try:
    from supabase_manager import SupabaseManager
    SUPABASE_ENABLED = True
except ImportError:
    SUPABASE_ENABLED = False
    print("⚠ Supabase manager tidak tersedia")

def register_jemaat_to_supabase(name):
    """
    Mendaftarkan jemaat baru ke database Supabase
    
    Args:
        name: Nama jemaat yang akan didaftarkan
        
    Returns:
        id_jemaat jika berhasil, None jika gagal
    """
    if not SUPABASE_ENABLED:
        print(f"  ⚠ Supabase tidak tersedia, skip registrasi untuk {name}")
        return None
    
    try:
        supabase = SupabaseManager()
        conn = supabase.get_connection()
        
        if not conn:
            print(f"  ✗ Gagal koneksi ke database untuk {name}")
            return None
        
        try:
            cur = conn.cursor()
            
            # Cek apakah tabel Jemaat ada
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'Jemaat'
                )
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                print(f"  ⚠ Tabel Jemaat belum ada di database")
                print(f"     Jalankan: npx prisma migrate dev atau npx prisma db push")
                print(f"     Skip registrasi untuk {name}")
                cur.close()
                supabase.return_connection(conn)
                supabase.close()
                return None
            
            # Cek apakah jemaat sudah ada
            cur.execute("""
                SELECT id_jemaat FROM "Jemaat" 
                WHERE LOWER(name) = LOWER(%s)
                LIMIT 1
            """, (name,))
            
            result = cur.fetchone()
            
            if result:
                id_jemaat = result[0]
                print(f"  ✓ {name} sudah terdaftar (ID: {id_jemaat})")
                cur.close()
                supabase.return_connection(conn)
                supabase.close()
                return id_jemaat
            
            # Jemaat belum ada, minta data lengkap
            print(f"\n--- Registrasi Jemaat Baru: {name} ---")
            print("  (Tekan Enter untuk gunakan nilai default)")
            
            # Input data jemaat
            jabatan = input("  Jabatan [Jemaat]: ").strip() or "Jemaat"
            status = input("  Status [Aktif]: ").strip() or "Aktif"
            
            # Tanggal lahir
            tgl_lahir_str = input("  Tanggal Lahir (YYYY-MM-DD) [2000-01-01]: ").strip() or "2000-01-01"
            try:
                tanggal_lahir = datetime.strptime(tgl_lahir_str, "%Y-%m-%d")
                # Hitung umur
                today = datetime.now()
                age = today.year - tanggal_lahir.year - ((today.month, today.day) < (tanggal_lahir.month, tanggal_lahir.day))
            except ValueError:
                print("    Format salah, gunakan default: 2000-01-01")
                tanggal_lahir = datetime(2000, 1, 1)
                age = datetime.now().year - 2000
            
            gender_input = input("  Gender (L/P) [L]: ").strip().upper() or "L"
            gender = "Laki-laki" if gender_input == "L" else "Perempuan"
            
            email = input(f"  Email [{name.lower().replace(' ', '.')}@gki.com]: ").strip() or f"{name.lower().replace(' ', '.')}@gki.com"
            handphone = input("  No. HP [0000000000]: ").strip() or "0000000000"
            
            # Generate ID
            id_jemaat = str(uuid.uuid4())
            
            # Insert ke database
            cur.execute("""
                INSERT INTO "Jemaat" 
                (id_jemaat, name, jabatan, status, tanggal_lahir, gender, email, "dateOfBirth", age, handphone)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_jemaat,
                name,
                jabatan,
                status,
                tanggal_lahir,
                gender,
                email,
                tanggal_lahir,  # dateOfBirth sama dengan tanggal_lahir
                age,
                handphone
            ))
            
            conn.commit()
            print(f"  ✓ {name} berhasil didaftarkan ke database (ID: {id_jemaat})")
            
            cur.close()
            supabase.return_connection(conn)
            supabase.close()
            
            return id_jemaat
            
        except Exception as e:
            print(f"  ✗ Error saat registrasi {name}: {e}")
            conn.rollback()
            supabase.return_connection(conn)
            return None
            
    except Exception as e:
        print(f"  ✗ Error koneksi Supabase untuk {name}: {e}")
        return None

def move_unknown_to_faces():
    """
    Pindahkan folder dari unknown ke faces setelah diberi nama
    """
    print("=== Pindahkan Wajah Unknown ke Dataset ===\n")
    
    if not os.path.exists(config.UNKNOWN_DIR):
        print(f"⚠ Direktori {config.UNKNOWN_DIR} tidak ditemukan")
        return
    
    unknown_folders = [f for f in Path(config.UNKNOWN_DIR).iterdir() if f.is_dir()]
    
    if len(unknown_folders) == 0:
        print("Tidak ada wajah unknown yang perlu diproses")
        return
    
    print(f"Ditemukan {len(unknown_folders)} folder wajah unknown:\n")
    
    for idx, folder in enumerate(unknown_folders, 1):
        print(f"{idx}. {folder.name}")
    
    print("\nPilihan:")
    print("1. Proses satu per satu (beri nama)")
    print("2. Proses semua (gunakan nama folder existing)")
    print("3. Skip / Keluar")
    
    choice = input("\nPilihan (1/2/3): ").strip()
    
    if choice == "1":
        # Proses satu per satu
        for folder in unknown_folders:
            print(f"\nFolder: {folder.name}")
            print(f"Jumlah foto: {len(list(folder.glob('*.jpg')))}")
            
            action = input("Aksi (n=beri nama, s=skip, q=quit): ").strip().lower()
            
            if action == 'q':
                break
            elif action == 's':
                continue
            elif action == 'n':
                new_name = input("Nama orang: ").strip()
                if new_name:
                    dest = Path(config.FACES_DIR) / new_name
                    
                    # Jika folder sudah ada, pindahkan file ke dalamnya
                    if dest.exists():
                        for img in folder.glob('*.jpg'):
                            shutil.copy2(img, dest)
                        shutil.rmtree(folder)
                        print(f"✓ Foto ditambahkan ke {new_name}")
                    else:
                        shutil.move(str(folder), str(dest))
                        print(f"✓ Folder dipindahkan sebagai {new_name}")
    
    elif choice == "2":
        # Proses semua
        for folder in unknown_folders:
            dest = Path(config.FACES_DIR) / folder.name
            
            if dest.exists():
                for img in folder.glob('*.jpg'):
                    shutil.copy2(img, dest)
                shutil.rmtree(folder)
                print(f"✓ {folder.name}: foto ditambahkan")
            else:
                shutil.move(str(folder), str(dest))
                print(f"✓ {folder.name}: folder dipindahkan")
    
    print("\n✓ Selesai memproses wajah unknown")

def retrain_model():
    """Latih ulang model dengan semua data"""
    print("\n=== Melatih Ulang Model (ArcFace) ===\n")
    
    encoder = ArcFaceEncoder()
    encoder.encode_faces_from_directory()
    
    if len(encoder.known_embeddings) > 0:
        encoder.save_encodings()
        print("\n✓ Model berhasil dilatih ulang!")
        
        # Registrasi semua nama ke Supabase
        if SUPABASE_ENABLED:
            print("\n=== Registrasi Jemaat ke Database ===\n")
            unique_names = set(encoder.known_names)
            
            registered_count = 0
            for name in unique_names:
                if register_jemaat_to_supabase(name):
                    registered_count += 1
            
            if registered_count > 0:
                print(f"\n✓ Berhasil registrasi {registered_count} jemaat")
            else:
                print(f"\n⚠ Tidak ada jemaat yang diregistrasi (database belum siap atau sudah terdaftar)")
        
        return True
    else:
        print("\n⚠ Tidak ada encoding yang berhasil dibuat")
        return False

def main():
    print("=== Retrain Model - GKI Karawaci ===\n")
    print("Script ini akan:")
    print("1. Memproses wajah unknown (pindah ke dataset)")
    print("2. Melatih ulang model dengan data terbaru\n")
    
    proceed = input("Lanjutkan? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Dibatalkan")
        return
    
    # Step 1: Proses unknown faces
    move_unknown_to_faces()
    
    # Step 2: Retrain model
    if retrain_model():
        print("\n" + "="*50)
        print("Model siap digunakan!")
        print("Jalankan 07_main_system.py untuk memulai sistem")
        print("="*50)

if __name__ == "__main__":
    main()
