# Rubric chấm kế hoạch "hợp lý và khả thi"

Rubric dùng cho bộ OKR mẫu trong `okr_samples/` (bộ tạm do team soạn, thay bằng bộ của Bên A khi có). Mỗi lần chạy pipeline trên một mẫu với một cặp provider/model sinh ra **một kế hoạch**; người chấm cho điểm 0/1 theo từng tiêu chí, sau đó tổng hợp thành tỉ lệ đạt. Mục tiêu nghiệm thu: **tỉ lệ đạt ≥ 80%**.

Rubric chỉ chấm chất lượng suy luận của LLM (hỏi lại, phân rã, ước lượng, phụ thuộc). Tỉ lệ JSON hợp lệ, số lần retry và thời gian chạy được đo tự động và báo cáo riêng (ADR 0004), không nằm trong điểm rubric.

## 1. Định dạng mẫu

Mỗi file là một object JSON:

| Trường | Ý nghĩa |
|---|---|
| `schema_version` | Phiên bản định dạng, hiện là `1` |
| `sample_id` | Trùng tên file (không có đuôi `.json`) |
| `domain` | Lĩnh vực, chỉ để thống kê |
| `quarter` | `{year, number}` của quý lập kế hoạch (mọi mẫu: Q4/2026); truyền cho scheduler, không nằm trong input của LLM |
| `kr_kinds` | Loại từng KR theo `id`: `numeric` (số đo) hoặc `qualitative` (định tính); chỉ dùng khi chấm |
| `input` | Payload gửi thẳng vào pipeline, đúng model `OkrInput` trong `app/planner_llm/schemas.py`: `objectives[]`, `context` (chuỗi, có thể rỗng), `clarifications` (luôn rỗng ở lần chạy đầu), `language` (`vi` hoặc `en`; kế hoạch phải viết theo ngôn ngữ này) |
| `input.objectives[]` | `id`, `title`, `key_results[]`. Thứ tự trong mảng là thứ tự ưu tiên (phần tử đầu ưu tiên cao nhất) |
| `input.objectives[].key_results[]` | `id`, `text`, `metric`, `unit`, `baseline`, `target` (`null` khi không có) |
| `expected.clarify_status` | `ok` hoặc `needs_clarification` |
| `expected.clarification_topics` | Chủ đề câu hỏi kỳ vọng (chỉ có khi `needs_clarification`) |
| `expected.total_hours_range` | Khoảng tổng giờ hợp lý `{min, max}`, bằng tổng các khoảng theo KR; `null` khi cần hỏi lại |
| `expected.key_results` | Theo từng `kr_id`: `hours_range` và `must_cover` (những việc một kế hoạch hợp lý phải có) |
| `expected.grader_notes` | Ghi chú riêng cho người chấm: phụ thuộc kỳ vọng, chỗ dễ trùng lặp, ràng buộc giờ |

`backend/tests/test_eval_samples.py` kiểm tra định dạng và tính nhất quán của cả 10 file, kiểm tra `input` parse đúng bằng `OkrInput` mà không mất hay thừa trường, và kiểm tra 7 mẫu rõ ràng không bị precheck deterministic báo lỗi. Nếu Backend đổi `OkrInput` hoặc request của `POST /plans`, test này báo đỏ để cập nhật mẫu.

| Mẫu | Ngôn ngữ | Lĩnh vực | Objective / KR | Kỳ vọng |
|---|---|---|---|---|
| 01_saas_onboarding_vi | vi | product | 2 / 5 | ok |
| 02_aws_certification_en | en | learning | 1 / 3 | ok (2 giờ/ngày) |
| 03_health_fitness_vi | vi | health | 2 / 4 | ok (2 giờ/ngày) |
| 04_b2b_sales_en | en | business | 2 / 5 | ok |
| 05_payment_reliability_vi | vi | engineering | 2 / 5 | ok (sát quỹ giờ) |
| 06_mobile_app_launch_en | en | product | 3 / 6 | ok |
| 07_self_improvement_vague_vi | vi | personal_development | 1 / 2 | needs_clarification |
| 08_company_growth_vague_en | en | business | 2 / 4 | needs_clarification |
| 09_master_thesis_vi | vi | learning | 2 / 5 | ok (chuỗi phụ thuộc dài) |
| 10_customer_support_missing_baseline_en | en | customer_support | 1 / 3 | needs_clarification (thiếu baseline) |

## 2. Quỹ giờ dùng cho tiêu chí khả thi

Mọi mẫu dùng Q4/2026 (01/10–31/12/2026): **65 ngày làm việc** (66 ngày T2–T6, trừ thứ Ba 24/11/2026 là Ngày Văn hóa Việt Nam trong `app/calendar/data/vn_holidays_2026.json`). Quỹ giờ dùng được = số ngày × giờ/ngày × 0,9 (trừ buffer 10%).

| Giờ/ngày | Quỹ S | Dùng được (0,9 × S) | Áp dụng cho |
|---|---|---|---|
| 4 (mặc định) | 260 | **234** | Mọi mẫu không nêu giờ riêng |
| 2 | 130 | **117** | 02, 03 (context giới hạn 2 giờ/ngày) |

`run_eval.py` tính số ngày bằng chính `app/calendar` (lịch mặc định T2–T6 cộng dữ liệu ngày lễ), theo trường `quarter` của mẫu. Nếu dữ liệu ngày lễ, Bên A hoặc cấu hình eval đổi lịch (bật T7, đổi capacity), tính lại bảng này trước khi chấm. Kết quả lần 1 và lần 2 chạy với 66 ngày (quỹ 237,6 h và 118,8 h); khi so với các lần đó, dùng quỹ ghi trong `time_budget` của từng file kết quả.

## 3. Quy trình chấm

1. Chạy pipeline với `temperature=0` cho mỗi mẫu × mỗi cặp provider/model; xuất kết quả (trạng thái clarify, câu hỏi, danh sách task) ra file.
2. Hai người chấm **độc lập**, không trao đổi trước khi nộp phiếu. Nếu được, ẩn tên provider/model khỏi file kết quả.
3. Mỗi người điền `scoresheet_template.csv`: một dòng cho mỗi (mẫu, provider, model).
4. Chọn nhánh chấm theo `expected.clarify_status` của mẫu (mục 4 hoặc 5). Mọi tiêu chí không áp dụng để trống.
5. Tính độ đồng thuận (mục 7), thảo luận các ô lệch, ghi điểm thống nhất cuối cùng.

## 4. Nhánh A: mẫu `needs_clarification` (07, 08, 10)

| Mã | Tiêu chí | 1 điểm khi | 0 điểm khi |
|---|---|---|---|
| Q1 | Trạng thái đúng | Pipeline trả `needs_clarification` và **không** sinh task | Trả `ok` hoặc sinh bất kỳ task nào |
| Q2 | Câu hỏi đúng trọng tâm | 1–5 câu hỏi; chạm được yêu cầu tối thiểu ghi trong `grader_notes` của mẫu | Không có câu hỏi, quá 5 câu, hoặc bỏ sót yêu cầu tối thiểu |
| Q3 | Không bịa số liệu | Không tự đặt baseline, target hay số đo thay người dùng | Có bất kỳ con số do model tự đặt ra làm giả định (ví dụ "giả sử CSAT hiện tại là 75%") |

Kế hoạch **đạt** khi Q1 = Q2 = Q3 = 1. Nếu Q1 = 0 thì Q2, Q3 vẫn chấm để phân tích nhưng kế hoạch không đạt.

Cách so câu hỏi với chủ đề: một câu hỏi "chạm" chủ đề khi câu trả lời cho câu hỏi đó cung cấp được thông tin của chủ đề. Một câu hỏi gộp nhiều chủ đề vẫn tính cho tất cả các chủ đề nó chạm. Cách diễn đạt và ngôn ngữ không quan trọng.

Pipeline gộp hai nguồn câu hỏi: precheck deterministic (KR số đo thiếu baseline/target, nhận diện theo trường có cấu trúc và từ chỉ thay đổi như "tăng", "improve") và bước clarify của LLM. Mẫu 10 được precheck bắt hoàn toàn nên chủ yếu kiểm tra pipeline; mẫu 07 và 08 có KR chỉ LLM mới bắt được, `grader_notes` ghi rõ câu hỏi nào bắt buộc phải đến từ LLM. Khi kết quả có trường `source` của câu hỏi, ghi số câu theo nguồn vào cột ghi chú (ví dụ `precheck=2; llm=2`).

## 5. Nhánh B: mẫu `ok` (01–06, 09)

Nếu pipeline trả `needs_clarification` cho mẫu `ok` thì kế hoạch **không đạt**, ghi `false_clarification` vào cột ghi chú và để trống C1–C6. Ngoại lệ: câu hỏi chỉ ra một điểm thật sự thiếu mà người soạn mẫu bỏ sót; khi đó hai người chấm ghi lý do, báo người soạn để sửa mẫu, và loại cặp (mẫu, model) này khỏi mẫu số.

Mỗi tiêu chí là 0/1. "Task lỗi" trong bảng là task mà người chấm ghi cụ thể id vào cột ghi chú, để lúc đối chiếu hai người chấm so được từng task.

| Mã | Tiêu chí | 1 điểm khi (tất cả điều kiện) |
|---|---|---|
| C1 | Bao phủ mọi KR | (a) Mọi KR trong `input` có ≥ 1 task gắn đúng `kr_id`. (b) Mỗi mục `must_cover` của KR đó được ít nhất một task gắn cùng KR (hoặc KR liên quan nêu trong `grader_notes`) thực hiện. (c) Mỗi KR `numeric` có ít nhất một task đo hoặc theo dõi chỉ số (baseline, tracking, kiểm tra cuối kỳ). |
| C2 | Task cụ thể và kiểm chứng được | Số task lỗi ≤ max(1, 10% tổng số task, làm tròn xuống). Task lỗi khi: tiêu đề không có hành động và đối tượng rõ ("Nghiên cứu", "Cải thiện hiệu năng"); **hoặc** `done_criteria` không quan sát được (không nêu sản phẩm, con số, trạng thái hay người duyệt); **hoặc** task viết khác ngôn ngữ `language` của mẫu. |
| C3 | Ước lượng giờ hợp lý | (a) Mọi task có `estimate_hours` trong [2, 6]. (b) Tổng giờ nằm trong `expected.total_hours_range`. (c) Số task bị đánh giá lệch rõ rệt (thực tế cần gấp đôi trở lên hoặc chưa tới một nửa ước lượng) ≤ 1. |
| C4 | Phụ thuộc hợp lý | (a) Không có chu trình, không trỏ tới id không tồn tại. (b) Mọi phụ thuộc bắt buộc ghi trong `grader_notes` đều có (trực tiếp hoặc qua chuỗi). (c) Thứ tự hiển nhiên được tôn trọng: đo baseline trước cải tiến, thiết kế trước làm, làm trước kiểm thử, kiểm thử trước phát hành/nộp. (d) Số phụ thuộc vô lý (task sau không cần kết quả của task trước) ≤ 1. |
| C5 | Không trùng lặp | Không có cặp task nào (cùng KR hoặc khác KR) làm cùng một việc ra cùng một sản phẩm. Các bước khác nhau của cùng một sản phẩm (thiết kế, làm, kiểm thử) không phải trùng. Công việc lặp lại chia theo đợt (phỏng vấn đợt 1, đợt 2) không phải trùng. |
| C6 | Khả thi trong quý | (a) Tổng giờ ≤ quỹ dùng được ở mục 2 (theo giờ/ngày của mẫu). (b) Không có task đòi hỏi thời gian ngoài quý (ví dụ "chạy thử nghiệm 4 tháng") hoặc vi phạm hạn nêu trong KR. (c) Không có task nguy hiểm hay phi thực tế theo `grader_notes` (ví dụ giảm cân cực đoan). |

Kế hoạch **đạt** khi C1 = C2 = C3 = C4 = C5 = C6 = 1.

### Quy ước cho các ca dễ lệch

- **Công việc lặp lại** (buổi tập, cuộc phỏng vấn, đợt gán nhãn): gộp thành task theo khối 2–6 giờ là đúng. Một task cho từng buổi 1 giờ vi phạm C3(a); một task 15 giờ cũng vi phạm C3(a).
- **Thời gian chờ** (duyệt store, chờ giảng viên phản hồi, chờ khách ký): là thời gian lịch, không phải giờ làm. Task "Chờ duyệt" có ước lượng giờ tính là task lỗi ở C2.
- **Task quản lý chung** ("Họp tổng kết tuần", "Review tiến độ OKR"): chấp nhận tối đa một task mỗi Objective, phải có `done_criteria` cụ thể; nhiều hơn thì mỗi task dư tính là task lỗi ở C2.
- **Task đúng nhưng gắn sai KR**: C1 vẫn tính cho KR mà task thực sự phục vụ nếu `grader_notes` nêu hai KR liên quan; ngược lại, KR bị thiếu task thì C1 = 0.
- **Việc do người khác làm** (dev, designer, đội sales): task của người lập kế hoạch là giao việc, viết spec, review hoặc nghiệm thu; chấp nhận nếu `done_criteria` kiểm chứng được.
- **`must_cover` là tối thiểu, không phải danh sách đóng**: task thêm vào hợp lý không bị trừ điểm, miễn không làm vỡ C3(b) hoặc C6.
- **Không chắc**: chấm theo nghĩa hẹp của câu chữ trong bảng tiêu chí, ghi lý do vào ghi chú để thảo luận ở bước đối chiếu.

## 6. Tổng hợp

Với mỗi cặp provider/model:

- **Tỉ lệ đạt** = số kế hoạch đạt / số mẫu được chấm (10, trừ mẫu bị loại theo ngoại lệ ở mục 5). **Đạt nghiệm thu khi ≥ 80%**, tức ít nhất 8/10.
- Báo cáo thêm (không tính vào tỉ lệ đạt): tỉ lệ hỏi lại đúng trên 3 mẫu `needs_clarification` (Q1), tỉ lệ không hỏi thừa trên 7 mẫu `ok`, tỉ lệ đạt theo từng tiêu chí C1–C6 và Q1–Q3, tỉ lệ đạt theo ngôn ngữ vi/en.
- So sánh provider/model dựa trên điểm đã thống nhất sau đối chiếu, không dùng điểm của từng người chấm riêng lẻ.

Ví dụ: model X đạt 6/7 mẫu `ok` và 2/3 mẫu `needs_clarification` → tỉ lệ đạt = 8/10 = 80%, đạt nghiệm thu.

## 7. Độ đồng thuận giữa hai người chấm

- Tính trên từng ô tiêu chí (Q1–Q3 hoặc C1–C6) của mọi dòng: **đồng thuận = số ô trùng điểm / tổng số ô được chấm**. Mục tiêu **≥ 90%**; có thể báo thêm Cohen's kappa.
- Kết luận đạt/không đạt của từng kế hoạch nên trùng ở ít nhất 9/10 mẫu cho mỗi model.
- Nếu đồng thuận < 90%: hai người chấm cùng xem các ô lệch, xác định tiêu chí nào mơ hồ, bổ sung quy ước ở mục 5 rồi chấm lại các dòng bị ảnh hưởng.
- Điểm cuối cùng là điểm sau thảo luận; ghi lại số ô lệch ban đầu trong báo cáo eval.

## 8. Phiếu chấm

Dùng `scoresheet_template.csv`. Quy ước cột:

- `clarify_status_actual`: trạng thái pipeline trả về (`ok`, `needs_clarification`, `error`).
- `Q1`–`Q3`, `C1`–`C6`: `1`, `0` hoặc để trống nếu không áp dụng.
- `pass`: `1` nếu kế hoạch đạt theo mục 4 hoặc 5, ngược lại `0`. Lỗi pipeline (`error`) tính `pass = 0`.
- `failed_task_ids`: id các task lỗi (phân tách bằng `;`), dùng khi đối chiếu C2–C5.
- `notes`: lý do cho mọi ô `0`, và `false_clarification` nếu có.
