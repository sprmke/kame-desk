import { useMemo, useState } from "react";
import { Braces, Check, Copy, Search } from "lucide-react";
import { toast } from "sonner";
import {
  DOCUMENT_PLACEHOLDER_GROUPS,
  enrichDocumentPlaceholders,
  filterDocumentPlaceholders,
  groupDocumentPlaceholders,
  type PlaceholderGroup,
} from "@/lib/documentTemplatePlaceholders";
import { Button } from "@/components/ui/button";
import {
  ResponsiveModal,
  ResponsiveModalContent,
  ResponsiveModalHeader,
  ResponsiveModalTitle,
} from "@/components/ui/responsive-modal";
import { richTextChromeIconButtonClassName } from "@/components/ui/rich-text-editor";
import { cn } from "@/lib/utils";

type InsertProps = {
  onInsert: (token: string) => void;
  groups?: readonly PlaceholderGroup[];
};

function PlaceholdersReference({
  onInsert,
  groups = DOCUMENT_PLACEHOLDER_GROUPS,
  className,
}: InsertProps & { className?: string }) {
  const [query, setQuery] = useState("");
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const enriched = useMemo(() => enrichDocumentPlaceholders(groups), [groups]);
  const filtered = useMemo(
    () => filterDocumentPlaceholders(enriched, query),
    [enriched, query],
  );
  const grouped = useMemo(
    () => groupDocumentPlaceholders(filtered),
    [filtered],
  );

  async function writeClipboard(token: string): Promise<boolean> {
    try {
      await navigator.clipboard.writeText(token);
      return true;
    } catch {
      toast.error("Could not copy");
      return false;
    }
  }

  async function copyOnly(token: string) {
    if (!(await writeClipboard(token))) return;
    setCopiedToken(token);
    toast.success("Copied");
    window.setTimeout(() => {
      setCopiedToken((current) => (current === token ? null : current));
    }, 1600);
  }

  async function insertToken(token: string) {
    if (!(await writeClipboard(token))) return;
    onInsert(token);
    toast.success("Placeholder added");
  }

  return (
    <div className={cn("space-y-2.5", className)}>
      <p className="text-[10px] leading-snug text-muted-foreground sm:text-[11px]">
        Tap to insert. Filled from patient data on issue.
      </p>

      <div className="relative">
        <Search
          className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search tokens"
          aria-label="Search placeholders"
          className={cn(
            "h-9 w-full rounded-lg border border-border/70 bg-card py-1.5 pl-8 pr-2.5 text-xs text-foreground shadow-[inset_0_1px_2px_hsl(240_6%_10%_/0.04)]",
            "placeholder:text-muted-foreground/70 field-focus transition-colors",
            "dark:border-border/50 dark:bg-muted/30 dark:shadow-none",
          )}
        />
      </div>

      {grouped.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border/70 bg-muted/20 px-2.5 py-3 text-center text-[10px] text-muted-foreground sm:text-[11px]">
          {query.trim() ? "No matches" : "No placeholders"}
        </p>
      ) : (
        <div className="space-y-3 sm:space-y-4">
          {grouped.map(({ group, items }) => (
            <section
              key={group}
              aria-label={group}
              className="rounded-lg border border-border bg-card p-3 sm:p-4"
            >
              <h3 className="mb-2 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                {group}
              </h3>
              <ul className="grid grid-cols-1 gap-x-4 gap-y-1 sm:grid-cols-2">
                {items.map((item) => {
                  const copied = copiedToken === item.token;
                  return (
                    <li key={item.token}>
                      <div
                        className={cn(
                          "flex w-full items-start gap-1 rounded-lg transition-colors",
                          "hover:bg-muted/40",
                        )}
                      >
                        <button
                          type="button"
                          onClick={() => void insertToken(item.token)}
                          className={cn(
                            "min-w-0 flex-1 px-2 py-2 text-left",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30",
                          )}
                        >
                          <code className="block break-all font-mono text-[10px] font-semibold text-primary sm:text-[11px]">
                            {item.token}
                          </code>
                          <span className="mt-0.5 block text-[10px] leading-snug text-muted-foreground sm:text-[11px]">
                            {item.description}
                          </span>
                          {item.example ? (
                            <span className="mt-0.5 block truncate text-[10px] leading-snug text-muted-foreground/75 sm:text-[11px]">
                              e.g. {item.example}
                            </span>
                          ) : null}
                        </button>
                        <button
                          type="button"
                          aria-label={`Copy ${item.token}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            void copyOnly(item.token);
                          }}
                          className={cn(
                            "flex min-h-[44px] min-w-[44px] shrink-0 items-center justify-center rounded-lg px-2 text-muted-foreground",
                            "hover:bg-muted/60 hover:text-foreground",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30",
                          )}
                        >
                          {copied ? (
                            <Check
                              className="size-3.5 text-primary"
                              aria-hidden
                            />
                          ) : (
                            <Copy className="size-3.5" aria-hidden />
                          )}
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

export function TemplatePlaceholdersDialog({
  open,
  onOpenChange,
  onInsert,
  groups = DOCUMENT_PLACEHOLDER_GROUPS,
}: InsertProps & {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const handleInsert = (token: string) => {
    onInsert(token);
    onOpenChange(false);
  };

  return (
    <ResponsiveModal open={open} onOpenChange={onOpenChange}>
      <ResponsiveModalContent className="flex max-h-[min(92dvh,640px)] flex-col gap-0 overflow-hidden p-0 sm:max-w-[min(95vw,48rem)] sm:p-0">
        <ResponsiveModalHeader className="shrink-0 border-b border-border/60 px-4 py-3 sm:px-5 sm:py-4">
          <ResponsiveModalTitle className="text-base sm:text-lg">
            Placeholders
          </ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4 sm:px-5">
          <PlaceholdersReference onInsert={handleInsert} groups={groups} />
        </div>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}

const editorChromeActionClassName = cn(
  richTextChromeIconButtonClassName,
  "border border-input bg-card hover:bg-accent sm:h-8 sm:w-auto sm:gap-1.5 sm:px-2.5",
);

export function PlaceholdersButton({ onClick }: { onClick: () => void }) {
  return (
    <Button
      type="button"
      variant="outline"
      size="icon-sm"
      className={editorChromeActionClassName}
      onClick={onClick}
      aria-label="Placeholders"
      title="Placeholders"
    >
      <Braces className="size-3.5 shrink-0" aria-hidden />
      <span className="hidden text-xs font-semibold sm:inline">
        Placeholders
      </span>
    </Button>
  );
}
