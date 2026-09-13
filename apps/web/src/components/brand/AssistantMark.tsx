import { cn } from "@/lib/utils";

/** Interim geometric assistant mark. Not a robot or sparkles glyph. */
export function AssistantMark({
  className,
  title = "Clinic assistant",
}: {
  className?: string;
  title?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={cn("size-5", className)}
      aria-hidden={title ? undefined : true}
      role={title ? "img" : undefined}
    >
      {title ? <title>{title}</title> : null}
      <path
        fill="currentColor"
        d="M5 5.5h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-6.2L8 21v-3.5H5a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2Zm2.8 4.2v1.6h8.4V9.7H7.8Zm0 3.4v1.6h5.6v-1.6H7.8Z"
      />
    </svg>
  );
}
