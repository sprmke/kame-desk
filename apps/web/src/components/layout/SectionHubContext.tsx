import { createContext, useContext } from "react";

/**
 * DOM node in the fixed section header where a tab's page injects its actions.
 * Null outside a `SectionHubShell`.
 */
const SectionActionsContext = createContext<HTMLElement | null>(null);

export const SectionActionsProvider = SectionActionsContext.Provider;

export function useSectionActionsSlot() {
  return useContext(SectionActionsContext);
}
