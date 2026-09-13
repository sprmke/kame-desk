import { Children, isValidElement, type ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  DURATION_TRANSITION_S,
  EASE_OUT_QUART,
  listItemDelay,
} from "@/lib/motion";
import { cn } from "@/lib/utils";

type Props = {
  children: ReactNode;
  className?: string;
};

export function StaggeredList({ children, className }: Props) {
  const reducedMotion = useReducedMotion();
  const items = Children.toArray(children);

  return (
    <ul className={cn("flex flex-col divide-y divide-border", className)}>
      {items.map((child, index) => (
        <motion.li
          key={
            isValidElement(child) && child.key != null
              ? String(child.key)
              : index
          }
          initial={reducedMotion ? false : { opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: DURATION_TRANSITION_S,
            delay: listItemDelay(index, Boolean(reducedMotion)),
            ease: EASE_OUT_QUART,
          }}
        >
          {child}
        </motion.li>
      ))}
    </ul>
  );
}
