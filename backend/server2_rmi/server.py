import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import time
import argparse
import threading
import Pyro5.api
import Pyro5.server
from typing import Optional

from backend.common.config import settings
from backend.common.logger import setup_logger
from backend.common.heartbeat import HeartbeatEmitter, HeartbeatListener
from backend.common.failover import FailoverManager, NodeRole, NodeStatus
from backend.server2_rmi.inventory_service import InventoryService

logger = setup_logger("Server2RMI")

parser = argparse.ArgumentParser(description="Server 2: Inventory & Stock Management Service (RMI)")
parser.add_argument("--role", choices=["COORDINATOR", "FOLLOWER"], default="COORDINATOR", help="Node Role")
parser.add_argument("--host", default=None, help="Host override")
parser.add_argument("--port", type=int, default=None, help="Port override")
args, _ = parser.parse_known_args()

INITIAL_ROLE = NodeRole(args.role)
IS_COORD = (INITIAL_ROLE == NodeRole.COORDINATOR)

NODE_HOST = args.host or (settings.SERVER2_RMI_PRIMARY_HOST if IS_COORD else settings.SERVER2_RMI_BACKUP_HOST)
NODE_PORT = args.port or (settings.SERVER2_RMI_PRIMARY_PORT if IS_COORD else settings.SERVER2_RMI_BACKUP_PORT)

PEER_HOST = settings.SERVER2_RMI_BACKUP_HOST if IS_COORD else settings.SERVER2_RMI_PRIMARY_HOST
PEER_PORT = settings.SERVER2_RMI_BACKUP_PORT if IS_COORD else settings.SERVER2_RMI_PRIMARY_PORT
HB_PORT = settings.SERVER2_RMI_HEARTBEAT_PORT

failover_mgr = FailoverManager(
    service_name="server2_rmi",
    initial_role=INITIAL_ROLE,
    node_host=NODE_HOST,
    node_port=NODE_PORT,
    peer_host=PEER_HOST,
    peer_port=PEER_PORT
)

pyro_daemon: Optional[Pyro5.server.Daemon] = None
daemon_thread: Optional[threading.Thread] = None
hb_emitter: Optional[HeartbeatEmitter] = None
hb_listener: Optional[HeartbeatListener] = None

def start_pyro_daemon():
    global pyro_daemon, daemon_thread
    try:
        pyro_daemon = Pyro5.server.Daemon(host=NODE_HOST, port=NODE_PORT)
        uri = pyro_daemon.register(InventoryService, objectId="InventoryService")
        logger.info(f"[RMI DAEMON] Objek InventoryService berhasil didaftarkan pada URI: {uri}")
        daemon_thread = threading.Thread(target=pyro_daemon.requestLoop, daemon=True, name="PyroDaemonLoop")
        daemon_thread.start()
    except Exception as e:
        logger.error(f"[RMI DAEMON] Gagal memulai Pyro Daemon pada {NODE_HOST}:{NODE_PORT}: {e}")

def on_coordinator_failure():
    failover_mgr.trigger_promotion(reason=f"Heartbeat timeout threshold ({settings.HEARTBEAT_TIMEOUT}s) exceeded on RMI port")

failover_mgr.register_promotion_callback(lambda: logger.info(f"[PROMOTION] Node RMI Backup siap melayani permintaan stok penuh sebagai COORDINATOR di {NODE_HOST}:{NODE_PORT}!"))

def main():
    global hb_emitter, hb_listener
    logger.info(f"=== Menjalankan Server 2 (RMI Inventory) sebagai {failover_mgr.role.value} di {NODE_HOST}:{NODE_PORT} ===")

    # Daemon dijalankan di kedua node, namun pengikut berada dalam posisi standby
    start_pyro_daemon()

    if failover_mgr.role == NodeRole.COORDINATOR:
        hb_emitter = HeartbeatEmitter(
            target_host=PEER_HOST,
            target_port=HB_PORT,
            sender_id=f"server2_rmi_{NODE_PORT}",
            interval=settings.HEARTBEAT_INTERVAL
        )
        hb_emitter.start()
    else:
        hb_listener = HeartbeatListener(
            listen_host=NODE_HOST,
            listen_port=HB_PORT,
            node_id=f"server2_rmi_{NODE_PORT}",
            timeout=settings.HEARTBEAT_TIMEOUT,
            interval=settings.HEARTBEAT_INTERVAL,
            max_missed=settings.MAX_MISSED_HEARTBEATS,
            on_failure=on_coordinator_failure
        )
        hb_listener.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("[RMI] Menghentikan layanan Server 2...")
        if hb_emitter:
            hb_emitter.stop()
        if hb_listener:
            hb_listener.stop()
        if pyro_daemon:
            pyro_daemon.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()
