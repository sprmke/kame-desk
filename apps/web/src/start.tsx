// @ts-nocheck — TanStack Start factory types lag router generics; vite build validates this file.
import { createStart } from "@tanstack/react-start";
import { getRouter } from "./router";

export const startInstance = createStart(() => ({
  getRouter,
}));
