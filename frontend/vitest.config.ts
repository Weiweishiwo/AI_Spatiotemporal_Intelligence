import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { createRequire } from "node:module";
import path from "node:path";

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
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/__tests__/setup.ts"],
    env: {
      NODE_ENV: "test",
    },
    exclude: ["**/node_modules/**", "**/*.browser.test.*"],
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
