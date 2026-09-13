import { useCallback, useState } from "react";
import { api } from "@/lib/apiClient";

function urlBase64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  const output = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) {
    output[i] = raw.charCodeAt(i);
  }
  return output;
}

export function usePushNotifications(vapidPublicKey: string | undefined) {
  const [status, setStatus] = useState<"idle" | "enabled" | "unsupported">(
    "idle",
  );

  const subscribe = useCallback(async () => {
    if (
      !vapidPublicKey ||
      !("serviceWorker" in navigator) ||
      !("PushManager" in window)
    ) {
      setStatus("unsupported");
      return;
    }
    const permission = await Notification.requestPermission();
    if (permission !== "granted") return;

    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
    });
    const json = sub.toJSON();
    await api.registerPushSubscription({
      endpoint: json.endpoint!,
      keys: {
        p256dh: json.keys!.p256dh!,
        auth: json.keys!.auth!,
      },
    });
    setStatus("enabled");
  }, [vapidPublicKey]);

  return { status, subscribe };
}
