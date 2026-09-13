import { cn } from "@/lib/utils";

/** Interim geometric monogram. A distinctive mark remains a human decision. */
export function ProductMark({
  className,
  title = "DoctorDesk",
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
        d="M6 4.5h7.2c3.4 0 5.8 2.2 5.8 5.5S16.6 15.5 13.2 15.5H9.5V19.5H6V4.5Zm3.5 7.4h3.4c1.5 0 2.4-1 2.4-2.4s-.9-2.4-2.4-2.4H9.5v4.8Z"
      />
    </svg>
  );
}
