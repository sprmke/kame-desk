import * as React from "react";
import * as RadioGroupPrimitive from "@radix-ui/react-radio-group";
import { cn } from "@/lib/utils";

const radioItemClassName = cn(
  "aspect-square size-[18px] shrink-0 cursor-pointer touch-manipulation rounded-full border-2 border-muted-foreground/45 bg-card shadow-theme-xs",
  "transition-[color,background-color,border-color,box-shadow] duration-150 ease-theme",
  "hover:border-primary/70",
  "focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:outline-none",
  "data-[state=checked]:border-primary data-[state=checked]:bg-primary",
  "disabled:cursor-not-allowed disabled:opacity-50",
);

function RadioGroup({
  className,
  ...props
}: React.ComponentProps<typeof RadioGroupPrimitive.Root>) {
  return (
    <RadioGroupPrimitive.Root
      data-slot="radio-group"
      className={cn("grid gap-2", className)}
      {...props}
    />
  );
}

function RadioGroupItem({
  className,
  ...props
}: React.ComponentProps<typeof RadioGroupPrimitive.Item>) {
  return (
    <RadioGroupPrimitive.Item
      data-slot="radio-group-item"
      className={cn(radioItemClassName, className)}
      {...props}
    >
      <RadioGroupPrimitive.Indicator className="flex items-center justify-center">
        <span className="size-2 rounded-full bg-primary-foreground" />
      </RadioGroupPrimitive.Indicator>
    </RadioGroupPrimitive.Item>
  );
}

function RadioGroupDisplay({
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
        radioItemClassName,
        "pointer-events-none flex items-center justify-center",
        checked && "border-primary bg-primary",
        className,
      )}
    >
      {checked ? (
        <span className="size-2 rounded-full bg-primary-foreground" />
      ) : null}
    </span>
  );
}

export { RadioGroup, RadioGroupItem, RadioGroupDisplay };
