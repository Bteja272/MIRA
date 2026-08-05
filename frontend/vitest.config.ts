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

    // WSL projects under /mnt/c can start forked jsdom workers
    // slowly. Run one thread at a time for stable local tests.
    pool: "threads",
    fileParallelism: false,
    maxWorkers: 1,
    minWorkers: 1,

    testTimeout: 15_000,
    hookTimeout: 15_000,

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