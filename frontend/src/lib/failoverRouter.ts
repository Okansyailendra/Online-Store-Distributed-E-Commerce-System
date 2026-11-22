/**
 * Smart Failover Client Request Handler
 * Menangani pemanggilan REST API ke Server 3 dengan transparansi failover (Primary :6003 -> Backup :6103).
 */

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  meta?: any;
  message?: string;
  error_code?: string;
  is_failover?: boolean;
  served_by?: string;
}

export async function apiFetch<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  // Gunakan Internal Next.js Proxy Route untuk menjamin keamanan & kestabilan
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const proxyUrl = `/api/proxy${cleanEndpoint}`;

  try {
    const res = await fetch(proxyUrl, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });

    const isFailover = res.headers.get("X-Failover-Triggered") === "true";
    const servedBy = res.headers.get("X-Served-By") || "Primary";

    const json = await res.json();

    return {
      ...json,
      is_failover: isFailover,
      served_by: servedBy,
    };
  } catch (error: any) {
    console.error(`[API FETCH ERROR] ${cleanEndpoint}:`, error);
    return {
      success: false,
      message: error.message || "Gagal menghubungi layanan API",
    };
  }
}
