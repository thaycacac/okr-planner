# OKR Planner (intent-task-ai)

Web app nhập OKR theo quý → AI hỏi lại khi mơ hồ → phân rã từng KR thành task → scheduler deterministic xếp lịch theo ngày làm việc, capacity, phụ thuộc, buffer 10% → cảnh báo khả thi và đề xuất phương án.

- Kiến trúc và quyết định: [`docs/adr/`](docs/adr/README.md)
- Backend: [`backend/`](backend) — Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic
- Frontend: [`frontend/`](frontend/README.md) — Next.js 16, TypeScript, Tailwind, next-intl

## Chạy local

```bash
cp .env.example backend/.env

# backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload     # http://localhost:8000/docs

# frontend
cd ../frontend
npm ci && npm run dev                        # http://localhost:3000
```

Toàn bộ stack bằng Docker (Postgres + backend + frontend):

```bash
docker compose up --build
docker compose --profile local-llm up --build   # thêm Ollama trong container
```

Trên macOS nên cài Ollama trực tiếp để dùng GPU Apple Silicon; backend trong container gọi `host.docker.internal:11434`.

## Đăng nhập

Toàn bộ API (trừ `/health`, `/ready`, `/auth/login`, `/auth/logout`) cần session cookie lấy từ `POST /auth/login` bằng một mật khẩu chung. Sinh hash rồi đặt vào `APP_PASSWORD_HASH` (giữ nháy đơn trong `.env`):

```bash
cd backend && .venv/bin/python -m app.hash_password
```

`APP_ENV=prod` bắt buộc có `APP_PASSWORD_HASH` và `SESSION_SECRET` ngẫu nhiên từ 32 ký tự trở lên, thiếu thì app không khởi động. Rate-limit đăng nhập tính theo IP client; sau proxy Next.js phải khai báo `TRUSTED_PROXY_IPS` (xem `.env.example`).

Bảo mật HTTP:

- Sai mật khẩu quá `LOGIN_MAX_ATTEMPTS` lần thì IP bị khóa `LOGIN_LOCK_SECONDS`. Mỗi lần khóa tiếp theo dài gấp đôi, tối đa `LOGIN_LOCK_MAX_SECONDS`. Đăng nhập đúng hoặc im lặng 15 phút sau lần khóa thì đếm lại từ đầu.
- Session hết hạn tuyệt đối sau `SESSION_MAX_AGE_HOURS`. Giảm giá trị này cũng rút ngắn các session đã cấp. Đổi `SESSION_SECRET` sẽ đăng xuất mọi người.
- Request ghi dữ liệu (`POST`/`PUT`/`PATCH`/`DELETE`) mà trình duyệt gửi từ origin khác bị trả `403 cross_site_request`. Backend dựa vào header `Sec-Fetch-Site`, nếu không có thì so `Origin` với `Host`/`X-Forwarded-Host`. Origin trong `CORS_ORIGINS` được phép gọi chéo.
- Mọi response có `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control: no-store` và CSP chặt cho JSON. Ở prod có thêm HSTS, còn `/docs` và `/openapi.json` bị tắt.

## LLM

Hai provider, chọn trong Cài đặt hoặc qua `LLM_PROVIDER` (`auto` | `local` | `openai`). Local mặc định dùng Ollama, tương thích LM Studio / vLLM qua endpoint OpenAI-compatible. Chi tiết: [ADR 0002](docs/adr/0002-llm-provider-local-va-openai.md). Model local ứng viên: [ADR 0004](docs/adr/0004-model-local-ung-vien-eval.md).

```bash
ollama pull qwen3:8b
```

## Kiểm tra trước khi gửi review

```bash
cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy && .venv/bin/pytest -q
cd frontend && npm run lint && npm run typecheck && npm run test && npm run build
```

CI (`.github/workflows/ci.yml`) chạy đúng các lệnh trên. Job `backend-postgres` chạy lại `pytest` trên Postgres 16. Chạy tương tự ở máy local như sau (mỗi test xóa schema `public`, nên tên database phải chứa `test`):

```bash
docker run -d --rm --name okr-test-pg -e POSTGRES_USER=okr -e POSTGRES_PASSWORD=okr \
  -e POSTGRES_DB=okr_planner_test -p 127.0.0.1:55433:5432 postgres:16-alpine
cd backend && TEST_DATABASE_URL=postgresql+psycopg://okr:okr@127.0.0.1:55433/okr_planner_test .venv/bin/pytest -q
docker rm -f okr-test-pg
```
