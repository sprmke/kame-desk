import { HelpCircle } from "lucide-react";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export function RequiredMark() {
  return (
    <span className="text-destructive" aria-hidden>
      {" "}
      *
    </span>
  );
}

type FieldLabelProps = {
  htmlFor?: string;
  label: string;
  required?: boolean;
  help?: string;
  className?: string;
};

export function FieldLabel({
  htmlFor,
  label,
  required = false,
  help,
  className,
}: FieldLabelProps) {
  const helpText = help?.trim() ?? "";
  const labelEl = (
    <Label htmlFor={htmlFor} className={cn(helpText && "mb-0", className)}>
      {label}
      {required ? <RequiredMark /> : null}
    </Label>
  );

  if (!helpText) return labelEl;

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {labelEl}
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className="inline-flex size-6 shrink-0 cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors duration-150 ease-theme hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label={`About ${label}`}
          >
            <HelpCircle className="size-3.5" aria-hidden />
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs text-xs leading-relaxed">
          {helpText}
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
