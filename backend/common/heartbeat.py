import socket
import json
import time
import threading
from typing import Callable, Optional
from backend.common.logger import setup_logger

logger = setup_logger("Heartbeat")

class HeartbeatEmitter:
    """
    Dijalankan oleh Node COORDINATOR (Primary).
    Memancarkan sinyal detak jantung secara periodik ke Node Pengikut (Follower).
    """
    def __init__(self, target_host: str, target_port: int, sender_id: str, interval: float = 2.0):
        self.target_host = target_host
        self.target_port = target_port
        self.sender_id = sender_id
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._seq = 0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name=f"HBEmitter-{self.sender_id}")
        self._thread.start()
        logger.info(f"[HEARTBEAT] Emitter aktif -> target {self.target_host}:{self.target_port} (Interval {self.interval}s)")

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info(f"[HEARTBEAT] Emitter dihentikan untuk {self.sender_id}")

    def _run_loop(self):
        while self._running:
            self._seq += 1
            payload = {
                "type": "HEARTBEAT",
                "sender": self.sender_id,
                "seq": self._seq,
                "timestamp": time.time()
            }
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.0)
                    s.connect((self.target_host, self.target_port))
                    msg = json.dumps(payload).encode("utf-8") + b"\n"
                    s.sendall(msg)
            except (ConnectionRefusedError, socket.timeout, OSError):
                # Follower mungkin belum menyala atau restart, abaikan error sesaat
                pass
            time.sleep(self.interval)


class HeartbeatListener:
    """
    Dijalankan oleh Node FOLLOWER (Backup).
    Mendengarkan sinyal detak jantung dari Koordinator. Jika detak hilang selama
    timeout (default 5.0 detik) atau melebihi max_missed (3x), memicu callback promosi.
    """
    def __init__(
        self,
        listen_host: str,
        listen_port: int,
        node_id: str,
        timeout: float = 5.0,
        interval: float = 2.0,
        max_missed: int = 3,
        on_failure: Optional[Callable[[], None]] = None
    ):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.node_id = node_id
        self.timeout = timeout
        self.interval = interval
        self.max_missed = max_missed
        self.on_failure = on_failure

        self._running = False
        self._server_sock: Optional[socket.socket] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._checker_thread: Optional[threading.Thread] = None
        self.last_heartbeat_time = time.time()
        self.has_received_first_heartbeat = False
        self._promoted = False

    def start(self):
        if self._running:
            return
        self._running = True
        self.last_heartbeat_time = time.time()
        
        # Mulai Socket Listener
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True, name=f"HBListener-{self.node_id}")
        self._listener_thread.start()

        # Mulai Timeout Watchdog Checker
        self._checker_thread = threading.Thread(target=self._watchdog_loop, daemon=True, name=f"HBWatchdog-{self.node_id}")
        self._checker_thread.start()
        logger.info(f"[HEARTBEAT] Listener siaga di {self.listen_host}:{self.listen_port} (Timeout: {self.timeout}s, Miss threshold: {self.max_missed})")

    def stop(self):
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
        logger.info(f"[HEARTBEAT] Listener dihentikan untuk {self.node_id}")

    def _listen_loop(self):
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind((self.listen_host, self.listen_port))
            self._server_sock.listen(5)
            self._server_sock.settimeout(1.0)
        except Exception as e:
            logger.error(f"[HEARTBEAT] Gagal bind listener pada {self.listen_host}:{self.listen_port}: {e}")
            return

        while self._running:
            try:
                conn, _ = self._server_sock.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        lines = data.decode("utf-8").strip().split("\n")
                        for line in lines:
                            if not line:
                                continue
                            try:
                                msg = json.loads(line)
                                if msg.get("type") == "HEARTBEAT":
                                    self.last_heartbeat_time = time.time()
                                    self.has_received_first_heartbeat = True
                            except json.JSONDecodeError:
                                pass
            except socket.timeout:
                continue
            except Exception:
                if not self._running:
                    break

    def _watchdog_loop(self):
        # Berikan grace period 3 detik saat awal booting agar koordinator sempat mengirim detak
        time.sleep(3.0)
        while self._running and not self._promoted:
            time.sleep(0.5)
            elapsed = time.time() - self.last_heartbeat_time
            missed_beats = int(elapsed // self.interval)

            if elapsed >= self.timeout:
                logger.warning(f"[FAILOVER DETECTED] Detak jantung hilang selama {elapsed:.2f}s ({missed_beats} detak terlewat)! Batas timeout {self.timeout}s terlampaui.")
                self._promoted = True
                self.stop()
                if self.on_failure:
                    self.on_failure()
                break
