import time
import uuid
from enum import Enum
from typing import Callable, Optional
from backend.common.logger import setup_logger

logger = setup_logger("Failover")

class NodeRole(str, Enum):
    COORDINATOR = "COORDINATOR"
    FOLLOWER = "FOLLOWER"

class NodeStatus(str, Enum):
    ONLINE = "ONLINE"
    STANDBY = "STANDBY"
    PROMOTED = "PROMOTED"
    CRASHED = "CRASHED"

class FailoverManager:
    """
    Mengelola siklus hidup, state transition (FOLLOWER -> COORDINATOR),
    dan audit log failover terdistribusi.
    """
    def __init__(self, service_name: str, initial_role: NodeRole, node_host: str, node_port: int, peer_host: str, peer_port: int):
        self.service_name = service_name
        self.role = initial_role
        self.status = NodeStatus.ONLINE if initial_role == NodeRole.COORDINATOR else NodeStatus.STANDBY
        self.node_host = node_host
        self.node_port = node_port
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.promotion_callbacks: list[Callable[[], None]] = []
        self.promoted_at: Optional[float] = None

    def register_promotion_callback(self, callback: Callable[[], None]):
        self.promotion_callbacks.append(callback)

    def trigger_promotion(self, reason: str = "Heartbeat timeout threshold exceeded"):
        if self.role == NodeRole.COORDINATOR:
            return

        logger.warning(f"============================================================")
        logger.warning(f"[FAILOVER EVENT] Memicu Promosi Mandiri untuk {self.service_name}!")
        logger.warning(f"  Penyebab : {reason}")
        logger.warning(f"  Node ID  : {self.node_host}:{self.node_port}")
        logger.warning(f"  Peran    : {self.role.value} -> {NodeRole.COORDINATOR.value}")
        logger.warning(f"============================================================")

        self.role = NodeRole.COORDINATOR
        self.status = NodeStatus.PROMOTED
        self.promoted_at = time.time()

        # Eksekusi seluruh callback aktivasi layanan
        for cb in self.promotion_callbacks:
            try:
                cb()
            except Exception as e:
                logger.error(f"[PROMOTION] Kesalahan pada callback aktivasi: {e}")

        logger.info(f"[PROMOTION SUCCESS] {self.service_name} sekarang berstatus COORDINATOR aktif melayani traffic!")
        
        # Log failover event ke data server secara asynchronous/non-blocking
        self._record_failover_log(reason)

    def _record_failover_log(self, reason: str):
        import threading
        def worker():
            try:
                from backend.common.db_client import db_client
                log_entry = {
                    "id": str(uuid.uuid4()),
                    "service_name": self.service_name,
                    "previous_coordinator": f"{self.peer_host}:{self.peer_port}",
                    "promoted_node": f"{self.node_host}:{self.node_port}",
                    "reason": reason,
                    "event_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "details": f'{{"promoted_at": {self.promoted_at}, "status": "{self.status.value}"}}'
                }
                db_client.record_failover_log(log_entry)
                logger.info(f"[AUDIT LOG] Peristiwa failover berhasil dicatat ke basis data terdistribusi.")
            except Exception as e:
                logger.warning(f"[AUDIT LOG] Catatan failover log tertunda (Data node mungkin masih proses failover): {e}")

        threading.Thread(target=worker, daemon=True).start()
