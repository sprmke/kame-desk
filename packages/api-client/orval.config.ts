import { defineConfig } from "orval";

export default defineConfig({
  doctordesk: {
    input: "../../apps/api/openapi.json",
    output: {
      target: "./src/generated.ts",
      client: "react-query",
      mode: "tags-split",
      override: {
        mutator: { path: "./src/custom-fetch.ts", name: "customFetch" },
      },
    },
  },
});
