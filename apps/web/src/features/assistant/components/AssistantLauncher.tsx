import { useEffect, useState } from "react";
import { AssistantMark } from "@/components/brand/AssistantMark";
import { AssistantPanel } from "@/features/assistant/components/AssistantPanel";
import { aboveBottomTabBarClassName } from "@/components/mobile/BottomTabBar";
import { cn } from "@/lib/utils";

export function AssistantLauncher({ className }: { className?: string }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    function onOpen() {
      setOpen(true);
    }
    window.addEventListener("doctordesk:open-assistant", onOpen);
    return () =>
      window.removeEventListener("doctordesk:open-assistant", onOpen);
  }, []);

  return (
    <>
      <button
        type="button"
        className={cn(
          "fixed right-4 z-40 flex size-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-theme-lg native-press",
          aboveBottomTabBarClassName(),
          className,
        )}
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close clinic assistant" : "Open clinic assistant"}
        aria-expanded={open}
        aria-controls="clinic-assistant-panel"
      >
        <AssistantMark className="size-5" />
      </button>
      {open ? <AssistantPanel onClose={() => setOpen(false)} /> : null}
    </>
  );
}
