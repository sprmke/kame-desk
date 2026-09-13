export function registerPwa() {
  if (import.meta.env.DEV) return;
  if (!("serviceWorker" in navigator)) return;
  void navigator.serviceWorker.register("/sw.js").catch(() => {});
}
