import { useEffect, useState, type ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { PAGE_TRANSITION } from "@/lib/motion";
import { cn } from "@/lib/utils";

type Props = {
  children: ReactNode;
  transitionKey: string;
  className?: string;
};

export function PageTransition({ children, transitionKey, className }: Props) {
  const reducedMotion = useReducedMotion();
  const [clearTransform, setClearTransform] = useState(false);

  useEffect(() => {
    setClearTransform(false);
  }, [transitionKey]);

  if (reducedMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      key={transitionKey}
      className={cn(className)}
      initial={{ opacity: 0, x: 18 }}
      animate={{ opacity: 1, x: 0 }}
      transition={PAGE_TRANSITION}
      onAnimationComplete={() => setClearTransform(true)}
      style={clearTransform ? { transform: "none" } : undefined}
    >
      {children}
    </motion.div>
  );
}
