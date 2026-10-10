import { writeFile } from "node:fs/promises";

// Needs the backend's absolute URL; the /api proxy only exists inside a running Next.js server.
const base = (process.env.BACKEND_INTERNAL_URL || "http://localhost:8000").replace(/\/$/, "");
const target = new URL("../openapi/openapi.json", import.meta.url);

const res = await fetch(`${base}/openapi.json`);
if (!res.ok) {
  console.error(`GET ${base}/openapi.json -> ${res.status}`);
  process.exit(1);
}
const spec = await res.json();
await writeFile(target, `${JSON.stringify(spec, null, 2)}\n`);
console.log(`Wrote ${target.pathname}`);
