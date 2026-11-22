import { useEffect, useState } from "react";

/**
 * Keeps a full-page skeleton off screen for the first `delayMs` of a load.
 * Fast (cached) queries then paint real content with no skeleton flash, while
 * slow loads still get a skeleton once the delay elapses.
 *
 * Use only where the skeleton replaces the page body. Inline section
 * skeletons should render immediately so they never leave a blank card.
 */
export function useDelayedLoading(active: boolean, delayMs = 180): boolean {
  const [visible, setVisible] = useState(active && delayMs <= 0);

  useEffect(() => {
    if (!active) {
      setVisible(false);
      return;
    }
    if (delayMs <= 0) {
      setVisible(true);
      return;
    }
    const timer = window.setTimeout(() => setVisible(true), delayMs);
    return () => window.clearTimeout(timer);
  }, [active, delayMs]);

  return visible;
}
