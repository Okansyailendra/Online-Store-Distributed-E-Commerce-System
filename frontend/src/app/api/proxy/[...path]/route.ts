import { NextRequest, NextResponse } from "next/server";

const PRIMARY_API = process.env.SERVER3_API_PRIMARY_URL || "http://127.0.0.1:6003";
const BACKUP_API = process.env.SERVER3_API_BACKUP_URL || "http://127.0.0.1:6103";

async function forwardRequest(req: NextRequest, targetBase: string, path: string[]) {
  const url = new URL(req.url);
  const targetUrl = `${targetBase}/api/v1/${path.join("/")}${url.search}`;

  const headers: Record<string, string> = {};
  req.headers.forEach((value, key) => {
    if (key.toLowerCase() !== "host") {
      headers[key] = value;
    }
  });

  const body = req.method !== "GET" && req.method !== "HEAD" ? await req.text() : undefined;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 2000); // Timeout 2.0 detik

  try {
    const response = await fetch(targetUrl, {
      method: req.method,
      headers,
      body,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}

async function handleProxy(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path || [];

  // 1. Coba hubungi Node Koordinator (Primary :6003)
  try {
    const primaryRes = await forwardRequest(req, PRIMARY_API, path);
    const data = await primaryRes.text();
    return new NextResponse(data, {
      status: primaryRes.status,
      headers: {
        "Content-Type": primaryRes.headers.get("Content-Type") || "application/json",
        "X-Served-By": "Primary",
        "X-Failover-Triggered": "false",
      },
    });
  } catch (primaryError) {
    console.warn(`[FAILOVER ROUTER] Panggilan ke API Primary gagal (${primaryError}). Mengalihkan ke Backup...`);

    // 2. Transparan Failover ke Node Pengikut (Backup :6103)
    try {
      const backupRes = await forwardRequest(req, BACKUP_API, path);
      const data = await backupRes.text();
      return new NextResponse(data, {
        status: backupRes.status,
        headers: {
          "Content-Type": backupRes.headers.get("Content-Type") || "application/json",
          "X-Served-By": "Backup",
          "X-Failover-Triggered": "true",
        },
      });
    } catch (backupError: any) {
      console.error("[FAILOVER ROUTER] Seluruh node API tidak dapat dihubungi:", backupError);
      return NextResponse.json(
        {
          success: false,
          error_code: "ALL_NODES_DOWN",
          message: "Layanan katalog sedang tidak tersedia pada kedua node.",
        },
        { status: 503 }
      );
    }
  }
}

export const GET = handleProxy;
export const POST = handleProxy;
export const PUT = handleProxy;
export const PATCH = handleProxy;
export const DELETE = handleProxy;
