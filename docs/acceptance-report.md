# Báo cáo nghiệm thu theo tiêu chí

Ngày chạy: 01/10/2026 · Máy: macOS (darwin 25.6), Python 3.12, Node 24, Chromium (Playwright 1.63).

Mọi test dưới đây chạy **không cần mạng và không cần LLM thật**: backend dùng `FakeProvider`
với kịch bản trả lời cố định. Riêng thời gian chạy với OpenAI (tiêu chí 8) được đo trong eval, không
chạy trong CI.

## Tóm tắt

| # | Tiêu chí | Test tự động | Kết quả |
|---|----------|--------------|---------|
| 1 | Không xếp task vào T7/CN/ngày lễ khi tắt; xếp đúng khi bật | `backend/tests/acceptance/test_days_off.py` (4 test) | ✅ Đạt |
| 2 | Không vượt ngày cuối quý, không vi phạm phụ thuộc | `backend/tests/acceptance/test_quarter_end_and_dependencies.py` (3 test) | ✅ Đạt |
| 3 | Giờ/ngày ≤ capacity với nhiều OKR và task nhiều ngày | `backend/tests/acceptance/test_daily_capacity.py` (1 test + 40 quý ngẫu nhiên) | ✅ Đạt |
| 4 | Mỗi KR có ≥ 1 task; mỗi task truy về đúng KR | `backend/tests/acceptance/test_kr_traceability.py` (4 test) | ✅ Đạt |
| 5 | OKR mơ hồ → hỏi lại, không tạo kế hoạch | `backend/tests/acceptance/test_vague_okr_clarification.py` (4 test) | ✅ Đạt |
| 6 | Quá tải → cảnh báo + phương án, không nhồi task | `backend/tests/acceptance/test_overload.py` (4 test) | ✅ Đạt |
| 7 | Cùng input + cấu hình → lịch giống hệt (so byte JSON) | `backend/tests/acceptance/test_determinism.py` (3 test) | ✅ Đạt |
| 8 | Có hiển thị tiến độ; OpenAI ≤ 60 s | `backend/tests/acceptance/test_progress_and_timing.py` (3 test) | ✅ Tiến độ đạt · ⏳ 60 s OpenAI chưa đo (xem ghi chú) |
| E2E | Luồng MVP: đăng nhập → quý → OKR → hỏi lại → lịch | `frontend/e2e/mvp-flow.spec.ts` | ✅ Đạt |
| E2E | Xếp lại lịch + what-if (phương án quá tải) | `frontend/e2e/reschedule-whatif.spec.ts` | ✅ Đạt |

Tổng: **66 test nghiệm thu backend đạt** (7,2 s), **2 test E2E Playwright đạt** (~25 s, chạy lại 3 lần
đều xanh).

## Chi tiết theo tiêu chí

Các test nghiệm thu đi qua API thật (FastAPI + SQLite/Postgres + scheduler), chỉ thay LLM bằng
`FakeProvider`. Hàm `assert_schedule_invariants` (`backend/tests/acceptance/support.py`) kiểm tra chung cho
mọi lịch: nằm trong cửa sổ quý, không rơi vào ngày nghỉ, không vượt capacity ngày, tổng phân bổ bằng ước
lượng, task phụ thuộc bắt đầu sau khi task trước kết thúc, và mỗi task mở hoặc được xếp hoặc nằm trong
danh sách không xếp được.

### 1. Ngày nghỉ (T7/CN/lễ/nghỉ phép)

| Test | Kiểm tra |
|------|----------|
| `test_switched_off_weekends_and_holidays_get_no_work_even_with_capacity` | T7/CN có capacity 4h nhưng công tắc tắt → không phút nào rơi vào T7, CN, lễ 24/11 |
| `test_switching_weekends_and_holidays_on_schedules_work_on_them` | Bật cả 3 công tắc ở cấu hình quý → 03/10 (T7), 04/10 (CN), 24/11 (lễ) được xếp việc |
| `test_each_switch_only_opens_its_own_kind_of_day` | Mỗi công tắc chỉ mở đúng loại ngày của nó |
| `test_leave_days_get_no_work` | Ngày nghỉ phép không có việc |

### 2. Cuối quý và phụ thuộc

| Test | Kiểm tra |
|------|----------|
| `test_work_that_does_not_fit_stays_unscheduled_instead_of_passing_quarter_end` | 600h việc vào quý 260h: ngày muộn nhất là 31/12, phần dư nằm trong `unscheduled` với lý do `exceeds_quarter`/`dependency_unscheduled` |
| `test_dependencies_finish_before_dependents_start_even_across_key_results` | Chuỗi phụ thuộc trong KR và giữa các KR: task sau bắt đầu sau ngày kết thúc task trước |
| `test_quarter_already_under_way_is_scheduled_from_today` | Quý đang chạy (hôm nay 16/11) → không xếp gì trước hôm nay |

### 3. Capacity mỗi ngày

| Test | Kiểm tra |
|------|----------|
| `test_several_okrs_with_multi_day_tasks_never_overfill_a_day` | 3 Objective × 2 KR, capacity khác nhau theo thứ (2h–6h), task 2,5–6h trải nhiều ngày, có phụ thuộc chéo KR → không ngày nào vượt capacity; `days[].scheduled_minutes` khớp tổng phân bổ |
| `test_random_multi_okr_quarters_never_overfill_a_day` (40 seed) | Quý sinh ngẫu nhiên (capacity, T7/CN, lễ, nghỉ phép, phụ thuộc, ưu tiên) → bất biến giữ nguyên |

### 4. Truy vết KR ↔ task

| Test | Kiểm tra |
|------|----------|
| `test_every_key_result_gets_tasks_and_every_task_traces_to_its_key_result` | 5 KR đều có task; mỗi task có `key_result_id`/`objective_id` đúng, cả trong lịch |
| `test_key_result_left_without_tasks_by_the_llm_is_asked_again` | LLM trả danh sách rỗng lần đầu → pipeline hỏi lại, cuối cùng KR vẫn có task |
| `test_plan_fails_instead_of_storing_a_key_result_without_tasks` | LLM luôn trả rỗng → kế hoạch thất bại (`invalid_llm_output`), không lưu task, không có lịch |
| `test_tasks_pointing_at_another_key_result_are_rejected` | Task trỏ tới KR không tồn tại bị từ chối và hỏi lại |

### 5. OKR mơ hồ

| Test | Kiểm tra |
|------|----------|
| `test_key_result_without_baseline_or_target_is_asked_back_without_a_plan` | KR "Tăng doanh thu…" thiếu baseline → câu hỏi về baseline, không task, không lịch, không gọi bước phân rã |
| `test_okr_the_llm_finds_unclear_is_asked_back_without_a_plan` | LLM đánh giá chưa rõ → trả câu hỏi, không có kế hoạch |
| `test_answering_the_questions_unlocks_the_plan` | Trả lời câu hỏi → kế hoạch được tạo |
| `test_okr_without_key_results_is_rejected_before_any_llm_call` | Objective không có KR bị chặn trước khi gọi LLM |

### 6. Quá tải

| Test | Kiểm tra |
|------|----------|
| `test_overloaded_quarter_is_flagged_red_and_extra_tasks_are_left_out` | 360h việc / 260h quỹ → trạng thái đỏ; task dư nằm ngoài lịch (không ngày nào vượt capacity); chỉ Objective ưu tiên thấp bị trễ |
| `test_overload_comes_with_options_computed_by_the_scheduler` | Có đủ 3 nhóm phương án; thiếu hụt bằng tổng ước lượng của task trễ; xem trước "tạm dừng Objective thấp" hết đỏ nhưng lịch chưa đổi |
| `test_options_change_the_plan_only_when_applied_and_can_be_undone` | Áp dụng "tăng giờ mỗi ngày" → hết đỏ; hoàn tác → đỏ lại |
| `test_tight_quarter_uses_the_buffer_with_a_yellow_warning` | Dùng vào vùng đệm 10% → vàng, cảnh báo `uses_buffer` |

### 7. Tất định

| Test | Kiểm tra |
|------|----------|
| `test_same_okr_and_settings_on_two_fresh_installs_give_identical_schedule_bytes` | Hai cơ sở dữ liệu mới, cùng OKR + lịch làm việc (capacity lệch, T7, nghỉ phép) → JSON lịch giống từng byte (bỏ `created_at`, `plan_run_id`) |
| `test_rescheduling_an_unchanged_quarter_reproduces_the_schedule_bytes` | Xếp lại quý không đổi → byte giống hệt |
| `test_scheduler_output_bytes_ignore_process_hash_seed_and_task_order` | Chạy scheduler ở tiến trình riêng với `PYTHONHASHSEED` 0/1/4242 và thứ tự input xuôi/ngược/xáo trộn → byte giống hệt |

### 8. Tiến độ và thời gian

| Test | Kiểm tra |
|------|----------|
| `test_progress_is_streamed_stage_by_stage_until_the_plan_is_ready` | Luồng SSE: số thứ tự liên tục, % không giảm, đủ các bước precheck → clarify → decompose (từng KR, x/y) → dedup → schedule, kết thúc `succeeded` 100% |
| `test_progress_can_be_read_while_the_plan_is_still_running` | Đọc `GET /plans/{id}` khi đang chạy thấy tiến độ tăng dần < 100% |
| `test_eval_flags_openai_plans_slower_than_sixty_seconds` | Công cụ eval đánh dấu `over_60s` đúng ngưỡng (60 000 ms đạt, 60 001 ms vượt) và chỉ áp dụng cho OpenAI |

## E2E Playwright

Chạy bằng `cd frontend && npm run test:e2e`. Playwright tự bật:

- backend thật `python -m tests.e2e_server` (SQLite mới mỗi lần, `FakeProvider`, mật khẩu test riêng), cổng 8217;
- `next dev` cổng 3217, proxy `/api` sang backend đó.

| Spec | Các bước |
|------|----------|
| `mvp-flow.spec.ts` | Đăng nhập → chọn quý → điền OKR mẫu → gửi → thấy thanh tiến độ → trang hỏi lại, trả lời → thấy "x/y KRs done" → tự chuyển sang danh sách task → kiểm tra lịch qua API → tab Lịch hiển thị task |
| `reschedule-whatif.spec.ts` | Tạo quý 2027-Q1 quá tải qua API, thêm task → banner "lịch đã cũ" → Xếp lại → hộp xem trước (vẫn thiếu giờ) → Áp dụng → toast "vẫn quá tải" → Xem phương án → chọn "Tạm dừng O2" → khung xem trước chuyển khỏi đỏ, lịch chưa đổi → Áp dụng phương án → lịch hết đỏ, không còn task trễ |

Cài lần đầu: `npm ci && npx playwright install chromium`; backend cần `backend/.venv` (có thể đổi bằng
`E2E_PYTHON`).

## Ghi chú và việc còn mở

1. **OpenAI ≤ 60 s chưa đo thực tế**: môi trường chưa có `OPENAI_API_KEY`. Công cụ đo đã có và được test
   (`evals/run_eval.py`, ngưỡng `OPENAI_TIME_LIMIT_MS = 60_000`, trường `over_60s`). Cần board/CTO cấp key
   để chạy `python -m evals.run_eval run --provider openai --model <model>` và bổ sung kết quả vào `docs/eval-report.md`.
2. Bước `validate` của pipeline không phát sự kiện tiến độ riêng; giao diện coi bước này hoàn tất khi bước
   `schedule` bắt đầu. Test tiến độ phản ánh đúng hành vi đó.
3. Kiểm tra độ nhạy của bộ test (mutation thủ công, đã khôi phục): bỏ qua ngày lễ, cộng thêm 60 phút
   capacity, cho task phụ thuộc bắt đầu cùng ngày task trước kết thúc → mỗi lỗi đều làm test nghiệm thu đỏ.
4. `src/components/auth/login-form.test.tsx` (đếm ngược khi khoá đăng nhập) thỉnh thoảng đỏ (~1/4 lần
   chạy `npm run test`) do phụ thuộc thời gian; không liên quan tới thay đổi này.

## Lệnh verify đã chạy

```bash
cd backend && ruff check . && ruff format --check . && mypy && pytest -q
# ruff xanh khi bỏ qua backend/.probe_clarify.py (script thử chưa track của việc khác, không thuộc thay đổi này)
# 462 passed, 3 skipped (trong đó 66 test nghiệm thu)
cd frontend && npm run lint && npm run typecheck && npm run test && npm run build
# lint/typecheck/build xanh; vitest 179/179 (xem ghi chú 4)
cd frontend && npm run test:e2e
# 2 passed
```
