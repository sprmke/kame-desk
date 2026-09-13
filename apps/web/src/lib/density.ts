export const DENSITY = {
  compact: "dd-row-compact",
  default: "dd-row-default",
  comfortable: "dd-row-comfortable",
} as const;

export type Density = keyof typeof DENSITY;
