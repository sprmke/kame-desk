import * as React from "react";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useIsBelowLg } from "@/hooks/useMediaQuery";
import { cn } from "@/lib/utils";

type ResponsiveModalProps = {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
};

/**
 * Bottom sheet below `lg`; centered dialog at `lg+`.
 * Use for operational actions (walk-in, reschedule, cancel, payment).
 * Keep AlertDialog for OS-style destructive confirms.
 */
export function ResponsiveModal({
  open,
  onOpenChange,
  children,
}: ResponsiveModalProps) {
  const useSheet = useIsBelowLg();

  if (useSheet) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        {children}
      </Sheet>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {children}
    </Dialog>
  );
}

type ResponsiveModalContentProps = React.ComponentPropsWithoutRef<
  typeof DialogContent
> & {
  sheetBodyClassName?: string;
};

export function ResponsiveModalContent({
  className,
  children,
  sheetBodyClassName,
  showCloseButton,
  ...props
}: ResponsiveModalContentProps) {
  const useSheet = useIsBelowLg();

  if (useSheet) {
    return (
      <SheetContent
        side="bottom"
        showCloseButton={showCloseButton ?? false}
        className={cn("gap-0 px-4 pt-1 pb-4", className)}
        {...props}
      >
        <div className={cn("flex min-h-0 flex-col gap-4", sheetBodyClassName)}>
          {children}
        </div>
      </SheetContent>
    );
  }

  return (
    <DialogContent
      className={className}
      showCloseButton={showCloseButton}
      {...props}
    >
      {children}
    </DialogContent>
  );
}

export function ResponsiveModalHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  const useSheet = useIsBelowLg();
  if (useSheet) {
    return (
      <SheetHeader
        className={cn("space-y-1 px-0 pb-0 pt-0", className)}
        {...props}
      />
    );
  }
  return <DialogHeader className={className} {...props} />;
}

export function ResponsiveModalFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  const useSheet = useIsBelowLg();
  if (useSheet) {
    return (
      <SheetFooter
        className={cn(
          "mt-0 flex-col-reverse gap-2 p-0 sm:flex-row sm:justify-end",
          className,
        )}
        {...props}
      />
    );
  }
  return <DialogFooter className={className} {...props} />;
}

export function ResponsiveModalTitle({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogTitle>) {
  const useSheet = useIsBelowLg();
  if (useSheet) {
    return (
      <SheetTitle
        className={cn(
          "text-base font-semibold tracking-tight sm:text-lg",
          className,
        )}
        {...props}
      />
    );
  }
  return <DialogTitle className={className} {...props} />;
}

export function ResponsiveModalDescription({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogDescription>) {
  const useSheet = useIsBelowLg();
  if (useSheet) {
    return <SheetDescription className={className} {...props} />;
  }
  return <DialogDescription className={className} {...props} />;
}

export function ResponsiveModalClose(
  props: React.ComponentPropsWithoutRef<typeof DialogClose>,
) {
  const useSheet = useIsBelowLg();
  if (useSheet) return <SheetClose {...props} />;
  return <DialogClose {...props} />;
}

export function ResponsiveModalTrigger(
  props: React.ComponentPropsWithoutRef<typeof DialogTrigger>,
) {
  const useSheet = useIsBelowLg();
  if (useSheet) return <SheetTrigger {...props} />;
  return <DialogTrigger {...props} />;
}
