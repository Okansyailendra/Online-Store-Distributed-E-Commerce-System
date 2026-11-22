import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import time
import argparse
from typing import Optional

from backend.common.config import settings
from backend.common.logger import setup_logger
from backend.common.rpc_protocol import RPCServer
from backend.common.heartbeat import HeartbeatEmitter, HeartbeatListener
from backend.common.failover import FailoverManager, NodeRole, NodeStatus
from backend.server1_rpc.checkout_handler import CheckoutHandler

logger = setup_logger("Server1RPC")

parser = argparse.ArgumentParser(description="Server 1: Transaction & Checkout Processing Service (RPC)")
parser.add_argument("--role", choices=["COORDINATOR", "FOLLOWER"], default="COORDINATOR", help="Node Role")
parser.add_argument("--host", default=None, help="Host override")
parser.add_argument("--port", type=int, default=None, help="Port override")
args, _ = parser.parse_known_args()

INITIAL_ROLE = NodeRole(args.role)
IS_COORD = (INITIAL_ROLE == NodeRole.COORDINATOR)

NODE_HOST = args.host or (settings.SERVER1_RPC_PRIMARY_HOST if IS_COORD else settings.SERVER1_RPC_BACKUP_HOST)
NODE_PORT = args.port or (settings.SERVER1_RPC_PRIMARY_PORT if IS_COORD else settings.SERVER1_RPC_BACKUP_PORT)

PEER_HOST = settings.SERVER1_RPC_BACKUP_HOST if IS_COORD else settings.SERVER1_RPC_PRIMARY_HOST
PEER_PORT = settings.SERVER1_RPC_BACKUP_PORT if IS_COORD else settings.SERVER1_RPC_PRIMARY_PORT
HB_PORT = settings.SERVER1_RPC_HEARTBEAT_PORT

failover_mgr = FailoverManager(
    service_name="server1_rpc",
    initial_role=INITIAL_ROLE,
    node_host=NODE_HOST,
    node_port=NODE_PORT,
    peer_host=PEER_HOST,
    peer_port=PEER_PORT
)

checkout_handler = CheckoutHandler()
rpc_server = RPCServer(host=NODE_HOST, port=NODE_PORT, server_name="Server1RPC")

# Daftarkan Remote Procedures
rpc_server.register_method("process_checkout", checkout_handler.process_checkout)
rpc_server.register_method("validate_order", checkout_handler.validate_order)
rpc_server.register_method("cancel_order", checkout_handler.cancel_order)
rpc_server.register_method("get_transaction_status", checkout_handler.get_transaction_status)

hb_emitter: Optional[HeartbeatEmitter] = None
hb_listener: Optional[HeartbeatListener] = None

def on_coordinator_failure():
    failover_mgr.trigger_promotion(reason=f"Heartbeat timeout ({settings.HEARTBEAT_TIMEOUT}s) exceeded on RPC port")

failover_mgr.register_promotion_callback(lambda: logger.info(f"[PROMOTION] Node RPC Backup siap melayani transaksi penuh sebagai COORDINATOR di {NODE_HOST}:{NODE_PORT}!"))

def main():
    global hb_emitter, hb_listener
    logger.info(f"=== Menjalankan Server 1 (RPC Checkout) sebagai {failover_mgr.role.value} di {NODE_HOST}:{NODE_PORT} ===")

    # Buka socket server RPC di kedua node
    rpc_server.start()

    if failover_mgr.role == NodeRole.COORDINATOR:
        hb_emitter = HeartbeatEmitter(
            target_host=PEER_HOST,
            target_port=HB_PORT,
            sender_id=f"server1_rpc_{NODE_PORT}",
            interval=settings.HEARTBEAT_INTERVAL
        )
        hb_emitter.start()
    else:
        hb_listener = HeartbeatListener(
            listen_host=NODE_HOST,
            listen_port=HB_PORT,
            node_id=f"server1_rpc_{NODE_PORT}",
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
        logger.info("[RPC] Menghentikan layanan Server 1...")
        if hb_emitter:
            hb_emitter.stop()
        if hb_listener:
            hb_listener.stop()
        rpc_server.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
