import { cn } from "@/lib/utils";

/**
 * Single source of truth for dashboard page width. Every page renders inside
 * one of these so the page header, sub-nav, and content share a left edge.
 *
 * `default` — lists, boards, hubs, settings, and detail pages. Content inside
 * this container is full width. Do not add a second `max-w-*` on the page.
 * `narrow` — standalone create/edit forms only (SOAP, new invoice, new patient).
 *
 * Pages nested in a section hub or the settings layout must not add a container
 * of their own; the shell already provides one.
 */
const WIDTH_CLASS = {
  default: "max-w-6xl",
  narrow: "max-w-2xl",
} as const;

export type PageWidth = keyof typeof WIDTH_CLASS;

/** For pages whose root element already exists. Prefer `PageContainer`. */
export function pageContainerClass(
  width: PageWidth = "default",
  className?: string,
) {
  return cn("mx-auto w-full", WIDTH_CLASS[width], className);
}

type Props = {
  children: React.ReactNode;
  width?: PageWidth;
  className?: string;
};

export function PageContainer({
  children,
  width = "default",
  className,
}: Props) {
  return <div className={pageContainerClass(width, className)}>{children}</div>;
}
