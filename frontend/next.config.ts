import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // E2E 測試用獨立的輸出資料夾（NEXT_DIST_DIR=.next-e2e），不會覆蓋開發用的 .next
  distDir: process.env.NEXT_DIST_DIR || ".next",
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
