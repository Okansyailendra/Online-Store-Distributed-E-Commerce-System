#!/usr/bin/env bash

# Jalankan seluruh 8 node backend terdistribusi dalam mode background
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR" || exit 1

export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"
PID_FILE="$ROOT_DIR/.running_pids"
LOGS_DIR="$ROOT_DIR/logs"
mkdir -p "$LOGS_DIR"
> "$PID_FILE"

source "$ROOT_DIR/venv/bin/activate"

echo "================================================================="
echo "   MEMULAI 8 NODE BACKEND SISTEM TERDISTRIBUSI (SISTER)"
echo "================================================================="

# 1. Jalankan Server 4 Data
nohup python3 backend/server4_data/server.py --role COORDINATOR > "$LOGS_DIR/server4_coord.log" 2>&1 &
echo "$!" >> "$PID_FILE"
echo "[OK] Server 4 (Data Primary :6004) dimulai (PID $!)"

nohup python3 backend/server4_data/server.py --role FOLLOWER > "$LOGS_DIR/server4_follow.log" 2>&1 &
echo "$!" >> "$PID_FILE"
echo "[OK] Server 4B (Data Backup :6104) dimulai (PID $!)"

sleep 1.5

# 2. Jalankan Server 2 RMI
nohup python3 backend/server2_rmi/server.py --role COORDINATOR > "$LOGS_DIR/server2_coord.log" 2>&1 &
echo "$!" >> "$PID_FILE"
echo "[OK] Server 2 (RMI Primary :6002) dimulai (PID $!)"

nohup python3 backend/server2_rmi/server.py --role FOLLOWER > "$LOGS_DIR/server2_follow.log" 2>&1 &
echo "$!" >> "$PID_FILE"
echo "[OK] Server 2B (RMI Backup :6102) dimulai (PID $!)"

sleep 1.5

# 3. Jalankan Server 1 RPC
nohup python3 backend/server1_rpc/server.py --role COORDINATOR > "$LOGS_DIR/server1_coord.log" 2>&1 &
echo "$!" >> "$PID_FILE"
echo "[OK] Server 1 (RPC Primary :6001) dimulai (PID $!)"

nohup python3 backend/server1_rpc/server.py --role FOLLOWER > "$LOGS_DIR/server1_follow.log" 2>&1 &
echo "$!" >> "$PID_FILE"
echo "[OK] Server 1B (RPC Backup :6101) dimulai (PID $!)"

sleep 1.5

# 4. Jalankan Server 3 REST API
nohup python3 backend/server3_api/server.py --role COORDINATOR > "$LOGS_DIR/server3_coord.log" 2>&1 &
echo "$!" >> "$PID_FILE"
echo "[OK] Server 3 (REST API Primary :6003) dimulai (PID $!)"

nohup python3 backend/server3_api/server.py --role FOLLOWER > "$LOGS_DIR/server3_follow.log" 2>&1 &
echo "$!" >> "$PID_FILE"
echo "[OK] Server 3B (REST API Backup :6103) dimulai (PID $!)"

sleep 1.5

echo "================================================================="
echo " Seluruh 8 node backend aktif berjalan! PID disimpan di .running_pids"
echo " Log setiap node dapat dilihat di folder logs/ (misal: tail -f logs/*.log)"
echo " Gunakan ./scripts/stop_all_local.sh untuk menghentikan seluruh node."
echo "================================================================="
