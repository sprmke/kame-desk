import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex w-fit items-center gap-1 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors duration-150 ease-theme [&_svg]:size-3",
  {
    variants: {
      variant: {
        default: "border-transparent bg-secondary text-secondary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        brand:
          "border-transparent bg-brand-50 text-brand-700 dark:bg-accent dark:text-accent-foreground",
        success:
          "border-transparent bg-success-50 text-success-700 dark:bg-success/15 dark:text-success",
        warning:
          "border-transparent bg-warning-50 text-warning-700 dark:bg-warning/15 dark:text-warning",
        error:
          "border-transparent bg-error-50 text-error-700 dark:bg-destructive/15 dark:text-destructive",
        destructive:
          "border-transparent bg-error-50 text-error-700 dark:bg-destructive/15 dark:text-destructive",
        info: "border-transparent bg-info-50 text-info-700 dark:bg-info-500/15 dark:text-info-500",
        outline: "border-border text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

function Badge({
  className,
  variant,
  asChild = false,
  dot = false,
  children,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean; dot?: boolean }) {
  const Comp = asChild ? Slot : "span";
  return (
    <Comp
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    >
      {asChild ? (
        children
      ) : (
        <>
          {dot ? (
            <span className="size-1.5 shrink-0 rounded-full bg-current opacity-80" />
          ) : null}
          {children}
        </>
      )}
    </Comp>
  );
}

export { Badge, badgeVariants };
