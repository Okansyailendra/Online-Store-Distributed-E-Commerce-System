import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import socket
import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx

from backend.common.config import settings
from backend.common.rpc_protocol import encode_frame, decode_frame
from backend.common.logger import setup_logger

logger = setup_logger("WebClient")

app = FastAPI(title="SisterShop Standalone Web Client")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SisterShop — Distributed & High-Availability E-Commerce</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
    </style>
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen flex flex-col">

    <!-- Navbar -->
    <header class="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="h-9 w-9 rounded-xl bg-blue-600 text-white font-extrabold flex items-center justify-center text-xl shadow">S</div>
                <div>
                    <span class="font-extrabold text-lg text-slate-900">Sister<span class="text-blue-600">Shop</span></span>
                    <span class="text-[10px] font-bold text-slate-400 block -mt-1 tracking-wider uppercase">Distributed HA</span>
                </div>
            </div>

            <!-- Cluster Status Pill -->
            <div class="flex items-center gap-3">
                <div id="cluster-indicator" class="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span id="cluster-text">Cluster Normal (HA Aktif)</span>
                </div>
                <button onclick="switchTab('cluster')" class="text-xs font-semibold px-3 py-1.5 rounded-lg border bg-slate-100 hover:bg-slate-200 transition">
                    Audit Cluster
                </button>
            </div>
        </div>
    </header>

    <!-- Failover Toast Alert -->
    <div id="failover-toast" class="hidden fixed bottom-6 right-6 z-50 max-w-md bg-slate-900 text-white p-4 rounded-2xl shadow-2xl border border-purple-500/40">
        <div class="flex items-start gap-3">
            <div class="h-8 w-8 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center shrink-0 font-bold">⚡</div>
            <div class="flex-1">
                <div class="font-bold text-xs text-purple-300">Toleransi Kesalahan Sistem Aktif</div>
                <div id="failover-toast-msg" class="text-xs text-slate-300 mt-0.5">Koneksi dialihkan secara transparan ke Node Cadangan.</div>
            </div>
            <button onclick="document.getElementById('failover-toast').classList.add('hidden')" class="text-slate-400 hover:text-white">✕</button>
        </div>
    </div>

    <!-- Main Content -->
    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-8 w-full space-y-8">
        
        <!-- Navigation Tabs -->
        <div class="flex items-center gap-2 border-b border-slate-200 pb-3">
            <button onclick="switchTab('katalog')" id="tab-btn-katalog" class="px-4 py-2 rounded-xl text-sm font-bold bg-blue-600 text-white">
                Katalog Produk & Belanja
            </button>
            <button onclick="switchTab('cluster')" id="tab-btn-cluster" class="px-4 py-2 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-100">
                Live Cluster & Failover Monitor
            </button>
            <button onclick="switchTab('pesanan')" id="tab-btn-pesanan" class="px-4 py-2 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-100">
                Riwayat Pesanan
            </button>
        </div>

        <!-- TAB 1: KATALOG & CHECKOUT -->
        <section id="tab-katalog" class="space-y-6">
            <div class="bg-gradient-to-r from-slate-900 via-blue-950 to-indigo-950 rounded-3xl p-8 text-white shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div class="max-w-xl space-y-2">
                    <span class="text-xs font-bold text-blue-400 uppercase tracking-widest">Multi-Protocol Architecture</span>
                    <h1 class="text-2xl sm:text-4xl font-extrabold leading-tight">E-Commerce Terdistribusi Tanpa SPOF</h1>
                    <p class="text-xs sm:text-sm text-slate-300">Katalog via REST API, Stok via RMI Pyro5 (OCC Anti-Overselling), dan Checkout atomik via Socket JSON-RPC 2.0.</p>
                </div>
            </div>

            <!-- Product Grid -->
            <div>
                <h2 class="text-xl font-bold mb-4">Daftar Produk Unggulan</h2>
                <div id="product-list" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div class="col-span-full text-center py-12 text-slate-400 text-sm">Memuat katalog dari Node API (:6003)...</div>
                </div>
            </div>
        </section>

        <!-- TAB 2: LIVE CLUSTER MONITOR -->
        <section id="tab-cluster" class="hidden space-y-6">
            <div class="flex justify-between items-center">
                <div>
                    <h2 class="text-xl font-bold text-slate-900">Live Node Health & Failover Audit</h2>
                    <p class="text-xs text-slate-500">Memantau status 8 node aktif-siaga (Thb = 2.0s, Timeout = 5.0s)</p>
                </div>
                <button onclick="fetchClusterStatus()" class="px-3.5 py-1.5 rounded-xl border bg-white hover:bg-slate-50 text-xs font-bold shadow-sm">
                    🔄 Refresh Status
                </button>
            </div>

            <!-- Nodes Grid -->
            <div id="cluster-nodes-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="col-span-full text-center py-8 text-slate-400 text-sm">Memeriksa kesehatan 8 node terdistribusi...</div>
            </div>

            <!-- Failover Logs -->
            <div class="space-y-3 pt-4">
                <h3 class="font-bold text-base text-slate-900">Riwayat Peristiwa Failover (cluster_failover_logs)</h3>
                <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
                    <table class="w-full text-left text-xs">
                        <thead class="bg-slate-50 border-b text-slate-500 font-bold">
                            <tr>
                                <th class="p-3">Waktu</th>
                                <th class="p-3">Layanan</th>
                                <th class="p-3">Koordinator Lama (Down)</th>
                                <th class="p-3">Node Promosi (Active)</th>
                                <th class="p-3">Alasan Deteksi</th>
                            </tr>
                        </thead>
                        <tbody id="failover-logs-body" class="divide-y divide-slate-100">
                            <tr><td colspan="5" class="p-4 text-center text-slate-400">Belum ada peristiwa failover. Seluruh koordinator aktif normal.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- TAB 3: RIWAYAT PESANAN -->
        <section id="tab-pesanan" class="hidden space-y-4">
            <h2 class="text-xl font-bold text-slate-900">Riwayat Pesanan Belanja</h2>
            <div id="orders-list" class="space-y-3">
                <div class="p-8 text-center text-slate-400 text-sm bg-white rounded-2xl border">Memuat riwayat transaksi...</div>
            </div>
        </section>

    </main>

    <!-- Modal Checkout -->
    <div id="checkout-modal" class="hidden fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div class="flex justify-between items-center border-b pb-3">
                <h3 class="font-bold text-base text-slate-900">Konfirmasi Checkout (JSON-RPC)</h3>
                <button onclick="closeCheckoutModal()" class="text-slate-400 hover:text-black">✕</button>
            </div>
            <div id="checkout-prod-info" class="p-3 bg-slate-50 rounded-xl text-xs space-y-1"></div>
            
            <form onsubmit="submitCheckoutRpc(event)" class="space-y-3">
                <div>
                    <label class="block text-xs font-bold mb-1">Alamat Pengiriman</label>
                    <textarea id="co-address" rows="2" class="w-full text-xs p-2.5 border rounded-xl" required>Jl. Raya Telang No. 1, Bangkalan, Madura</textarea>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-xs font-bold mb-1">Kurir</label>
                        <select id="co-courier" class="w-full text-xs p-2.5 border rounded-xl">
                            <option value="JNE Regular">JNE Regular (Rp 15.000)</option>
                            <option value="JNE Express">JNE Express (Rp 20.000)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold mb-1">Pembayaran</label>
                        <select id="co-payment" class="w-full text-xs p-2.5 border rounded-xl">
                            <option value="BANK_TRANSFER">Transfer Bank VA</option>
                            <option value="E_WALLET">QRIS E-Wallet</option>
                        </select>
                    </div>
                </div>
                <button type="submit" id="btn-submit-co" class="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow transition">
                    Eksekusi Checkout RPC Sekarang
                </button>
            </form>
        </div>
    </div>

    <script>
        let currentProducts = [];
        let activeCheckoutProduct = null;

        function formatRupiah(num) {
            return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(num);
        }

        function switchTab(tab) {
            ['katalog', 'cluster', 'pesanan'].forEach(t => {
                document.getElementById('tab-' + t).classList.add('hidden');
                document.getElementById('tab-btn-' + t).className = 'px-4 py-2 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-100';
            });
            document.getElementById('tab-' + tab).classList.remove('hidden');
            document.getElementById('tab-btn-' + tab).className = 'px-4 py-2 rounded-xl text-sm font-bold bg-blue-600 text-white';

            if (tab === 'cluster') fetchClusterStatus();
            if (tab === 'pesanan') fetchOrders();
        }

        async function fetchProducts() {
            try {
                const res = await fetch('/api/products');
                const json = await res.json();
                if (json.success && json.data) {
                    currentProducts = json.data;
                    renderProducts();
                }
            } catch (e) {
                console.error(e);
            }
        }

        function renderProducts() {
            const list = document.getElementById('product-list');
            if (currentProducts.length === 0) {
                list.innerHTML = '<div class="col-span-full text-center py-8 text-slate-400">Tidak ada produk ditemukan.</div>';
                return;
            }
            list.innerHTML = currentProducts.map(p => `
                <div class="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition flex flex-col justify-between">
                    <div>
                        <div class="aspect-square rounded-xl bg-slate-100 overflow-hidden mb-3">
                            <img src="${p.image_url || 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500'}" class="w-full h-full object-cover">
                        </div>
                        <span class="text-[10px] font-bold text-blue-600 uppercase tracking-wider">${p.category_name || 'Produk'}</span>
                        <h3 class="font-bold text-sm text-slate-900 line-clamp-2 mt-0.5">${p.name}</h3>
                        <div class="font-black text-blue-600 text-base mt-1">${formatRupiah(p.price)}</div>
                    </div>
                    <div class="pt-3 mt-3 border-t flex items-center justify-between">
                        <span class="text-xs font-bold ${p.stock > 0 ? 'text-emerald-600' : 'text-red-500'}">
                            ${p.stock > 0 ? 'Stok: ' + p.stock : 'Habis'}
                        </span>
                        <button onclick="openCheckoutModal('${p.id}')" ${p.stock <= 0 ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow transition disabled:bg-slate-200 disabled:text-slate-400">
                            Beli Langsung
                        </button>
                    </div>
                </div>
            `).join('');
        }

        function openCheckoutModal(prodId) {
            activeCheckoutProduct = currentProducts.find(p => p.id === prodId);
            if (!activeCheckoutProduct) return;

            document.getElementById('checkout-prod-info').innerHTML = `
                <div class="font-bold text-slate-900">${activeCheckoutProduct.name}</div>
                <div>Harga: <strong>${formatRupiah(activeCheckoutProduct.price)}</strong> (1 Unit)</div>
                <div class="text-slate-400">SKU: ${activeCheckoutProduct.sku} | Versi OCC: v${activeCheckoutProduct.version || 1}</div>
            `;
            document.getElementById('checkout-modal').classList.remove('hidden');
        }

        function closeCheckoutModal() {
            document.getElementById('checkout-modal').classList.add('hidden');
        }

        async function submitCheckoutRpc(e) {
            e.preventDefault();
            if (!activeCheckoutProduct) return;

            const btn = document.getElementById('btn-submit-co');
            btn.disabled = true;
            btn.innerText = 'Memanggil Socket RPC (Port :6001/:6101)...';

            const courier = document.getElementById('co-courier').value;
            const cost = courier === 'JNE Express' ? 20000 : 15000;

            const payload = {
                product_id: activeCheckoutProduct.id,
                quantity: 1,
                unit_price: activeCheckoutProduct.price,
                shipping_address: document.getElementById('co-address').value,
                shipping_courier: courier,
                shipping_cost: cost,
                payment_method: document.getElementById('co-payment').value
            };

            try {
                const res = await fetch('/api/rpc/checkout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const json = await res.json();

                if (json.success) {
                    if (json.is_failover) {
                        showFailoverToast('Server 1 (RPC): Koordinator Utama terputus. Panggilan RPC otomatis dialihkan ke Node Cadangan (:6101) tanpa error!');
                    }
                    alert(`Transaksi Sukses via RPC!\\nNomor Pesanan: ${json.data.order_number}\\nTotal: ${formatRupiah(json.data.total_amount)}\\nStatus: ${json.data.status}`);
                    closeCheckoutModal();
                    fetchProducts();
                } else {
                    alert('Transaksi Gagal: ' + (json.message || 'Error'));
                }
            } catch (err) {
                alert('Gagal menghubungi gateway RPC: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerText = 'Eksekusi Checkout RPC Sekarang';
            }
        }

        function showFailoverToast(msg) {
            const toast = document.getElementById('failover-toast');
            document.getElementById('failover-toast-msg').innerText = msg;
            toast.classList.remove('hidden');
            setTimeout(() => toast.classList.add('hidden'), 7000);
        }

        async function fetchClusterStatus() {
            try {
                const res = await fetch('/api/cluster/status');
                const json = await res.json();
                if (json.success) {
                    const grid = document.getElementById('cluster-nodes-grid');
                    grid.innerHTML = json.nodes.map(n => `
                        <div class="p-4 rounded-2xl border ${n.online ? 'bg-white border-slate-200' : 'bg-red-50 border-red-200'}">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${n.role === 'COORDINATOR' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'}">${n.role}</span>
                                <span class="text-xs font-bold flex items-center gap-1 ${n.online ? 'text-emerald-600' : 'text-red-500'}">
                                    <span class="h-2 w-2 rounded-full ${n.online ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}"></span>
                                    ${n.online ? 'ONLINE' : 'CRASHED'}
                                </span>
                            </div>
                            <div class="font-extrabold text-xs text-slate-900">${n.name}</div>
                            <div class="text-[11px] text-slate-400 mt-1">Port <strong>:${n.port}</strong> • ${n.protocol}</div>
                        </div>
                    `).join('');

                    // Failover logs
                    const lRes = await fetch('/api/cluster/logs');
                    const lJson = await lRes.json();
                    if (lJson.success && lJson.data.length > 0) {
                        document.getElementById('failover-logs-body').innerHTML = lJson.data.map(l => `
                            <tr class="hover:bg-slate-50">
                                <td class="p-3 text-slate-400">${new Date(l.event_timestamp).toLocaleTimeString()}</td>
                                <td class="p-3 font-bold text-blue-600">${l.service_name}</td>
                                <td class="p-3 font-mono text-red-500">${l.previous_coordinator}</td>
                                <td class="p-3 font-mono text-emerald-600 font-bold">${l.promoted_node}</td>
                                <td class="p-3 text-slate-600">${l.reason}</td>
                            </tr>
                        `).join('');
                    }
                }
            } catch (e) {
                console.error(e);
            }
        }

        async function fetchOrders() {
            try {
                const res = await fetch('/api/orders');
                const json = await res.json();
                const container = document.getElementById('orders-list');
                if (json.success && json.data.length > 0) {
                    container.innerHTML = json.data.map(o => `
                        <div class="p-4 rounded-2xl bg-white border flex justify-between items-center">
                            <div>
                                <div class="font-bold text-sm text-slate-900">${o.order_number}</div>
                                <div class="text-xs text-slate-400">${new Date(o.created_at).toLocaleString()} • ${o.shipping_courier}</div>
                            </div>
                            <div class="text-right">
                                <div class="font-black text-blue-600 text-sm">${formatRupiah(o.total_amount)}</div>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700">${o.status}</span>
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div class="p-8 text-center text-slate-400 text-sm bg-white rounded-2xl border">Belum ada pesanan belanja.</div>';
                }
            } catch (e) {
                console.error(e);
            }
        }

        // Init
        fetchProducts();
        setInterval(fetchProducts, 8000);
    </script>
</body>
</html>
"""

# Client internal proxy router
PRIMARY_API = "http://127.0.0.1:6003"
BACKUP_API = "http://127.0.0.1:6103"

PRIMARY_RPC_PORT = 6001
BACKUP_RPC_PORT = 6101

def tcp_rpc_call(host: str, port: int, payload: dict, timeout=2.0) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
        s.sendall(encode_frame(payload))
        resp = decode_frame(s)
        return resp

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_CONTENT

@app.get("/api/products")
def proxy_products():
    for url in [PRIMARY_API, BACKUP_API]:
        try:
            with httpx.Client(timeout=1.5) as client:
                r = client.get(f"{url}/api/v1/products?limit=24")
                if r.status_code == 200:
                    return r.json()
        except Exception:
            continue
    return {"success": False, "data": []}

@app.get("/api/cluster/status")
def proxy_cluster():
    for url in [PRIMARY_API, BACKUP_API]:
        try:
            with httpx.Client(timeout=1.5) as client:
                r = client.get(f"{url}/api/v1/cluster/status")
                if r.status_code == 200:
                    return r.json()
        except Exception:
            continue
    return {"success": False}

@app.get("/api/cluster/logs")
def proxy_logs():
    for url in [PRIMARY_API, BACKUP_API]:
        try:
            with httpx.Client(timeout=1.5) as client:
                r = client.get(f"{url}/api/v1/cluster/logs")
                if r.status_code == 200:
                    return r.json()
        except Exception:
            continue
    return {"success": False, "data": []}

@app.get("/api/orders")
def proxy_orders():
    # Mengambil seluruh order dari database untuk review langsung
    from backend.common.db_client import db_client
    rows = db_client.query("SELECT id, order_number, total_amount, status, shipping_courier, created_at FROM orders ORDER BY created_at DESC LIMIT 20")
    return {"success": True, "data": rows}

@app.post("/api/rpc/checkout")
async def proxy_rpc_checkout(request: Request):
    data = await request.json()
    idemp_key = "idemp-" + str(socket.gethostname()) + "-" + str(int(socket.socket().fileno() or 1)) + "-" + str(id(data))
    
    # Ambil user demo Budi
    from backend.common.db_client import db_client
    user = db_client.query_one("SELECT id FROM users WHERE email = 'budi@sister.com'")
    user_id = user["id"] if user else "u-demo-1"

    rpc_frame = {
        "jsonrpc": "2.0",
        "id": "req-web-chk",
        "method": "process_checkout",
        "params": {
            "idempotency_key": idemp_key,
            "user_id": user_id,
            "shipping_address": data.get("shipping_address", "Jl. Raya Telang No. 1, Madura"),
            "shipping_courier": data.get("shipping_courier", "JNE Regular"),
            "shipping_cost": data.get("shipping_cost", 15000),
            "payment_method": data.get("payment_method", "BANK_TRANSFER"),
            "items": [
                {
                    "product_id": data["product_id"],
                    "quantity": data["quantity"],
                    "unit_price": data["unit_price"]
                }
            ]
        }
    }

    # 1. Coba hubungi RPC Primary (Port 6001)
    try:
        res = tcp_rpc_call("127.0.0.1", PRIMARY_RPC_PORT, rpc_frame)
        if "result" in res:
            return {"success": True, "data": res["result"], "is_failover": False}
        return {"success": False, "message": str(res.get("error", "Error RPC"))}
    except Exception as primary_err:
        logger.warning(f"[FAILOVER ROUTER] RPC Primary gagal ({primary_err}). Beralih ke Backup :6101...")
        # 2. Coba hubungi RPC Backup (Port 6101)
        try:
            res = tcp_rpc_call("127.0.0.1", BACKUP_RPC_PORT, rpc_frame)
            if "result" in res:
                return {"success": True, "data": res["result"], "is_failover": True}
            return {"success": False, "message": str(res.get("error", "Error RPC Backup"))}
        except Exception as backup_err:
            return {"success": False, "message": f"Seluruh node RPC mati: {backup_err}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="warning")
