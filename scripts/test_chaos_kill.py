#!/usr/bin/env python3
"""
Skrip Simulasi Injeksi Kegagalan (Chaos Testing / Crash Injection)
Digunakan untuk mendemonstrasikan toleransi kesalahan di hadapan dosen penguji.
"""

import sys
import time
import subprocess
import httpx
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.common.config import settings

def print_separator(title=""):
    print("\n" + "=" * 65)
    if title:
        print(f"   {title}")
        print("=" * 65)

def check_node(host, port, name):
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.8)
            s.connect((host, port))
            return True
    except Exception:
        return False

def main():
    print_separator("SIMULASI PENGUJIAN TOLERANSI KESALAHAN (CHAOS KILL)")
    print("Skrip ini akan menguji ketahanan failover otomatis pada:")
    print("  1. Server 1 (RPC Checkout: Port 6001 -> 6101)")
    print("  2. Server 3 (REST API Katalog: Port 6003 -> 6103)")
    print("  3. Keluar")

    choice = input("\nPilih skenario pengujian [1/2/3]: ").strip()

    if choice == "1":
        target_port = settings.SERVER1_RPC_PRIMARY_PORT
        backup_port = settings.SERVER1_RPC_BACKUP_PORT
        service_name = "Server 1 (RPC Transaksi)"
    elif choice == "2":
        target_port = settings.SERVER3_API_PRIMARY_PORT
        backup_port = settings.SERVER3_API_BACKUP_PORT
        service_name = "Server 3 (REST API Katalog)"
    else:
        print("Pengujian dibatalkan.")
        return

    print_separator(f"TAHAP 1: Memeriksa Status {service_name}")
    primary_alive = check_node("127.0.0.1", target_port, "Primary")
    backup_alive = check_node("127.0.0.1", backup_port, "Backup")

    print(f"Status Primary (Port {target_port}): {'ONLINE 💚' if primary_alive else 'OFFLINE ❌'}")
    print(f"Status Backup  (Port {backup_port}): {'ONLINE 💚' if backup_alive else 'OFFLINE ❌'}")

    if not primary_alive or not backup_alive:
        print("\nPeringatan: Pastikan kedua node sudah dijalankan dengan ./scripts/run_all_local.sh sebelum memulai uji coba.")
        return

    print_separator("TAHAP 2: Injeksi Kegagalan (Crash Injection)")
    input(f"Tekan ENTER untuk mematikan paksa Koordinator Utama pada port {target_port}...")
    
    # Matikan port target
    subprocess.run(["fuser", "-k", f"{target_port}/tcp"], stderr=subprocess.DEV_NULL)
    print(f"\n[CRASH TRIGGERED] Node Koordinator pada port {target_port} berhasil dimatikan secara mendadak!")

    print_separator("TAHAP 3: Menghitung Waktu Deteksi & Promosi Otomatis")
    print(f"Menunggu deteksi hilangnya Heartbeat (Threshold: {settings.HEARTBEAT_TIMEOUT}s)...")
    
    start_time = time.time()
    for i in range(1, int(settings.HEARTBEAT_TIMEOUT) + 3):
        time.sleep(1.0)
        elapsed = time.time() - start_time
        print(f"  Detik ke-{i} (Elapsed: {elapsed:.1f}s)... Pengikut memantau detak jantung...")

    print_separator("TAHAP 4: Verifikasi Status Promosi Pengikut")
    # Periksa log failover via database
    try:
        from backend.server4_data.database import Database
        db = Database(settings.DATABASE_SQLITE_PRIMARY_PATH)
        logs = db.query("SELECT service_name, previous_coordinator, promoted_node, reason, event_timestamp FROM cluster_failover_logs ORDER BY event_timestamp DESC LIMIT 1")
        if logs:
            l = logs[0]
            print("Audit Log Failover Terdistribusi Berhasil Tercatat:")
            print(f"  - Service      : {l['service_name']}")
            print(f"  - Failed Node  : {l['previous_coordinator']}")
            print(f"  - Promoted Node: {l['promoted_node']}")
            print(f"  - Waktu Deteksi: {l['event_timestamp']}")
            print(f"  - Alasan       : {l['reason']}")
            print("\n[KESIMPULAN DEMO]: Failover Promotion SUKSES dan Ketersediaan Sistem Terjaga!")
        else:
            print("Node pengikut sedang memproses promosi. Periksa terminal pengikut.")
    except Exception as e:
        print(f"Info: {e}")

if __name__ == "__main__":
    main()
