#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/.running_pids"

if [ -f "$PID_FILE" ]; then
    echo "Menghentikan seluruh node backend terdistribusi..."
    while read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            echo "Node PID $pid dihentikan."
        fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

# Pastikan port 6001-6004, 6101-6104, 6201-6204 bersih
fuser -k 6001/tcp 6002/tcp 6003/tcp 6004/tcp 6101/tcp 6102/tcp 6103/tcp 6104/tcp 6201/tcp 6202/tcp 6203/tcp 6204/tcp 2>/dev/null

echo "Seluruh node backend telah dihentikan secara bersih."
