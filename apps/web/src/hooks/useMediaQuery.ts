import { useCallback, useSyncExternalStore } from "react";

/**
 * Subscribes to `window.matchMedia`. `defaultMatch` is the SSR / hydration
 * snapshot so server HTML matches the first client pass. `useIsBelowLg`
 * defaults to true so clinic tablets do not flash a centered dialog.
 */
export function useMediaQuery(query: string, defaultMatch = false): boolean {
  const subscribe = useCallback(
    (onStoreChange: () => void) => {
      const mql = window.matchMedia(query);
      mql.addEventListener("change", onStoreChange);
      return () => mql.removeEventListener("change", onStoreChange);
    },
    [query],
  );
  const getSnapshot = useCallback(
    () => window.matchMedia(query).matches,
    [query],
  );
  const getServerSnapshot = useCallback(() => defaultMatch, [defaultMatch]);

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

/** Tailwind `sm` — below 640px. */
export function useIsMobile(): boolean {
  return useMediaQuery("(max-width: 639px)", true);
}

/** Tailwind `md` — below 768px. */
export function useIsBelowMd(): boolean {
  return useMediaQuery("(max-width: 767px)", true);
}

/** Tailwind `lg` — phone/tablet shell below 1024px. */
export function useIsBelowLg(): boolean {
  return useMediaQuery("(max-width: 1023px)", true);
}

export function usePrefersReducedMotion(): boolean {
  return useMediaQuery("(prefers-reduced-motion: reduce)", false);
}
