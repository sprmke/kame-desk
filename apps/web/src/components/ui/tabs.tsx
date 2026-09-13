import * as React from "react";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { SlidingActivePill } from "@/components/ui/sliding-active-pill";
import { useDomActiveSlidingPill } from "@/hooks/useSlidingActivePill";
import { cn } from "@/lib/utils";

function Tabs({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Root>) {
  return (
    <TabsPrimitive.Root
      data-slot="tabs"
      className={cn("flex flex-col gap-4", className)}
      {...props}
    />
  );
}

function TabsList({
  className,
  children,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List>) {
  const { containerRef, bounds } = useDomActiveSlidingPill(
    "[data-state='active']",
  );

  const mergedRef = React.useCallback(
    (node: HTMLDivElement | null) => {
      containerRef.current = node;
    },
    [containerRef],
  );

  return (
    <TabsPrimitive.List
      ref={mergedRef}
      data-slot="tabs-list"
      className={cn(
        "relative inline-flex h-9 w-fit items-center rounded-lg bg-secondary p-0.5 text-muted-foreground",
        className,
      )}
      {...props}
    >
      {bounds ? <SlidingActivePill bounds={bounds} /> : null}
      {children}
    </TabsPrimitive.List>
  );
}

function TabsTrigger({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        "relative z-[1] inline-flex cursor-pointer touch-manipulation items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium whitespace-nowrap transition-colors duration-150 ease-theme",
        "text-muted-foreground hover:text-foreground data-[state=active]:text-foreground",
        "focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:outline-none",
        "disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4",
        className,
      )}
      {...props}
    />
  );
}

function TabsContent({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      data-slot="tabs-content"
      className={cn("outline-none", className)}
      {...props}
    />
  );
}

export { Tabs, TabsList, TabsTrigger, TabsContent };
