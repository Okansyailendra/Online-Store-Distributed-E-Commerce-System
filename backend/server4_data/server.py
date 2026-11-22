import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import argparse
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

from backend.common.config import settings
from backend.common.logger import setup_logger
from backend.common.heartbeat import HeartbeatEmitter, HeartbeatListener
from backend.common.failover import FailoverManager, NodeRole, NodeStatus
from backend.server4_data.database import Database
from backend.server4_data.replication import ReplicationManager

logger = setup_logger("Server4Data")

parser = argparse.ArgumentParser(description="Server 4: Data Layer & State Replication Service")
parser.add_argument("--role", choices=["COORDINATOR", "FOLLOWER"], default="COORDINATOR", help="Node Role")
parser.add_argument("--host", default=None, help="Host override")
parser.add_argument("--port", type=int, default=None, help="Port override")
args, _ = parser.parse_known_args()

INITIAL_ROLE = NodeRole(args.role)
IS_COORD = (INITIAL_ROLE == NodeRole.COORDINATOR)

NODE_HOST = args.host or (settings.SERVER4_DATA_PRIMARY_HOST if IS_COORD else settings.SERVER4_DATA_BACKUP_HOST)
NODE_PORT = args.port or (settings.SERVER4_DATA_PRIMARY_PORT if IS_COORD else settings.SERVER4_DATA_BACKUP_PORT)

PEER_HOST = settings.SERVER4_DATA_BACKUP_HOST if IS_COORD else settings.SERVER4_DATA_PRIMARY_HOST
PEER_PORT = settings.SERVER4_DATA_BACKUP_PORT if IS_COORD else settings.SERVER4_DATA_PRIMARY_PORT
HB_PORT = settings.SERVER4_DATA_REPLICATION_PORT

DB_PATH = settings.DATABASE_SQLITE_PRIMARY_PATH if IS_COORD else settings.DATABASE_SQLITE_BACKUP_PATH

# Inisialisasi Database Lokal
db = Database(DB_PATH)

# Inisialisasi Pengelola Failover
failover_mgr = FailoverManager(
    service_name="server4_data",
    initial_role=INITIAL_ROLE,
    node_host=NODE_HOST,
    node_port=NODE_PORT,
    peer_host=PEER_HOST,
    peer_port=PEER_PORT
)

# Inisialisasi Replikasi Manager
replication_mgr = ReplicationManager(target_backup_url=f"http://{PEER_HOST}:{PEER_PORT}")

# Heartbeat Components
hb_emitter: Optional[HeartbeatEmitter] = None
hb_listener: Optional[HeartbeatListener] = None

def on_coordinator_failure():
    failover_mgr.trigger_promotion(reason=f"Heartbeat timeout threshold ({settings.HEARTBEAT_TIMEOUT}s) exceeded on data port")

failover_mgr.register_promotion_callback(lambda: logger.info("[PROMOTION] Database Follower telah aktif penuh sebagai PRIMARY WRITE-MASTER!"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    global hb_emitter, hb_listener
    logger.info(f"=== Menjalankan Server 4 (Data Service) sebagai {failover_mgr.role.value} di {NODE_HOST}:{NODE_PORT} ===")
    
    if failover_mgr.role == NodeRole.COORDINATOR:
        hb_emitter = HeartbeatEmitter(target_host=PEER_HOST, target_port=HB_PORT, sender_id=f"server4_data_{NODE_PORT}", interval=settings.HEARTBEAT_INTERVAL)
        hb_emitter.start()
    else:
        hb_listener = HeartbeatListener(listen_host=NODE_HOST, listen_port=HB_PORT, node_id=f"server4_data_{NODE_PORT}", timeout=settings.HEARTBEAT_TIMEOUT, interval=settings.HEARTBEAT_INTERVAL, max_missed=settings.MAX_MISSED_HEARTBEATS, on_failure=on_coordinator_failure)
        hb_listener.start()

    yield

    if hb_emitter:
        hb_emitter.stop()
    if hb_listener:
        hb_listener.stop()

app = FastAPI(title="Server 4 - Data & State Replication Service", lifespan=lifespan)

# Skema Request
class QueryRequest(BaseModel):
    sql: str
    params: Optional[dict] = None

class TransactionStatement(BaseModel):
    sql: str
    params: Optional[dict] = None

class TransactionRequest(BaseModel):
    statements: list[TransactionStatement]

class ReplicatePayload(BaseModel):
    event_id: str
    sequence_id: int
    timestamp: float
    sql: str
    params: Optional[dict] = None

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "server4_data",
        "role": failover_mgr.role.value,
        "node_status": failover_mgr.status.value,
        "host": NODE_HOST,
        "port": NODE_PORT,
        "database_path": DB_PATH
    }

@app.post("/internal/db/query")
def execute_query(req: QueryRequest):
    try:
        rows = db.query(req.sql, req.params)
        return {"success": True, "rows": rows}
    except Exception as e:
        logger.error(f"[DATA QUERY ERROR] {e} | SQL: {req.sql}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/db/execute")
def execute_command(req: QueryRequest):
    try:
        affected = db.execute(req.sql, req.params)
        # Jika node adalah koordinator aktif, lakukan replikasi mutasi
        if failover_mgr.role == NodeRole.COORDINATOR:
            replication_mgr.replicate_mutation(req.sql, req.params)
        return {"success": True, "affected_rows": affected}
    except Exception as e:
        logger.error(f"[DATA EXECUTE ERROR] {e} | SQL: {req.sql}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/db/transaction")
def execute_transaction(req: TransactionRequest):
    try:
        raw_stmts = [{"sql": s.sql, "params": s.params or {}} for s in req.statements]
        success = db.execute_transaction(raw_stmts)
        if success and failover_mgr.role == NodeRole.COORDINATOR:
            for s in raw_stmts:
                replication_mgr.replicate_mutation(s["sql"], s["params"])
        return {"success": True}
    except Exception as e:
        logger.error(f"[DATA TRANSACTION ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/replicate")
def receive_replication(payload: ReplicatePayload):
    try:
        db.execute(payload.sql, payload.params)
        return {"success": True, "sequence_id": payload.sequence_id, "ack": True}
    except Exception as e:
        logger.error(f"[REPLICATION APPLY ERROR] Gagal menerapkan mutasi #{payload.sequence_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/internal/sync/catchup")
def get_catchup_events(from_seq: int = 0):
    events = replication_mgr.get_pending_sync_events(from_seq)
    return {"success": True, "events": events}

if __name__ == "__main__":
    uvicorn.run(app, host=NODE_HOST, port=NODE_PORT, log_level="warning")
