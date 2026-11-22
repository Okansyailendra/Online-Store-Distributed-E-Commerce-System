import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import argparse
import uvicorn
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.common.config import settings
from backend.common.logger import setup_logger
from backend.common.heartbeat import HeartbeatEmitter, HeartbeatListener
from backend.common.failover import FailoverManager, NodeRole, NodeStatus

from backend.server3_api.routes.auth_routes import router as auth_router
from backend.server3_api.routes.product_routes import router as product_router
from backend.server3_api.routes.cart_routes import router as cart_router
from backend.server3_api.routes.order_routes import router as order_router
from backend.server3_api.routes.admin_routes import router as admin_router
from backend.server3_api.routes.cluster_routes import router as cluster_router

logger = setup_logger("Server3API")

parser = argparse.ArgumentParser(description="Server 3: Product Catalog, Auth, Cart & Order REST API Service")
parser.add_argument("--role", choices=["COORDINATOR", "FOLLOWER"], default="COORDINATOR", help="Node Role")
parser.add_argument("--host", default=None, help="Host override")
parser.add_argument("--port", type=int, default=None, help="Port override")
args, _ = parser.parse_known_args()

INITIAL_ROLE = NodeRole(args.role)
IS_COORD = (INITIAL_ROLE == NodeRole.COORDINATOR)

NODE_HOST = args.host or (settings.SERVER3_API_PRIMARY_HOST if IS_COORD else settings.SERVER3_API_BACKUP_HOST)
NODE_PORT = args.port or (settings.SERVER3_API_PRIMARY_PORT if IS_COORD else settings.SERVER3_API_BACKUP_PORT)

PEER_HOST = settings.SERVER3_API_BACKUP_HOST if IS_COORD else settings.SERVER3_API_PRIMARY_HOST
PEER_PORT = settings.SERVER3_API_BACKUP_PORT if IS_COORD else settings.SERVER3_API_PRIMARY_PORT
HB_PORT = settings.SERVER3_API_HEARTBEAT_PORT

failover_mgr = FailoverManager(
    service_name="server3_api",
    initial_role=INITIAL_ROLE,
    node_host=NODE_HOST,
    node_port=NODE_PORT,
    peer_host=PEER_HOST,
    peer_port=PEER_PORT
)

hb_emitter: Optional[HeartbeatEmitter] = None
hb_listener: Optional[HeartbeatListener] = None

def on_coordinator_failure():
    failover_mgr.trigger_promotion(reason=f"Heartbeat timeout threshold ({settings.HEARTBEAT_TIMEOUT}s) exceeded on API port")

failover_mgr.register_promotion_callback(lambda: logger.info(f"[PROMOTION] Node API Backup sekarang aktif penuh melayani permintaan REST sebagai COORDINATOR di {NODE_HOST}:{NODE_PORT}!"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    global hb_emitter, hb_listener
    logger.info(f"=== Menjalankan Server 3 (REST API) sebagai {failover_mgr.role.value} di {NODE_HOST}:{NODE_PORT} ===")

    if failover_mgr.role == NodeRole.COORDINATOR:
        hb_emitter = HeartbeatEmitter(
            target_host=PEER_HOST,
            target_port=HB_PORT,
            sender_id=f"server3_api_{NODE_PORT}",
            interval=settings.HEARTBEAT_INTERVAL
        )
        hb_emitter.start()
    else:
        hb_listener = HeartbeatListener(
            listen_host=NODE_HOST,
            listen_port=HB_PORT,
            node_id=f"server3_api_{NODE_PORT}",
            timeout=settings.HEARTBEAT_TIMEOUT,
            interval=settings.HEARTBEAT_INTERVAL,
            max_missed=settings.MAX_MISSED_HEARTBEATS,
            on_failure=on_coordinator_failure
        )
        hb_listener.start()

    yield

    if hb_emitter:
        hb_emitter.stop()
    if hb_listener:
        hb_listener.stop()

app = FastAPI(
    title="Sister E-Commerce API (Server 3)",
    description="Layanan REST API Katalog, Autentikasi, Cart, dan Order History dengan Failover Terdistribusi",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware agar Frontend Next.js di port 3000 dapat berinteraksi langsung atau melalui proxy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(admin_router)
app.include_router(cluster_router)

if __name__ == "__main__":
    uvicorn.run(app, host=NODE_HOST, port=NODE_PORT, log_level="warning")
