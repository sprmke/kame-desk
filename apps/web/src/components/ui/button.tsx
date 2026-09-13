import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex cursor-pointer touch-manipulation items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-[color,background-color,border-color,box-shadow,transform] duration-150 ease-theme disabled:cursor-not-allowed disabled:pointer-events-none disabled:opacity-50 outline-none focus-visible:ring-2 focus-visible:ring-ring/40 active:scale-[0.98] [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-theme-xs hover:bg-brand-700 hover:shadow-theme-md hover:brightness-[1.02]",
        destructive:
          "bg-destructive text-destructive-foreground shadow-theme-xs hover:opacity-90 hover:shadow-theme-md hover:brightness-[1.02]",
        outline:
          "border border-input bg-card text-foreground shadow-theme-xs hover:border-primary/30 hover:bg-secondary",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-secondary text-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        soft: "bg-primary/10 text-primary hover:bg-primary/15",
      },
      size: {
        default: "h-11 min-h-11 px-4 lg:h-10 lg:min-h-10 [&_svg]:size-4",
        sm: "h-11 min-h-11 rounded-md px-3 text-sm lg:h-9 lg:min-h-9 [&_svg]:size-4",
        lg: "h-11 min-h-11 rounded-lg px-5 text-sm [&_svg]:size-4",
        icon: "size-11 [&_svg]:size-4",
        "icon-sm": "size-11 lg:size-9 [&_svg]:size-4",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  loading = false,
  children,
  disabled,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
    loading?: boolean;
  }) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={disabled || loading}
      {...props}
    >
      {asChild ? (
        children
      ) : (
        <>
          {loading ? (
            <Loader2 className="size-4 animate-spin" aria-hidden />
          ) : null}
          {children}
        </>
      )}
    </Comp>
  );
}

export { Button, buttonVariants };
