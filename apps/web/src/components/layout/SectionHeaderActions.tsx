import { createPortal } from "react-dom";
import { useSectionActionsSlot } from "@/components/layout/SectionHubContext";

/**
 * Renders a tab page's primary actions into the fixed section header, so the
 * page keeps ownership of the handlers without adding a second header row.
 */
export function SectionHeaderActions({
  children,
}: {
  children: React.ReactNode;
}) {
  const slot = useSectionActionsSlot();
  if (!slot) return null;
  return createPortal(children, slot);
}
