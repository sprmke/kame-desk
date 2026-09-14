import { Link } from "@tanstack/react-router";
import { FileQuestion } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function NotFoundShell({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 px-6 text-center",
        compact ? "min-h-[40vh]" : "min-h-svh",
      )}
    >
      <FileQuestion className="size-10 text-muted-foreground" aria-hidden />
      <h1 className="text-lg font-semibold text-foreground">Page not found</h1>
      <Button asChild variant="outline">
        <Link to="/">Back to Today</Link>
      </Button>
    </div>
  );
}

export function NotFoundPage() {
  return <NotFoundShell />;
}

export function CompactNotFoundPage() {
  return <NotFoundShell compact />;
}
