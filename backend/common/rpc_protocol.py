import socket
import struct
import json
import threading
from typing import Callable, Any, Optional
from backend.common.logger import setup_logger

logger = setup_logger("RPCProtocol")

class RPCError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

def encode_frame(payload: dict) -> bytes:
    """
    Membungkus payload JSON dengan 4-byte big-endian length prefix.
    """
    body = json.dumps(payload).encode("utf-8")
    length = len(body)
    header = struct.pack(">I", length)
    return header + body

def decode_frame(sock: socket.socket) -> Optional[dict]:
    """
    Membaca frame dari socket: 4 bytes length prefix lalu tepat N bytes body.
    """
    header_data = b""
    while len(header_data) < 4:
        chunk = sock.recv(4 - len(header_data))
        if not chunk:
            return None
        header_data += chunk

    payload_len = struct.unpack(">I", header_data)[0]
    
    # Baca payload tepat sebesar payload_len
    body_data = b""
    while len(body_data) < payload_len:
        chunk = sock.recv(min(4096, payload_len - len(body_data)))
        if not chunk:
            return None
        body_data += chunk

    return json.loads(body_data.decode("utf-8"))


class RPCClient:
    """
    Klien RPC berkemampuan koneksi cepat dengan timeout presisi.
    """
    @staticmethod
    def call(host: str, port: int, method: str, params: dict, request_id: str = "req-1", timeout: float = 1.5) -> dict:
        req_frame = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        data = encode_frame(req_frame)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.sendall(data)
            
            resp = decode_frame(sock)
            if resp is None:
                raise RPCError(-32603, "Internal RPC Error: No response received from server")
            
            if "error" in resp:
                err = resp["error"]
                raise RPCError(err.get("code", -32000), err.get("message", "Unknown RPC Error"), err.get("data"))
            
            return resp.get("result", {})


class RPCServer:
    """
    TCP Socket JSON-RPC 2.0 Server yang mendukung multi-threading per client connection.
    """
    def __init__(self, host: str, port: int, server_name: str = "RPCServer"):
        self.host = host
        self.port = port
        self.server_name = server_name
        self.methods: dict[str, Callable[[dict], Any]] = {}
        self._server_sock: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def register_method(self, name: str, handler: Callable[[dict], Any]):
        self.methods[name] = handler

    def start(self):
        if self._running:
            return
        self._running = True
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen(128)
        self._server_sock.settimeout(1.0)

        self._thread = threading.Thread(target=self._accept_loop, daemon=True, name=f"{self.server_name}-Acceptor")
        self._thread.start()
        logger.info(f"[{self.server_name}] Mendengarkan panggilan RPC pada {self.host}:{self.port}")

    def stop(self):
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
        logger.info(f"[{self.server_name}] Server dihentikan pada port {self.port}")

    def _accept_loop(self):
        while self._running:
            try:
                client_sock, client_addr = self._server_sock.accept()
                threading.Thread(target=self._handle_client, args=(client_sock, client_addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                if not self._running:
                    break

    def _handle_client(self, sock: socket.socket, addr):
        with sock:
            sock.settimeout(10.0)
            while self._running:
                try:
                    req = decode_frame(sock)
                    if req is None:
                        break
                    
                    req_id = req.get("id", "null")
                    method_name = req.get("method")
                    params = req.get("params", {})

                    if method_name not in self.methods:
                        err_resp = {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "error": {
                                "code": -32601,
                                "message": f"Method '{method_name}' not found"
                            }
                        }
                        sock.sendall(encode_frame(err_resp))
                        continue

                    # Eksekusi method
                    try:
                        handler = self.methods[method_name]
                        result = handler(params)
                        resp = {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "result": result
                        }
                    except RPCError as rpc_err:
                        resp = {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "error": {
                                "code": rpc_err.code,
                                "message": rpc_err.message,
                                "data": rpc_err.data
                            }
                        }
                    except Exception as ex:
                        logger.error(f"[{self.server_name}] Error eksekusi method '{method_name}': {ex}")
                        resp = {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "error": {
                                "code": -32000,
                                "message": str(ex)
                            }
                        }

                    sock.sendall(encode_frame(resp))
                except (ConnectionResetError, socket.timeout):
                    break
                except Exception as ex:
                    logger.debug(f"[{self.server_name}] Exception koneksi dari {addr}: {ex}")
                    break
