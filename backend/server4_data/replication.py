import httpx
import time
import uuid
import threading
from typing import Optional
from backend.common.logger import setup_logger

logger = setup_logger("Replication")

class ReplicationManager:
    """
    Mengelola streaming replikasi mutasi state semi-synchronous
    dari Koordinator Data ke Pengikut Data.
    """
    def __init__(self, target_backup_url: str):
        self.target_backup_url = target_backup_url
        self._seq = 0
        self._pending_queue: list[dict] = []
        self._lock = threading.Lock()

    def replicate_mutation(self, sql: str, params: Optional[dict] = None) -> bool:
        with self._lock:
            self._seq += 1
            payload = {
                "event_id": str(uuid.uuid4()),
                "sequence_id": self._seq,
                "timestamp": time.time(),
                "sql": sql,
                "params": params or {}
            }

        # Coba kirim ke follower (semi-synchronous dengan timeout pendek 1.0 detik)
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.post(f"{self.target_backup_url}/internal/replicate", json=payload)
                if resp.status_code == 200:
                    return True
                logger.warning(f"[REPLICATION] Follower merespon HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            # Jika follower belum aktif atau sedang crash, simpan ke antrean pending
            with self._lock:
                self._pending_queue.append(payload)
                if len(self._pending_queue) > 1000:
                    self._pending_queue.pop(0) # Batasi memori buffer
            logger.debug(f"[REPLICATION] Follower offline ({e}), mutasi #{self._seq} diantrikan.")
        return False

    def get_pending_sync_events(self, from_seq: int = 0) -> list[dict]:
        with self._lock:
            return [ev for ev in self._pending_queue if ev["sequence_id"] > from_seq]
