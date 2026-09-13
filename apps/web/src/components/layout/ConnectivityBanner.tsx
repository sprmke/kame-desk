import { useEffect, useRef, useState } from "react";
import { WifiOff, RefreshCw } from "lucide-react";
import { useOnlineStatus } from "@/lib/onlineStatus";

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-PH", {
    timeZone: "Asia/Manila",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function ConnectivityBanner() {
  const online = useOnlineStatus();
  const [offlineSince, setOfflineSince] = useState<Date | null>(null);
  const [showReconnected, setShowReconnected] = useState(false);
  const wasOfflineRef = useRef(false);

  // Depends only on `online` — setting offlineSince/showReconnected here must
  // not re-trigger this same effect, or the reconnect timer gets cleared by
  // its own cleanup before it fires.
  useEffect(() => {
    if (!online) {
      wasOfflineRef.current = true;
      setOfflineSince((prev) => prev ?? new Date());
      setShowReconnected(false);
      return;
    }
    setOfflineSince(null);
    if (wasOfflineRef.current) {
      wasOfflineRef.current = false;
      setShowReconnected(true);
      const timer = setTimeout(() => setShowReconnected(false), 4000);
      return () => clearTimeout(timer);
    }
  }, [online]);

  if (!online) {
    return (
      <div className="flex items-center gap-2 bg-warning-100 px-4 py-2 text-sm text-warning-900">
        <WifiOff className="size-4 shrink-0" />
        <span>
          You&apos;re offline. Viewing cached data
          {offlineSince ? ` as of ${formatTime(offlineSince)}` : ""}. Booking,
          billing, and prescriptions require a connection.
        </span>
      </div>
    );
  }

  if (showReconnected) {
    return (
      <div className="flex items-center gap-2 bg-success-100 px-4 py-2 text-sm text-success-900">
        <RefreshCw className="size-4 shrink-0" />
        <span>Reconnected, syncing…</span>
      </div>
    );
  }

  return null;
}
