import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const cardVariants = cva("text-card-foreground", {
  variants: {
    surface: {
      plain: "bg-transparent",
      panel: "rounded-lg border border-border bg-card",
      raised: "rounded-lg border border-border bg-card shadow-theme-sm",
      overlay: "rounded-lg border border-border bg-card shadow-theme-md",
    },
    interactive: {
      true: "cursor-pointer touch-manipulation transition-[box-shadow,transform,border-color] duration-150 ease-theme hover:border-primary/20 motion-safe:active:scale-[0.99]",
      false: "",
    },
  },
  defaultVariants: {
    surface: "raised",
    interactive: false,
  },
});

function Card({
  className,
  interactive,
  surface,
  ...props
}: React.ComponentProps<"div"> & VariantProps<typeof cardVariants>) {
  return (
    <div
      data-slot="card"
      data-surface={surface ?? "raised"}
      data-interactive={interactive ? "true" : undefined}
      className={cn(cardVariants({ interactive, surface }), className)}
      {...props}
    />
  );
}

function CardHeader({
  className,
  divided = false,
  ...props
}: React.ComponentProps<"div"> & { divided?: boolean }) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "flex flex-col gap-1 px-5 py-4 sm:px-6",
        divided && "border-b border-border",
        className,
      )}
      {...props}
    />
  );
}

function CardTitle({ className, ...props }: React.ComponentProps<"h3">) {
  return (
    <h3
      data-slot="card-title"
      className={cn("text-base font-semibold leading-none", className)}
      {...props}
    />
  );
}

function CardDescription({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p
      data-slot="card-description"
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}

function CardAction({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-action"
      className={cn("ml-auto flex items-center gap-2", className)}
      {...props}
    />
  );
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-content"
      className={cn("px-5 py-4 sm:px-6", className)}
      {...props}
    />
  );
}

function CardFooter({
  className,
  divided = false,
  ...props
}: React.ComponentProps<"div"> & { divided?: boolean }) {
  return (
    <div
      data-slot="card-footer"
      className={cn(
        "flex items-center gap-2 px-5 py-4 sm:px-6",
        divided && "border-t border-border",
        className,
      )}
      {...props}
    />
  );
}

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardAction,
  CardContent,
  CardFooter,
  cardVariants,
};
