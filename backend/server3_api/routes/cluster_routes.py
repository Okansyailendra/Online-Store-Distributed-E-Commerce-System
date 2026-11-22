import socket
import httpx
import time
from fastapi import APIRouter
from backend.common.config import settings
from backend.common.db_client import db_client

router = APIRouter(prefix="/api/v1", tags=["Cluster & Health Monitoring"])

def check_tcp_port(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            return True
    except Exception:
        return False

def check_http_endpoint(url: str, timeout: float = 0.5) -> bool:
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            return resp.status_code == 200
    except Exception:
        return False

@router.get("/health")
def get_health():
    # Cek koneksi db
    db_ok = False
    try:
        row = db_client.query_one("SELECT 1 as alive")
        db_ok = bool(row and row.get("alive") == 1)
    except Exception:
        pass

    return {
        "status": "HEALTHY" if db_ok else "DEGRADED",
        "service": "server3_api",
        "timestamp": time.time(),
        "database_connected": db_ok
    }

@router.get("/cluster/status")
def get_cluster_status():
    """
    Mengaudit status langsung seluruh 8 node terdistribusi dalam cluster.
    """
    nodes = [
        {
            "id": "server1_rpc_primary",
            "name": "Server 1: RPC Transaksi (Primary)",
            "role": "COORDINATOR",
            "host": settings.SERVER1_RPC_PRIMARY_HOST,
            "port": settings.SERVER1_RPC_PRIMARY_PORT,
            "protocol": "TCP JSON-RPC 2.0",
            "online": check_tcp_port(settings.SERVER1_RPC_PRIMARY_HOST, settings.SERVER1_RPC_PRIMARY_PORT)
        },
        {
            "id": "server1_rpc_backup",
            "name": "Server 1: RPC Transaksi (Backup)",
            "role": "FOLLOWER",
            "host": settings.SERVER1_RPC_BACKUP_HOST,
            "port": settings.SERVER1_RPC_BACKUP_PORT,
            "protocol": "TCP JSON-RPC 2.0",
            "online": check_tcp_port(settings.SERVER1_RPC_BACKUP_HOST, settings.SERVER1_RPC_BACKUP_PORT)
        },
        {
            "id": "server2_rmi_primary",
            "name": "Server 2: RMI Inventaris (Primary)",
            "role": "COORDINATOR",
            "host": settings.SERVER2_RMI_PRIMARY_HOST,
            "port": settings.SERVER2_RMI_PRIMARY_PORT,
            "protocol": "Pyro5 RMI",
            "online": check_tcp_port(settings.SERVER2_RMI_PRIMARY_HOST, settings.SERVER2_RMI_PRIMARY_PORT)
        },
        {
            "id": "server2_rmi_backup",
            "name": "Server 2: RMI Inventaris (Backup)",
            "role": "FOLLOWER",
            "host": settings.SERVER2_RMI_BACKUP_HOST,
            "port": settings.SERVER2_RMI_BACKUP_PORT,
            "protocol": "Pyro5 RMI",
            "online": check_tcp_port(settings.SERVER2_RMI_BACKUP_HOST, settings.SERVER2_RMI_BACKUP_PORT)
        },
        {
            "id": "server3_api_primary",
            "name": "Server 3: REST API Katalog (Primary)",
            "role": "COORDINATOR",
            "host": settings.SERVER3_API_PRIMARY_HOST,
            "port": settings.SERVER3_API_PRIMARY_PORT,
            "protocol": "HTTP REST",
            "online": check_http_endpoint(f"http://{settings.SERVER3_API_PRIMARY_HOST}:{settings.SERVER3_API_PRIMARY_PORT}/api/v1/health")
        },
        {
            "id": "server3_api_backup",
            "name": "Server 3: REST API Katalog (Backup)",
            "role": "FOLLOWER",
            "host": settings.SERVER3_API_BACKUP_HOST,
            "port": settings.SERVER3_API_BACKUP_PORT,
            "protocol": "HTTP REST",
            "online": check_http_endpoint(f"http://{settings.SERVER3_API_BACKUP_HOST}:{settings.SERVER3_API_BACKUP_PORT}/api/v1/health")
        },
        {
            "id": "server4_data_primary",
            "name": "Server 4: Data & Replikasi (Primary)",
            "role": "COORDINATOR",
            "host": settings.SERVER4_DATA_PRIMARY_HOST,
            "port": settings.SERVER4_DATA_PRIMARY_PORT,
            "protocol": "HTTP Data Service",
            "online": check_http_endpoint(f"http://{settings.SERVER4_DATA_PRIMARY_HOST}:{settings.SERVER4_DATA_PRIMARY_PORT}/health")
        },
        {
            "id": "server4_data_backup",
            "name": "Server 4: Data & Replikasi (Backup)",
            "role": "FOLLOWER",
            "host": settings.SERVER4_DATA_BACKUP_HOST,
            "port": settings.SERVER4_DATA_BACKUP_PORT,
            "protocol": "HTTP Data Service",
            "online": check_http_endpoint(f"http://{settings.SERVER4_DATA_BACKUP_HOST}:{settings.SERVER4_DATA_BACKUP_PORT}/health")
        }
    ]

    return {
        "success": True,
        "cluster_healthy": any(n["online"] for n in nodes[:2]) and any(n["online"] for n in nodes[2:4]) and any(n["online"] for n in nodes[4:6]) and any(n["online"] for n in nodes[6:8]),
        "nodes": nodes,
        "timestamp": time.time()
    }

@router.get("/cluster/logs")
def get_cluster_logs():
    """
    Mengambil riwayat peristiwa failover dari tabel cluster_failover_logs.
    """
    sql = """
    SELECT id, service_name, previous_coordinator, promoted_node, reason, event_timestamp, details
    FROM cluster_failover_logs
    ORDER BY event_timestamp DESC
    LIMIT 50
    """
    logs = db_client.query(sql)
    return {"success": True, "data": logs}
