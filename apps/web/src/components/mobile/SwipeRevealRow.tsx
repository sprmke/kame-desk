import {
  useCallback,
  useRef,
  useState,
  type PointerEvent,
  type ReactNode,
} from "react";
import { useIsBelowLg, usePrefersReducedMotion } from "@/hooks/useMediaQuery";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type SwipeRevealAction = {
  key: string;
  label: string;
  variant?: "default" | "destructive" | "outline";
  onClick: () => void;
};

type Props = {
  children: ReactNode;
  actions: SwipeRevealAction[];
  className?: string;
  disabled?: boolean;
};

const ACTION_WIDTH = 88;
const OPEN_THRESHOLD = 48;

/**
 * Swipe-to-reveal, not swipe-to-execute. A second tap runs the action.
 * Phone/tablet only; desktop renders children unchanged.
 */
export function SwipeRevealRow({
  children,
  actions,
  className,
  disabled,
}: Props) {
  const isBelowLg = useIsBelowLg();
  const reducedMotion = usePrefersReducedMotion();
  const enabled = isBelowLg && !disabled && actions.length > 0;
  const maxOpen = actions.length * ACTION_WIDTH;

  const [offset, setOffset] = useState(0);
  const startX = useRef(0);
  const startY = useRef(0);
  const startOffset = useRef(0);
  const axis = useRef<"undecided" | "x" | "y">("undecided");
  const dragging = useRef(false);

  const close = useCallback(() => setOffset(0), []);

  function onPointerDown(event: PointerEvent<HTMLDivElement>) {
    if (!enabled) return;
    dragging.current = true;
    axis.current = "undecided";
    startX.current = event.clientX;
    startY.current = event.clientY;
    startOffset.current = offset;
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event: PointerEvent<HTMLDivElement>) {
    if (!enabled || !dragging.current) return;
    const dx = event.clientX - startX.current;
    const dy = event.clientY - startY.current;

    if (axis.current === "undecided") {
      if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
      axis.current = Math.abs(dx) > Math.abs(dy) ? "x" : "y";
    }
    if (axis.current !== "x") return;

    event.preventDefault();
    const next = Math.min(0, Math.max(-maxOpen, startOffset.current + dx));
    setOffset(next);
  }

  function onPointerUp() {
    if (!enabled || !dragging.current) return;
    dragging.current = false;
    if (axis.current !== "x") {
      axis.current = "undecided";
      return;
    }
    axis.current = "undecided";
    setOffset((current) => (current < -OPEN_THRESHOLD ? -maxOpen : 0));
  }

  if (!enabled) {
    return <div className={className}>{children}</div>;
  }

  return (
    <div className={cn("relative overflow-hidden", className)}>
      <div
        className="absolute inset-y-0 right-0 flex"
        aria-hidden={offset === 0}
      >
        {actions.map((action) => (
          <Button
            key={action.key}
            type="button"
            variant={action.variant ?? "outline"}
            className="h-full min-h-[44px] rounded-none px-3"
            style={{ width: ACTION_WIDTH }}
            onClick={() => {
              close();
              action.onClick();
            }}
          >
            {action.label}
          </Button>
        ))}
      </div>
      <div
        className="relative z-[1] bg-card touch-pan-y"
        style={{
          transform: `translateX(${offset}px)`,
          transition:
            reducedMotion || dragging.current
              ? "none"
              : "transform 0.22s cubic-bezier(0.22, 1, 0.36, 1)",
        }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
      >
        {children}
      </div>
    </div>
  );
}
