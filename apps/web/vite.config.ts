import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import tailwindcss from "@tailwindcss/vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  server: { port: 3100, strictPort: true },
  plugins: [tsconfigPaths(), tanstackStart(), react(), tailwindcss()],
});
