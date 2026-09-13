/** Local dev defaults: web :3100, API :8100 (avoids clashes with other projects on :3000). */
export const API_BASE =
  import.meta.env.VITE_API_URL ?? "http://localhost:8100/api/v1";

export const API_WS_BASE = API_BASE.replace("/api/v1", "");
