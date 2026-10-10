# ADR 0002 — LLM provider: Local và OpenAI dùng chung pipeline

- Trạng thái: Chấp nhận
- Ngày: 2026-09-30

## Bối cảnh

Board yêu cầu hỗ trợ cả LLM chạy local (dữ liệu không rời máy, 0 USD) và OpenAI (chất lượng, tốc độ ổn định). Người dùng chọn trong Cài đặt. LLM chỉ được dùng để **suy luận** (hỏi lại, phân rã theo KR, ước lượng giờ, phụ thuộc, gộp task trùng); mọi phép tính ngày/giờ do scheduler (ADR 0003).

## Quyết định

### Interface chung

```python
class LLMProvider(Protocol):
    name: str            # "local" | "openai"
    model: str
    max_concurrency: int

    async def generate_json(self, prompt: Prompt, schema: type[BaseModel]) -> dict: ...
    async def health_check(self) -> ProviderHealth: ...
```

- `Prompt` gồm `system`, `user` và metadata (bước pipeline, `kr_id`), không chứa logic riêng provider.
- `schema` là model Pydantic; JSON Schema sinh bằng `model_json_schema()` và chuẩn hóa về dạng strict (mọi field `required`, `additionalProperties: false`) để dùng được cho cả OpenAI Structured Outputs và Ollama `format`.
- Hai adapter nằm trong `backend/app/planner_llm/providers/`:
  - `LocalProvider`: mặc định gọi Ollama native `POST /api/chat` với `format=<json schema>`, `stream=false`, `options.temperature=0`. Chế độ `openai_compatible` gọi `POST /v1/chat/completions` với `response_format: {type: json_schema}` cho LM Studio / vLLM.
  - `OpenAIProvider`: SDK chính thức, `response_format` JSON Schema `strict: true`.

### Validate và retry (chung cho cả hai provider)

1. Parse JSON → validate Pydantic → validate rule (giờ trong [2, 6], id hợp lệ, không chu trình phụ thuộc, mọi KR có ít nhất một task).
2. Lỗi → gửi lại prompt kèm mô tả lỗi cụ thể, **tối đa 2 lần retry**.
3. Vẫn lỗi → trả lỗi có cấu trúc cho UI kèm gợi ý đổi provider. **Không tự động chuyển** sang OpenAI (tránh gửi dữ liệu ra ngoài khi người dùng chưa đồng ý).

### Cấu hình

| Biến env | Mặc định | Ghi chú |
|---|---|---|
| `LLM_PROVIDER` | `auto` | `auto` = Local nếu Ollama phản hồi `GET /api/tags`, ngược lại OpenAI |
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434` | Trong docker-compose: `http://ollama:11434` |
| `LOCAL_LLM_API_STYLE` | `ollama` | `ollama` hoặc `openai_compatible` |
| `LOCAL_LLM_MODEL` | `qwen3:8b` | Chốt sau eval (ADR 0004) |
| `LOCAL_LLM_CONCURRENCY` | `1` | 1–2 để tránh tràn RAM/VRAM |
| `LOCAL_LLM_TIMEOUT_SECONDS` | `180` | |
| `OPENAI_API_KEY` | (trống) | Chỉ qua env/secret, không lưu DB dạng rõ |
| `OPENAI_MODEL_CLARIFY` | `gpt-4o-mini` | Chốt sau eval |
| `OPENAI_MODEL_DECOMPOSE` | `gpt-4o-mini` | Chốt sau eval |
| `OPENAI_MODEL_DEDUP` | `gpt-4o-mini` | Chốt sau eval |
| `OPENAI_CONCURRENCY` | `5` | |

Lựa chọn provider trong Cài đặt được lưu DB và ghi đè `LLM_PROVIDER`. API key OpenAI **không** nhập qua UI ở phase 1 (security by default); nếu cần ở phase 2 thì lưu mã hóa và phải qua SecurityEngineer review.

### Truy vết

Mỗi `PlanRun` lưu `provider`, `model` từng bước, số lần retry, thời gian từng bước, lỗi JSON (không lưu nội dung OKR vào log).

### Nút "Kiểm tra kết nối"

`POST /settings/llm/test` gọi `health_check()`: một prompt nhỏ với schema nhỏ, trả `{ok, provider, model, latency_ms, error}`.

## Phương án đã cân nhắc

| Phương án | Lý do không chọn |
|---|---|
| Chỉ dùng endpoint OpenAI-compatible cho mọi local runtime | Ollama OpenAI-compatible hỗ trợ `json_schema` chưa đồng đều giữa các phiên bản; native `format` ổn định hơn. Vẫn giữ chế độ `openai_compatible` cho LM Studio/vLLM |
| LangChain / LlamaIndex | Thêm lớp trừu tượng nặng cho 3 lời gọi có cấu trúc; khó kiểm soát retry và schema strict |
| Tự động fallback sang OpenAI khi local lỗi | Vi phạm quyền riêng tư dữ liệu người dùng đã chọn local |

## Hệ quả

- Pipeline, prompt và test dùng chung; thêm provider mới (Anthropic, Gemini) chỉ cần một adapter.
- Test pipeline dùng `FakeProvider` trả JSON cố định, không cần mạng.
- Local chậm hơn: UI phải hiển thị tiến trình theo từng KR; mục tiêu 60 giây chỉ áp dụng cho OpenAI.
