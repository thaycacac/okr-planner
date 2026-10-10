# ADR 0005 — Frontend và API cùng origin qua proxy `/api/*` của Next.js

- Trạng thái: Chấp nhận
- Ngày: 2026-09-30
- Bổ sung cho: ADR 0001 (mục Auth, Hạ tầng). Không đổi quyết định cookie `SameSite=Lax` của ADR 0001.

## Bối cảnh

ADR 0001 chọn session cookie httpOnly + Secure + `SameSite=Lax` và deploy backend, frontend thành hai service Railway. Mỗi service có domain riêng dạng `*.up.railway.app`. `up.railway.app` nằm trong Public Suffix List, nên hai subdomain đó là **hai site khác nhau**:

- Trình duyệt không gửi cookie `Lax` trong `fetch`/`EventSource` cross-site, nên đăng nhập xong sẽ không giữ được phiên.
- Đổi sang `SameSite=None; Secure` biến cookie phiên thành cookie bên thứ ba. Safari (ITP), Firefox (ETP) và cấu hình chặn cookie bên thứ ba của Chrome đều có thể chặn nó, nên lỗi phụ thuộc trình duyệt của người xem demo.
- SSE tiến trình (`GET /plans/{job_id}/events`) dùng `EventSource`. Cross-origin thì cần `withCredentials` và CORS có credentials, thêm một nguồn lỗi nữa.

## Quyết định

Trình duyệt chỉ nói chuyện với **một origin** là frontend. Next.js chuyển tiếp `/api/*` tới backend qua mạng nội bộ Railway.

```
Browser ──HTTPS──> frontend (Next.js)  /api/:path*  ──private network──> backend (FastAPI) /:path*
```

### Frontend

- `rewrites()` trong `next.config.ts`: `/api/:path*` → `${BACKEND_INTERNAL_URL}/:path*`.
- Client gọi base URL tương đối `/api` (`NEXT_PUBLIC_API_BASE_URL=/api` là mặc định). Dev dùng cùng cơ chế với `BACKEND_INTERNAL_URL=http://localhost:8000`, để lỗi proxy lộ ra ngay ở máy dev.
- Với `output: "standalone"`, đích của rewrite bị đóng băng lúc `next build`, nên `BACKEND_INTERNAL_URL` là **build arg** của Docker image frontend, không phải biến runtime. Trên Railway, dùng private domain của service backend (ví dụ `http://backend.railway.internal:8000`).
- Proxy của Next.js mặc định cắt request sau **30 giây**. Phải đặt `experimental.proxyTimeout` lớn hơn timeout LLM dài nhất cộng khoảng dư (hiện `local_llm_timeout_seconds=180`), tức ≥ 240 000 ms.
- SSE phải đi qua proxy mà không bị gom buffer: smoke test phải thấy từng event đến theo thời gian thực, không dồn một lần lúc cuối.
- Script `api:pull` cần URL tuyệt đối của backend (`BACKEND_INTERNAL_URL`), không dùng `/api`.

### Backend

- Cookie phiên **host-only** (không đặt `Domain`), `Path=/`, `HttpOnly`, `SameSite=Lax`, `Secure` khi chạy production. Cookie đi qua proxy và gắn vào host của frontend.
- Sau proxy, IP kết nối của mọi request là IP của service frontend. Rate-limit đăng nhập phải lấy IP client từ header proxy và **chỉ tin header này khi request đến từ proxy tin cậy**. Nếu không, một người nhập sai mật khẩu sẽ khóa mọi người, còn nếu tin header từ bất kỳ đâu thì kẻ tấn công vượt được rate-limit.
  - Cơ chế: app tự xử lý (`TRUSTED_PROXY_IPS` là danh sách IP/CIDR, `CLIENT_IP_HEADER`), còn uvicorn chạy `--no-proxy-headers` để chỉ một nơi đọc header. Với `x-forwarded-for`, lấy hop ngoài cùng bên phải không thuộc proxy tin cậy. Với header khác, đọc đúng một IP.
  - Railway: Next.js không nối thêm hop vào `X-Forwarded-For`, còn Railway chỉ cam kết ghi đè `X-Real-IP` ở edge. Vì vậy production dùng `CLIENT_IP_HEADER=x-real-ip` và `TRUSTED_PROXY_IPS=<dải private network của service frontend>`. Cấu hình này **chỉ an toàn khi backend không có public domain**. Nếu có, request đi thẳng từ Internet có thể mang theo `X-Real-IP` giả. Smoke khi deploy: hai client khác IP không khóa lẫn nhau, và `X-Real-IP` do client tự gửi không đổi được bucket.
  - Dev/`docker compose`: `TRUSTED_PROXY_IPS` rỗng nên mọi request qua frontend dùng chung một bucket. Chấp nhận được.
- Response SSE gửi `Cache-Control: no-cache` và `X-Accel-Buffering: no`, kèm event/comment heartbeat ≤ 15 giây để giữ kết nối qua các proxy.
- Production không cần CORS vì cùng origin. `CORS_ORIGINS` giữ cho trường hợp dev gọi thẳng backend.
- Service backend trên Railway **không cần public domain**. Tắt public domain giúp thu nhỏ bề mặt tấn công; `/health` và `/ready` vẫn là healthcheck nội bộ của Railway.

## Phương án đã cân nhắc

| Phương án | Lý do không chọn |
|---|---|
| `SameSite=None; Secure` + CORS credentials | Cookie bên thứ ba bị Safari/Firefox chặn mặc định, và ngày càng nhiều cấu hình Chrome cũng chặn. Demo có thể hỏng tùy trình duyệt của board |
| Custom domain chung (`app.example.com` + `api.example.com`) | Cần mua domain và cấu hình DNS (chi phí, việc của board), không cần thiết cho demo. Vẫn tương thích về sau: có thể thêm custom domain mà không phải bỏ proxy |
| Route Handler `app/api/[...path]/route.ts` tự viết proxy | Kiểm soát nhiều hơn (đọc env lúc runtime, timeout riêng) nhưng phải tự xử lý stream, header và `Set-Cookie`. `rewrites` là cơ chế có sẵn, đủ dùng. Nếu gặp vấn đề với SSE hoặc timeout thì chuyển sang cách này (two-way door) |
| Gộp frontend và backend vào một container/reverse proxy (Caddy/Nginx) | Thêm một thành phần phải vận hành, lệch khỏi mô hình hai service của ADR 0001 |

## Hệ quả

- Cookie là first-party nên không phụ thuộc chính sách cookie bên thứ ba của trình duyệt. Sau này server component có thể đọc cookie phiên để chặn trang chưa đăng nhập từ phía server (tùy chọn, chưa bắt buộc).
- Thêm một hop mạng nội bộ cho mỗi request API. Độ trễ không đáng kể so với thời gian gọi LLM.
- Đổi URL backend phải **build lại image frontend**, vì đích rewrite nằm trong build. Nhớ điểm này trong runbook deploy/rollback.
- Rollback: quyết định đảo ngược được. Đặt lại `NEXT_PUBLIC_API_BASE_URL` về URL tuyệt đối của backend, bỏ rewrite và bật lại CORS.
