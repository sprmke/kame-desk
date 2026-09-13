import * as React from "react";
import * as CheckboxPrimitive from "@radix-ui/react-checkbox";
import { CheckIcon, MinusIcon } from "lucide-react";
import { cn } from "@/lib/utils";

function Checkbox({
  className,
  ...props
}: React.ComponentProps<typeof CheckboxPrimitive.Root>) {
  return (
    <CheckboxPrimitive.Root
      data-slot="checkbox"
      className={cn(
        "peer size-[18px] shrink-0 cursor-pointer touch-manipulation rounded-[5px] border-2 border-muted-foreground/45 bg-card shadow-theme-xs outline-none transition-[color,background-color,border-color,box-shadow] duration-150 ease-theme",
        "hover:border-primary/70",
        "focus-visible:ring-2 focus-visible:ring-ring/40",
        "data-[state=checked]:border-primary data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground",
        "data-[state=indeterminate]:border-primary data-[state=indeterminate]:bg-primary data-[state=indeterminate]:text-primary-foreground",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      <CheckboxPrimitive.Indicator className="flex items-center justify-center text-current data-[state=indeterminate]:[&_.checkbox-check]:hidden data-[state=indeterminate]:[&_.checkbox-minus]:block">
        <CheckIcon className="checkbox-check size-3 stroke-[3]" />
        <MinusIcon className="checkbox-minus hidden size-3 stroke-[3]" />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
}

function CheckboxDisplay({
  checked,
  className,
}: {
  checked: boolean;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      className={cn(
        "inline-flex size-[18px] shrink-0 items-center justify-center rounded-[5px] border-2 bg-card shadow-theme-xs",
        checked
          ? "border-primary bg-primary text-primary-foreground shadow-[0_1px_3px_color-mix(in_srgb,var(--color-primary)_35%,transparent)]"
          : "border-muted-foreground/45",
        className,
      )}
    >
      {checked ? <CheckIcon className="size-3 stroke-[3]" aria-hidden /> : null}
    </span>
  );
}

export { Checkbox, CheckboxDisplay };
