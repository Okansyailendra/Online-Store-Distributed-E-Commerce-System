import httpx
import time
from typing import Optional, Any
from backend.common.config import settings
from backend.common.logger import setup_logger

logger = setup_logger("DBClient")

class DatabaseClient:
    """
    HTTP Client untuk mengakses data service (server4_data) dengan
    dukungan transparent failover antara Primary (:6004) dan Backup (:6104).
    """
    def __init__(self):
        self.primary_url = f"http://{settings.SERVER4_DATA_PRIMARY_HOST}:{settings.SERVER4_DATA_PRIMARY_PORT}"
        self.backup_url = f"http://{settings.SERVER4_DATA_BACKUP_HOST}:{settings.SERVER4_DATA_BACKUP_PORT}"
        self.active_url = self.primary_url
        self.timeout = settings.SOCKET_TIMEOUT

    def _get_client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout)

    def _request_with_failover(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.active_url}{endpoint}"
        try:
            with self._get_client() as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                raise RuntimeError(f"Database service returned HTTP {resp.status_code}: {resp.text}")
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as err:
            # Ganti rute ke backup atau sebaliknya
            prev_url = self.active_url
            self.active_url = self.backup_url if self.active_url == self.primary_url else self.primary_url
            logger.warning(f"[FAILOVER ROUTING] Koneksi ke data service {prev_url} gagal ({err}). Beralih ke {self.active_url}...")
            
            # Coba request sekali lagi ke rute baru
            url_backup = f"{self.active_url}{endpoint}"
            with self._get_client() as client:
                resp = client.post(url_backup, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                raise RuntimeError(f"Backup data service returned HTTP {resp.status_code}: {resp.text}")

    def query(self, sql: str, params: Optional[dict] = None) -> list[dict]:
        payload = {"sql": sql, "params": params or {}}
        res = self._request_with_failover("/internal/db/query", payload)
        return res.get("rows", [])

    def query_one(self, sql: str, params: Optional[dict] = None) -> Optional[dict]:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def execute(self, sql: str, params: Optional[dict] = None) -> int:
        payload = {"sql": sql, "params": params or {}}
        res = self._request_with_failover("/internal/db/execute", payload)
        return res.get("affected_rows", 0)

    def execute_transaction(self, statements: list[dict]) -> bool:
        """
        Menjalankan kumpulan query dalam 1 atomic transaction.
        statements: [{"sql": str, "params": dict}, ...]
        """
        payload = {"statements": statements}
        res = self._request_with_failover("/internal/db/transaction", payload)
        return res.get("success", False)

    def record_failover_log(self, log_entry: dict):
        sql = """
        INSERT INTO cluster_failover_logs (id, service_name, previous_coordinator, promoted_node, reason, event_timestamp, details)
        VALUES (:id, :service_name, :previous_coordinator, :promoted_node, :reason, :event_timestamp, :details)
        """
        try:
            self.execute(sql, log_entry)
        except Exception as e:
            logger.error(f"[DBClient] Gagal menyimpan cluster_failover_log: {e}")

db_client = DatabaseClient()
