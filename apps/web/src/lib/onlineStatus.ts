import { useSyncExternalStore } from "react";

function getSnapshot(): boolean {
  if (typeof navigator === "undefined") return true;
  return navigator.onLine;
}

function getServerSnapshot(): boolean {
  return true;
}

function subscribe(callback: () => void): () => void {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

/** True when the browser reports a network connection. SSR-safe (assumes online on the server). */
export function useOnlineStatus(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
