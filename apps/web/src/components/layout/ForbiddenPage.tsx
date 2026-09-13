import { Link } from "@tanstack/react-router";
import { ShieldOff } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ForbiddenPage() {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 text-center">
      <ShieldOff className="size-10 text-muted-foreground" />
      <div>
        <h1 className="text-lg font-semibold text-foreground">Access denied</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your role cannot open this page.
        </p>
      </div>
      <Button asChild variant="outline">
        <Link to="/dashboard">Back to Today</Link>
      </Button>
    </div>
  );
}
