# Architecture Decision Records

| # | Quyết định | Trạng thái |
|---|---|---|
| [0001](0001-kien-truc-tong-the.md) | Kiến trúc tổng thể: monorepo FastAPI + Next.js, module backend, DB, job bất đồng bộ | Chấp nhận |
| [0002](0002-llm-provider-local-va-openai.md) | LLM provider Local + OpenAI dùng chung pipeline, validate, retry | Chấp nhận |
| [0003](0003-scheduler-deterministic.md) | Scheduler deterministic (list scheduling), feasibility, what-if | Chấp nhận |
| [0004](0004-model-local-ung-vien-eval.md) | Tập model local ứng viên để eval; mặc định `qwen3:8b` | Chấp nhận (chất lượng Local chưa nghiệm thu) |
| [0005](0005-cung-origin-qua-proxy-nextjs.md) | Frontend và API cùng origin qua proxy `/api/*` của Next.js (cookie first-party) | Chấp nhận |

ADR mới: copy định dạng của ADR gần nhất, đánh số tiếp theo. Không sửa ADR đã chấp nhận; nếu đổi quyết định thì viết ADR mới đánh dấu "Thay thế ADR xxxx".
