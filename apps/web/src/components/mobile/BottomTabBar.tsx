import type { ComponentType } from "react";
import { Link } from "@tanstack/react-router";
import { MoreHorizontal } from "lucide-react";
import { SlidingActivePill } from "@/components/ui/sliding-active-pill";
import { useSlidingActivePill } from "@/hooks/useSlidingActivePill";
import { cn } from "@/lib/utils";

export type BottomTabItem = {
  key: string;
  label: string;
  to?: string;
  Icon: ComponentType<{ className?: string; strokeWidth?: number }>;
  onClick?: () => void;
};

type Props = {
  items: BottomTabItem[];
  activeKey: string | null;
  className?: string;
  "aria-label"?: string;
};

export const MORE_TAB_KEY = "more";

export function moreTabItem(onClick: () => void): BottomTabItem {
  return {
    key: MORE_TAB_KEY,
    label: "More",
    Icon: MoreHorizontal,
    onClick,
  };
}

export function bottomTabBarOffsetClassName(): string {
  return "max-lg:pb-[calc(6.75rem+env(safe-area-inset-bottom,0px))]";
}

export function aboveBottomTabBarClassName(): string {
  return "max-lg:bottom-[calc(5.5rem+env(safe-area-inset-bottom,0px))] lg:bottom-4";
}

export function BottomTabBar({
  items,
  activeKey,
  className,
  "aria-label": ariaLabel = "Main",
}: Props) {
  const { containerRef, setItemRef, bounds } = useSlidingActivePill(activeKey, [
    items.map((item) => item.key).join("\0"),
  ]);

  return (
    <nav
      data-testid="bottom-tab-bar"
      className={cn(
        "pointer-events-none fixed inset-x-0 bottom-0 z-40 lg:hidden",
        "px-3 pb-[max(0.625rem,env(safe-area-inset-bottom))]",
        "touch-manipulation",
        className,
      )}
    >
      <div
        className={cn(
          "pointer-events-auto mx-auto w-full max-w-md",
          "rounded-2xl border border-border bg-card shadow-theme-md",
        )}
      >
        <div
          ref={containerRef}
          className="relative flex items-stretch justify-around gap-0.5 px-1.5 py-1"
          role="list"
        >
          {bounds ? (
            <SlidingActivePill
              bounds={bounds}
              className="rounded-xl bg-primary shadow-none"
            />
          ) : null}
          {items.map((item) => {
            const active = item.key === activeKey;
            const Icon = item.Icon;
            const sharedClass = cn(
              "relative z-[1] flex min-h-[48px] min-w-0 flex-1 flex-col items-center justify-center gap-0.5",
              "rounded-xl px-1 py-1 native-press",
              active ? "text-primary-foreground" : "text-muted-foreground",
            );

            const content = (
              <>
                <Icon
                  strokeWidth={1.75}
                  className="size-[18px] shrink-0"
                  aria-hidden
                />
                <span
                  className={cn(
                    "w-full truncate text-center text-[10px] leading-none tracking-tight",
                    active ? "font-semibold" : "font-medium",
                  )}
                >
                  {item.label}
                </span>
              </>
            );

            if (item.onClick || !item.to) {
              return (
                <button
                  key={item.key}
                  ref={setItemRef(item.key)}
                  type="button"
                  role="listitem"
                  onClick={item.onClick}
                  aria-current={active ? "page" : undefined}
                  aria-label={item.label}
                  aria-expanded={item.onClick ? active : undefined}
                  className={sharedClass}
                >
                  {content}
                </button>
              );
            }

            return (
              <div
                key={item.key}
                ref={setItemRef(item.key)}
                className="flex min-w-0 flex-1"
                role="listitem"
              >
                <Link
                  to={item.to}
                  aria-current={active ? "page" : undefined}
                  aria-label={item.label}
                  className={cn(sharedClass, "w-full")}
                >
                  {content}
                </Link>
              </div>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
