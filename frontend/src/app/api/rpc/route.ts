import { NextRequest, NextResponse } from "next/server";
import net from "net";

const RPC_PRIMARY_HOST = process.env.SERVER1_RPC_PRIMARY_HOST || "127.0.0.1";
const RPC_PRIMARY_PORT = parseInt(process.env.SERVER1_RPC_PRIMARY_PORT || "6001", 10);

const RPC_BACKUP_HOST = process.env.SERVER1_RPC_BACKUP_HOST || "127.0.0.1";
const RPC_BACKUP_PORT = parseInt(process.env.SERVER1_RPC_BACKUP_PORT || "6101", 10);

function sendTcpRpc(host: string, port: number, payload: any, timeoutMs = 2000): Promise<any> {
  return new Promise((resolve, reject) => {
    const client = new net.Socket();
    let settled = false;

    const timer = setTimeout(() => {
      if (!settled) {
        settled = true;
        client.destroy();
        reject(new Error(`Timeout connecting to RPC at ${host}:${port}`));
      }
    }, timeoutMs);

    client.connect(port, host, () => {
      const jsonBody = Buffer.from(JSON.stringify(payload), "utf-8");
      const header = Buffer.alloc(4);
      header.writeUInt32BE(jsonBody.length, 0);

      client.write(Buffer.concat([header, jsonBody]));
    });

    let buffer = Buffer.alloc(0);
    let expectedLength: number | null = null;

    client.on("data", (chunk) => {
      buffer = Buffer.concat([buffer, chunk]);

      if (expectedLength === null && buffer.length >= 4) {
        expectedLength = buffer.readUInt32BE(0);
        buffer = buffer.subarray(4);
      }

      if (expectedLength !== null && buffer.length >= expectedLength) {
        if (!settled) {
          settled = true;
          clearTimeout(timer);
          client.destroy();
          try {
            const bodyStr = buffer.subarray(0, expectedLength).toString("utf-8");
            const parsed = JSON.parse(bodyStr);
            resolve(parsed);
          } catch (e) {
            reject(new Error("Failed to parse RPC response JSON"));
          }
        }
      }
    });

    client.on("error", (err) => {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        client.destroy();
        reject(err);
      }
    });

    client.on("close", () => {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        reject(new Error("Connection closed before response received"));
      }
    });
  });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const method = body.method;
    const params = body.params || {};

    const rpcFrame = {
      jsonrpc: "2.0",
      id: `web-${Date.now()}`,
      method,
      params,
    };

    // 1. Coba hubungi Koordinator RPC Primary (Port 6001)
    try {
      const res = await sendTcpRpc(RPC_PRIMARY_HOST, RPC_PRIMARY_PORT, rpcFrame);
      if (res.error) {
        return NextResponse.json({
          success: false,
          error_code: res.error.message || "RPC_ERROR",
          message: res.error.message,
          data: res.error.data,
          is_failover: false,
        });
      }
      return NextResponse.json({
        success: true,
        data: res.result,
        is_failover: false,
        served_by: "Primary RPC (:6001)",
      });
    } catch (primaryErr) {
      console.warn(`[RPC FAILOVER] Primary RPC (${RPC_PRIMARY_HOST}:${RPC_PRIMARY_PORT}) gagal (${primaryErr}). Beralih ke Backup...`);

      // 2. Transparan Failover ke Pengikut RPC Backup (Port 6101)
      try {
        const backupRes = await sendTcpRpc(RPC_BACKUP_HOST, RPC_BACKUP_PORT, rpcFrame);
        if (backupRes.error) {
          return NextResponse.json({
            success: false,
            error_code: backupRes.error.message || "RPC_ERROR",
            message: backupRes.error.message,
            data: backupRes.error.data,
            is_failover: true,
          });
        }
        return NextResponse.json({
          success: true,
          data: backupRes.result,
          is_failover: true,
          served_by: "Backup RPC (:6101)",
        });
      } catch (backupErr: any) {
        console.error("[RPC FAILOVER FAILED] Kedua node RPC tidak dapat dijangkau:", backupErr);
        return NextResponse.json(
          {
            success: false,
            error_code: "RPC_NODES_DOWN",
            message: "Layanan transaksi RPC sedang tidak tersedia pada kedua node.",
          },
          { status: 503 }
        );
      }
    }
  } catch (err: any) {
    return NextResponse.json(
      {
        success: false,
        message: err.message || "Invalid request payload",
      },
      { status: 400 }
    );
  }
}
