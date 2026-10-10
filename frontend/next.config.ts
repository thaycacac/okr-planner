import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

import { pageSecurityHeaders } from "./src/lib/security-headers";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

// Read at `next build`: with `output: "standalone"` the rewrite destination is
// baked into the build, so changing the backend URL means rebuilding the image.
const backendUrl = (process.env.BACKEND_INTERNAL_URL || "http://localhost:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    // Next.js cuts proxied requests after 30s by default; LLM calls may take up
    // to LOCAL_LLM_TIMEOUT_SECONDS (180s) before the backend answers.
    proxyTimeout: 240_000,
  },
  // The per-request CSP (nonce) is set in src/proxy.ts.
  async headers() {
    return pageSecurityHeaders({ dev: process.env.NODE_ENV === "development" });
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendUrl}/:path*` }];
  },
};

export default withNextIntl(nextConfig);
