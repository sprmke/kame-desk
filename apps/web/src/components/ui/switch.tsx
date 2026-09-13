import * as React from "react";
import * as SwitchPrimitive from "@radix-ui/react-switch";
import { cn } from "@/lib/utils";

function Switch({
  className,
  ...props
}: React.ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      className={cn(
        "peer inline-flex h-6 w-11 shrink-0 cursor-pointer touch-manipulation items-center rounded-full border-2 border-transparent shadow-theme-xs transition-colors duration-150 ease-theme outline-none",
        "hover:data-[state=unchecked]:bg-input/80",
        "focus-visible:ring-2 focus-visible:ring-ring/40",
        "data-[state=checked]:bg-primary data-[state=unchecked]:bg-input",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className={cn(
          "pointer-events-none block size-5 rounded-full bg-white shadow-theme-sm ring-0 transition-transform duration-[180ms] ease-out-quart motion-reduce:transition-none",
          "data-[state=checked]:translate-x-[1.25rem] data-[state=unchecked]:translate-x-0.5",
        )}
      />
    </SwitchPrimitive.Root>
  );
}

export { Switch };
