import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { playwright } from "@vitest/browser-playwright";
import { createRequire } from "node:module";
import path from "node:path";

if (process.env.NODE_ENV === "production" || !process.env.NODE_ENV) {
  process.env.NODE_ENV = "test";
}

const require = createRequire(import.meta.url);

const reactDir = path.dirname(
  require.resolve("react/package.json", {
    paths: [require.resolve("@testing-library/react")],
  })
);
const reactDomDir = path.dirname(
  require.resolve("react-dom/package.json", {
    paths: [require.resolve("@testing-library/react")],
  })
);

export default defineConfig({
  plugins: [react()],
  test: {
    env: {
      NODE_ENV: "test",
    },
    include: ["**/*.browser.test.*"],
    setupFiles: ["./src/__tests__/setup.browser.ts"],
    browser: {
      enabled: true,
      screenshotFailures: false,
      provider: playwright({
        launchOptions: {
          executablePath: "/usr/bin/chromium",
          args: ["--no-sandbox", "--disable-dev-shm-usage"],
        },
      }),
      headless: true,
      instances: [{ browser: "chromium" }],
    },
  },
  resolve: {
    dedupe: ["react", "react-dom"],
    alias: [
      { find: /^react$/, replacement: path.join(reactDir, "index.js") },
      { find: /^react\/(.*)$/, replacement: path.join(reactDir, "$1") },
      { find: /^react-dom$/, replacement: path.join(reactDomDir, "index.js") },
      { find: /^react-dom\/(.*)$/, replacement: path.join(reactDomDir, "$1") },
      { find: "@", replacement: path.resolve(import.meta.dirname, "./src") },
    ],
  },
});
