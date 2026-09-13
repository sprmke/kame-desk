/**
 * Clinical motion tokens. Calmer than hospitality springs: higher damping,
 * no overshoot. Pair every animated surface with `useReducedMotion()`.
 */

export const EASE_THEME = [0.4, 0, 0.2, 1] as const;
export const EASE_OUT_QUART = [0.22, 1, 0.36, 1] as const;

/** Micro: hover, press, focus, color/border. */
export const DURATION_MICRO_S = 0.15;
export const DURATION_MICRO_MS = 150;

/** Transition: sheets, dialogs, pills, list enter. */
export const DURATION_TRANSITION_S = 0.22;
export const DURATION_TRANSITION_MS = 220;

/** Page-level: dashboard sub-route stage push. */
export const DURATION_PAGE_S = 0.16;
export const DURATION_PAGE_MS = 160;

/** Sliding tab/dock pill. Damped enough that it does not bounce. */
export const SLIDING_PILL_SPRING = {
  type: "spring" as const,
  stiffness: 380,
  damping: 44,
  mass: 0.92,
};

export const PAGE_TRANSITION = {
  duration: DURATION_PAGE_S,
  ease: EASE_OUT_QUART,
};

export function listItemDelay(index: number, reducedMotion: boolean): number {
  if (reducedMotion) return 0;
  return Math.min(index, 12) * 0.028;
}
