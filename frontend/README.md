# OKR Planner — frontend

Next.js (App Router) + TypeScript, Tailwind, next-intl (vi mặc định, en). Kiến trúc: `../docs/adr/0001-kien-truc-tong-the.md`.

```bash
npm ci
npm run dev        # http://localhost:3000
npm run lint
npm run typecheck
npm run test
npm run build
```

Trình duyệt chỉ gọi origin của frontend: Next.js chuyển tiếp `/api/*` tới backend (`rewrites()` trong `next.config.ts`), nên cookie phiên là first-party. Chi tiết: `../docs/adr/0005-cung-origin-qua-proxy-nextjs.md`.

Biến môi trường:

- `BACKEND_INTERNAL_URL` (mặc định `http://localhost:8000`): URL tuyệt đối của backend, đích của rewrite `/api/:path*` → `${BACKEND_INTERNAL_URL}/:path*`. Được đọc lúc `next build` (và `next dev`); với `output: "standalone"` giá trị bị đóng băng trong build, nên trong Docker đây là **build arg** và đổi URL backend phải build lại image. `docker compose` dùng `http://backend:8000`; trên Railway dùng private domain của service backend.
- `NEXT_PUBLIC_API_BASE_URL` (mặc định `/api`): base URL client gọi. Chỉ đặt URL tuyệt đối khi muốn gọi thẳng backend (khi đó backend cần `CORS_ORIGINS` chứa origin frontend, và cookie `SameSite=Lax` chỉ hoạt động nếu hai bên cùng site).
- Proxy đặt `experimental.proxyTimeout` = 240 s (mặc định của Next.js là 30 s) để không cắt request LLM dài.
- `NEXT_PUBLIC_API_MOCK=1`: dùng mock trong trình duyệt (`src/lib/api/mock.ts`) thay cho backend, mật khẩu mock `okr-demo`. Chỉ dùng khi backend chưa có route auth/settings.

UI dùng shadcn/ui (`components.json`, component trong `src/components/ui/`). Thêm component: `npx shadcn@latest add <tên>`.

## API client

Type sinh từ OpenAPI bằng `openapi-typescript`, gọi qua `openapi-fetch` (`src/lib/api/client.ts`): mọi request gửi cookie (`credentials: "include"`), 401 trên route dữ liệu chuyển về `/login?reason=expired`.

```bash
npm run api:pull   # tải $BACKEND_INTERNAL_URL/openapi.json vào openapi/openapi.json
npm run api:gen    # sinh src/lib/api/schema.d.ts
```

`openapi/openapi.json` hiện là bản nháp: `/health`, `/ready` lấy từ backend; `/auth/*`, `/settings/*` soạn theo ADR 0002 cho tới khi backend publish. Khi backend có route thật, chạy lại hai lệnh trên rồi `npm run typecheck`.

Next.js 16 có thay đổi phá vỡ so với các bản trước; đọc tài liệu trong `node_modules/next/dist/docs/` trước khi viết code (xem `AGENTS.md`).
