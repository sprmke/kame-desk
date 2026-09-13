import { motion, useReducedMotion } from "framer-motion";
import { SLIDING_PILL_SPRING } from "@/lib/motion";
import { cn } from "@/lib/utils";
import type { SlidingPillBounds } from "@/hooks/useSlidingActivePill";

type Props = {
  bounds: SlidingPillBounds;
  className?: string;
};

export function SlidingActivePill({ bounds, className }: Props) {
  const reducedMotion = useReducedMotion();
  const classNames = cn(
    "pointer-events-none absolute z-0 rounded-md bg-card shadow-theme-xs",
    className,
  );

  if (reducedMotion) {
    return (
      <div
        aria-hidden
        className={classNames}
        style={{
          left: bounds.left,
          top: bounds.top,
          width: bounds.width,
          height: bounds.height,
        }}
      />
    );
  }

  return (
    <motion.div
      aria-hidden
      className={classNames}
      initial={false}
      animate={{
        left: bounds.left,
        top: bounds.top,
        width: bounds.width,
        height: bounds.height,
      }}
      transition={SLIDING_PILL_SPRING}
    />
  );
}
