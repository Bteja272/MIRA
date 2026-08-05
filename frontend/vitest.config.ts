import react from "@vitejs/plugin-react";
import {
  defineConfig,
} from "vitest/config";

export default defineConfig({
  plugins: [
    react(),
  ],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [
      "./src/test/setup.ts",
    ],
    css: true,
    clearMocks: true,
    restoreMocks: true,
    coverage: {
      provider: "v8",
      reporter: [
        "text",
        "html",
      ],
      reportsDirectory:
        "./coverage",
      include: [
        "src/**/*.{ts,tsx}",
      ],
      exclude: [
        "src/main.tsx",
        "src/router.tsx",
        "src/test/**",
        "src/**/*.d.ts",
      ],
    },
  },
});