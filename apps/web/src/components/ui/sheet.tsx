import * as React from "react";
import * as SheetPrimitive from "@radix-ui/react-dialog";
import { XIcon } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { useVisualViewportBottomInset } from "@/hooks/useVisualViewportInset";

function Sheet(props: React.ComponentProps<typeof SheetPrimitive.Root>) {
  return <SheetPrimitive.Root data-slot="sheet" {...props} />;
}

function SheetTrigger(
  props: React.ComponentProps<typeof SheetPrimitive.Trigger>,
) {
  return <SheetPrimitive.Trigger data-slot="sheet-trigger" {...props} />;
}

function SheetClose(props: React.ComponentProps<typeof SheetPrimitive.Close>) {
  return <SheetPrimitive.Close data-slot="sheet-close" {...props} />;
}

function SheetPortal(
  props: React.ComponentProps<typeof SheetPrimitive.Portal>,
) {
  return <SheetPrimitive.Portal data-slot="sheet-portal" {...props} />;
}

function SheetOverlay({
  className,
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Overlay>) {
  return (
    <SheetPrimitive.Overlay
      data-slot="sheet-overlay"
      className={cn(
        "fixed inset-0 z-50 bg-black/40 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=open]:duration-[220ms] data-[state=closed]:duration-[220ms] motion-reduce:animate-none",
        className,
      )}
      {...props}
    />
  );
}

const sheetVariants = cva(
  "fixed z-50 flex flex-col gap-4 bg-card shadow-theme-lg transition ease-out-quart motion-reduce:transition-none data-[state=closed]:duration-[220ms] data-[state=open]:duration-[220ms]",
  {
    variants: {
      side: {
        top: "inset-x-0 top-0 border-b pt-[max(1rem,env(safe-area-inset-top))] data-[state=closed]:animate-out data-[state=closed]:slide-out-to-top data-[state=open]:animate-in data-[state=open]:slide-in-from-top",
        bottom:
          "inset-x-0 bottom-0 max-h-[92dvh] rounded-t-2xl border-t pb-[max(1rem,env(safe-area-inset-bottom))] data-[state=closed]:animate-out data-[state=closed]:slide-out-to-bottom data-[state=open]:animate-in data-[state=open]:slide-in-from-bottom",
        left: "inset-y-0 left-0 h-full w-3/4 border-r data-[state=closed]:animate-out data-[state=closed]:slide-out-to-left data-[state=open]:animate-in data-[state=open]:slide-in-from-left sm:max-w-xs",
        right:
          "inset-y-0 right-0 h-full w-3/4 border-l data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right data-[state=open]:animate-in data-[state=open]:slide-in-from-right sm:max-w-xs",
      },
    },
    defaultVariants: { side: "right" },
  },
);

type SheetContentProps = React.ComponentProps<typeof SheetPrimitive.Content> &
  VariantProps<typeof sheetVariants> & {
    showCloseButton?: boolean;
    hideClose?: boolean;
    showHandle?: boolean;
    overlayClassName?: string;
  };

function SheetContent({
  className,
  children,
  side = "right",
  showCloseButton = true,
  hideClose = false,
  showHandle = false,
  overlayClassName,
  ...props
}: SheetContentProps) {
  const keyboardInset = useVisualViewportBottomInset();
  const showSheetHandle = showHandle || side === "bottom";
  const showClose = !hideClose && showCloseButton && side !== "bottom";

  return (
    <SheetPortal>
      <SheetOverlay className={overlayClassName} />
      <SheetPrimitive.Content
        data-slot="sheet-content"
        className={cn(sheetVariants({ side }), className)}
        style={
          side === "bottom"
            ? {
                paddingBottom: `max(1rem, calc(env(safe-area-inset-bottom) + ${keyboardInset}px))`,
              }
            : undefined
        }
        {...props}
      >
        {showSheetHandle ? (
          <div className="flex shrink-0 justify-center pb-1 pt-3" aria-hidden>
            <div className="h-1 w-10 rounded-full bg-muted-foreground/35" />
          </div>
        ) : null}
        {children}
        {showClose ? (
          <SheetPrimitive.Close className="absolute top-3 right-3 flex size-11 cursor-pointer items-center justify-center rounded-md text-muted-foreground opacity-70 transition-opacity hover:opacity-100 focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:outline-none disabled:pointer-events-none">
            <XIcon className="size-4" />
            <span className="sr-only">Close</span>
          </SheetPrimitive.Close>
        ) : null}
      </SheetPrimitive.Content>
    </SheetPortal>
  );
}

function SheetHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sheet-header"
      className={cn("flex flex-col gap-1.5 p-4", className)}
      {...props}
    />
  );
}

function SheetFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sheet-footer"
      className={cn("mt-auto flex flex-col gap-2 p-4", className)}
      {...props}
    />
  );
}

function SheetTitle({
  className,
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Title>) {
  return (
    <SheetPrimitive.Title
      data-slot="sheet-title"
      className={cn("text-base font-semibold text-foreground", className)}
      {...props}
    />
  );
}

function SheetDescription({
  className,
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Description>) {
  return (
    <SheetPrimitive.Description
      data-slot="sheet-description"
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}

export {
  Sheet,
  SheetTrigger,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
};
