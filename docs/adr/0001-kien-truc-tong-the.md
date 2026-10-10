# ADR 0001 — Kiến trúc tổng thể OKR Planner

- Trạng thái: Chấp nhận
- Ngày: 2026-09-30
- Người quyết định: CTO (dựa trên plan rev 3 đã được board duyệt)

## Bối cảnh

OKR Planner là web app single-user: người dùng nhập OKR theo quý, AI hỏi lại khi OKR mơ hồ, phân rã từng KR thành task khoảng 4 giờ, sau đó hệ thống xếp lịch theo ngày làm việc, capacity, phụ thuộc và buffer 10%, cảnh báo khi không khả thi.

Yêu cầu có ảnh hưởng tới kiến trúc:

- Kết quả xếp lịch phải **ổn định và kiểm thử được** (cùng đầu vào, cùng cấu hình thì cùng kết quả).
- Hỗ trợ hai nhà cung cấp LLM (Local và OpenAI), người dùng chọn trong Cài đặt.
- Giao diện song ngữ vi/en, responsive, có lịch tuần/tháng và dashboard workload.
- Dữ liệu lưu phía server, bảo vệ bằng một mật khẩu chung.
- Team nhỏ (1 Backend, 1 Frontend, 1 QA, CTO), timeline khoảng 5 tuần.

## Quyết định

### Monorepo, hai ứng dụng

```
intent-task-ai/
├── backend/            FastAPI (Python 3.11)
├── frontend/           Next.js (TypeScript)
├── docs/adr/           Architecture Decision Records
├── docs/               chính sách dữ liệu, runbook, eval
├── docker-compose.yml  postgres + backend + frontend (+ profile local-llm: ollama)
└── .github/workflows/  CI: lint + test cho cả hai phía
```

Một repo giúp thay đổi API và UI đi cùng một diff, phù hợp team nhỏ (Conway's Law: ranh giới backend/frontend trùng với ranh giới người sở hữu).

### Backend: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic

Module trong `backend/app/`, phụ thuộc chỉ đi theo một chiều `api → (planner_llm, scheduler, exporters, persistence) → calendar → domain`:

| Module | Trách nhiệm | Được import |
|---|---|---|
| `domain/` | Entity và rule nghiệp vụ thuần (Quarter, Objective, KeyResult, Task, CalendarConfig). Không phụ thuộc framework, DB hay LLM | stdlib, pydantic |
| `calendar/` | Ngày làm việc: T7/CN, lễ VN (dữ liệu seed chỉnh được), nghỉ phép, ngày làm bù, capacity theo thứ | `domain` |
| `scheduler/` | Scheduler deterministic, feasibility, what-if (xem ADR 0003) | `domain`, `calendar` |
| `planner_llm/` | Clarify, decompose theo KR, dedup, validate; adapter provider (xem ADR 0002) | `domain` |
| `exporters/` | Port `Exporter` → CSV, XLSX; sau này Google Calendar/Jira/Trello | `domain` |
| `persistence/` | SQLAlchemy models, repository, Alembic migrations | `domain` |
| `api/` | FastAPI routers, auth, SSE tiến trình, wiring | tất cả |

Quy tắc: `scheduler/` và `calendar/` **không được** import `planner_llm/`, `persistence/` hay FastAPI. Nhờ vậy phần tính ngày/giờ test được bằng pytest + hypothesis thuần, không cần DB hay mạng.

### Database: PostgreSQL (prod), SQLite (dev/test)

- Dùng kiểu cột tương thích cả hai (không dùng tính năng riêng của Postgres ở phase 1–2).
- Migration bằng Alembic ngay từ đầu; không dùng `create_all` ở prod.
- Mỗi `PlanRun` lưu `provider`, `model`, thời gian chạy, số lần retry để truy vết.

### Frontend: Next.js (App Router) + TypeScript

- Tailwind + shadcn/ui cho component, next-intl cho vi/en, FullCalendar (tuần/tháng), Recharts (workload).
- Gọi backend qua REST; tiến trình sinh kế hoạch qua SSE (fallback polling).
- Kiểu dữ liệu API sinh từ OpenAPI của FastAPI để tránh lệch schema.

### Luồng sinh kế hoạch là job bất đồng bộ

`POST /plans` tạo job, trả `job_id`; UI theo dõi tiến trình qua SSE `GET /plans/{job_id}/events`. Các bước: pre-check deterministic → clarify → decompose theo từng KR (song song, có giới hạn concurrency) → dedup → validate → schedule → feasibility. Phase 1 chạy job trong process bằng `asyncio` (một user nên đủ); nếu cần scale mới xem xét hàng đợi ngoài (two-way door).

### Auth

Một mật khẩu chung từ env (`APP_PASSWORD_HASH`, argon2), session cookie httpOnly + Secure + SameSite=Lax, rate-limit đăng nhập. Phase 1 làm bản tối thiểu, phase 2 hardening.

### Hạ tầng và vận hành

- Docker image cho backend và frontend; `docker-compose.yml` cho dev, profile `local-llm` chạy Ollama.
- Deploy demo: Railway vùng Singapore (backend, frontend, Postgres managed).
- Observability tối thiểu trước demo: log JSON có `request_id`, endpoint `/health` và `/ready`, log thời gian từng bước LLM. **Không log nội dung OKR ở mức info.**
- Rollback: mỗi deploy là một image có tag; migration Alembic luôn có `downgrade`.

## Phương án đã cân nhắc

| Phương án | Lý do không chọn |
|---|---|
| Full-stack Next.js (API routes + Prisma) | Scheduler và validate schema LLM viết bằng Python + Pydantic + hypothesis tự nhiên hơn; team đã quen FastAPI |
| Để LLM tự xếp lịch | Không deterministic, không kiểm thử được, dễ vi phạm capacity/ngày lễ. Vi phạm tiêu chí nghiệm thu |
| Solver tối ưu (OR-Tools CP-SAT) cho scheduler | Mạnh nhưng khó giải thích và khó đảm bảo tie-break ổn định; list scheduling đủ cho single-user. Có thể thay sau vì scheduler là module độc lập |
| Hàng đợi Celery/Redis cho job | Thừa cho một user; tăng chi phí vận hành. Để dành khi cần |

## Hệ quả

- Phần then chốt (scheduler, calendar) test được hoàn toàn offline, chứng minh được các tiêu chí nghiệm thu bằng test tự động.
- Hai ngôn ngữ (Python, TypeScript) → cần giữ hợp đồng API qua OpenAPI.
- SQLite cho dev/test nhanh nhưng phải tránh tính năng riêng của Postgres; CI phase 2 thêm một job chạy test với Postgres.
