# Báo cáo eval kế hoạch OKR — Local và OpenAI

- Ngày chạy: 2026-10-01. Lần 1: 4 model local, pipeline và prompt ban đầu. Lần 2 (sau tối ưu): `qwen3:8b` và `qwen3:14b`, sau khi Backend sửa pipeline và prompt theo mục 5. Lần 3 (sau tối ưu vòng 3): `qwen3:8b` và `qwen3:14b`, sau khi Backend chặn task độn, chặn ước lượng thừa, sửa clarify và rút gọn dedup (mục 5c).
- Bộ mẫu: 10 OKR tạm trong `backend/evals/okr_samples/` (7 mẫu rõ ràng, 3 mẫu cần hỏi lại)
- Rubric: `backend/evals/RUBRIC.md`
- Trạng thái: **Local xong ba lần. OpenAI không chạy** theo quyết định của board ngày 2026-10-01 (không cấp `OPENAI_API_KEY` cho eval). Báo cáo không có số liệu OpenAI (xem mục 6).

## 1. Kết luận nhanh

### Lần 3 (sau tối ưu vòng 3)

- **Vẫn không model nào đạt 80%.** Cả `qwen3:8b` và `qwen3:14b` giữ **3/10**, vẫn chỉ đạt 3 mẫu cần hỏi lại; **0/7 mẫu rõ ràng đạt** ở cả hai model. C1 (đủ `must_cover`) là **0/7 ở cả hai**.
- Vòng tối ưu có tác dụng rõ ở chỗ được nhắm tới: task "độn" gần như hết (C2 `qwen3:8b` 1/7 → **6/7**, `qwen3:14b` 1/6 → **7/7**). `qwen3:14b` không còn hỏi thừa (7/7) và tốt lên ở hầu hết tiêu chí (C3 2/6 → 3/7, C4 2/6 → 5/7, C5 1/6 → 4/7). JSON sau retry vẫn 100% ở cả hai.
- Chưa sửa được: `qwen3:8b` trùng việc nhiều hơn (C5 2/7 → **0/7**, phần lớn là task "đo kết quả cuối" ghi lại kết quả đã có ở task trước); nhiều task riêng lẻ vẫn bị ước lượng thiếu (C3(c)). `qwen3:14b` mẫu 02 vẫn vượt quỹ quý (129 h so với 117 h) dù đã replan, và pipeline trả kế hoạch đó mà không cảnh báo.
- **Kể cả bỏ hẳn C1, cũng không model nào tới 80%.** Khi đó `qwen3:8b` vẫn 3/10, `qwen3:14b` lên 5/10 (mẫu 03 và 05 chỉ trượt C1). Vậy chỉ hiệu chỉnh `must_cover` thì không đủ đạt ngưỡng; lỗi C3, C4, C5 còn lại là lỗi của model và prompt (mục 5c.4).
- **Độ trễ chưa đạt mục tiêu** (`qwen3:8b`: trung vị 7 mẫu rõ ≤ 240 s, max ≤ 360 s). Đo được **379 s / 532 s**. Dedup nhanh hơn 2,6 lần (101 s → 38 s), nhưng decompose chậm hơn (282 s → 364 s) vì retry tăng từ 15 lên 25. Máy dev bị tải rất nặng suốt lần chạy (load average 70–170 khi chạy `qwen3:8b`, 380–590 khi chạy `qwen3:14b`), nên đây chưa phải số đo trên máy rảnh.
- **Model mặc định giữ nguyên `qwen3:8b` cho mọi máy** (mục 8.1). Theo thứ tự của ADR 0004: hai model hòa tỉ lệ đạt (3/10), `qwen3:8b` thắng ở C6 (7/7 so với 6/7). `qwen3:14b` tốt hơn ở C2–C5 nhưng chậm hơn khoảng 2,2 lần.

### Lần 2 (sau tối ưu)

- **Vẫn không model nào đạt 80%.** `qwen3:8b` tăng từ 1/10 lên **3/10**; `qwen3:14b` giữ **3/10**. Cả hai chỉ đạt 3 mẫu cần hỏi lại; **0/7 mẫu rõ ràng đạt** ở cả hai model.
- Các sửa pipeline có hiệu quả: bước clarify của LLM nay hỏi đủ các KR mơ hồ (Q2 3/3 ở cả hai model), `num_predict` cắt được output quá dài để retry (không còn treo đến hết timeout), JSON sau retry vẫn 100%.
- Ước lượng tổng giờ chuyển từ "quá thấp" sang "sát khoảng" với `qwen3:8b` (6/7 kế hoạch trong khoảng kỳ vọng, lần 1 là 1/7) nhưng sang "quá cao" với `qwen3:14b` (4/6 vượt trần, 2 kế hoạch vượt cả quỹ giờ của quý).
- Lỗi mới: số task tăng khoảng 1,7–1,9 lần, kéo theo nhiều task "độn" mơ hồ ("Implement improvements part 1/2", "Theo dõi và điều chỉnh"), nên C2 giảm mạnh (`qwen3:14b` từ 6/7 xuống 1/6). C1 (đủ `must_cover`) vẫn gần như 0. `qwen3:14b` hỏi thừa một mẫu rõ ràng (mẫu 03).
- Thời gian mỗi plan tăng khoảng 3,5 lần với `qwen3:8b` (trung vị 103 s lên 364 s) và 1,4 lần với `qwen3:14b` (303 s lên 420 s).
- **Chốt model mặc định: `qwen3:8b` cho cả máy 16GB và máy ≥32GB** (mục 8). Không model nào đạt tiêu chí rubric của ADR 0004, và `qwen3:14b` không cho điểm cao hơn mà chậm hơn, hay vượt quỹ giờ hơn. Nghiệm thu 80% chưa đạt; cần CTO quyết định vòng tiếp theo (mục 5b.5).

### Lần 1

- **Không model local nào đạt nghiệm thu 80%.** Tốt nhất là `qwen3:14b` và `gemma3:12b` với 3/10. Cả 3 kế hoạch đạt đều là mẫu cần hỏi lại; **0/7 mẫu rõ ràng đạt** ở mọi model.
- Lỗi chung của mọi model: thiếu việc bắt buộc (`must_cover`, C1 = 0% ở cả bốn model), ước lượng giờ thấp (C3), phụ thuộc thiếu hoặc vô lý (C4) và trùng việc giữa các KR (C5).
- Có ba lỗi ở pipeline và prompt (không phải lỗi model), sửa được ngay:
  1. Bước clarify **bỏ mất câu hỏi của LLM** khi model trả `status: "ok"` nhưng vẫn kèm câu hỏi. `qwen3:8b` trượt mẫu 07 vì lỗi này.
  2. `LocalProvider` không giới hạn số token sinh ra, nên `llama3.1:8b` **lặp vô hạn** trong JSON ở bước dedup đến khi timeout, 7/7 mẫu rõ ràng.
  3. Prompt decompose ghi "aiming for about 4" giờ, nên model đặt gần như mọi task 4 giờ và tổng giờ thấp hơn mức kỳ vọng.
- **Đề xuất model mặc định (tạm):** `qwen3:14b` cho máy ≥32GB, giữ `qwen3:8b` cho máy 16GB. Không model nào đạt tiêu chí ADR 0004, nên **chưa chốt**. Chạy lại eval sau khi Backend sửa các điểm ở mục 5 và sau khi có mốc OpenAI. (Lần 2 đã chạy; OpenAI không chạy theo quyết định board, xem mục 6.)

## 2. Thiết lập

| Mục | Giá trị |
|---|---|
| Máy | MacBook Pro M1 Max, 32GB RAM, Ollama (API native `/api/chat`, `format` = JSON Schema) |
| Pipeline | `run_pipeline` của `app/planner_llm` (precheck → clarify → decompose theo KR → dedup theo Objective → validate), không sửa gì |
| Tham số | `temperature=0`, `max_retries=2`, concurrency local = 1 (mặc định của app), qwen3 tắt thinking |
| Timeout mỗi lần gọi | 600 s (app mặc định 180 s). Nới ra để model 12–14B không bị cắt oan. Riêng `llama3.1:8b` mẫu 06 và 09 chạy với 180 s để tiết kiệm thời gian, vì 5/5 mẫu rõ ràng trước đó đều treo ở dedup đến hết 600 s; kết quả vẫn là lỗi đó. |
| Số lần chạy | 1 lần cho mỗi (mẫu × model), vì temperature 0 |
| Chấm | 2 grader độc lập, **blinded** (tên model thay bằng mã băm), chấm theo đúng RUBRIC, sau đó đối chiếu. Grader là hai phiên agent AI riêng biệt, không phải người (xem mục 7). |

Script: `backend/evals/run_eval.py`. Kết quả thô: `backend/evals/results/<provider>__<model>/<sample>.json`, gồm kế hoạch, câu hỏi, thời gian từng bước, retry, lỗi bị từ chối và các phần rubric chấm tự động được. Phiếu chấm: `backend/evals/results/scores.csv`, gồm dòng của grader A, grader B và dòng `agreed`. Số tổng hợp: `backend/evals/results/summary.json`.

Từ lần 3, `backend/evals/results/` chứa kết quả lần 3 (`qwen3:8b`, `qwen3:14b`). Kết quả, phiếu chấm và `summary.json` của các lần trước được giữ nguyên: lần 1 (4 model) trong `backend/evals/results/round1/`, lần 2 trong `backend/evals/results/round2/`. Lần 2 và lần 3 dùng cùng thiết lập ở bảng trên (timeout 600 s, `temperature=0`, `max_retries=2`, concurrency 1, cùng máy). Mỗi lần dùng một seed riêng cho grading pack để mã blinded khác nhau (lần 2: `--seed 2027`; lần 3: `--seed 2028`, mã `Mc88b` và `M3f57`). Grader của mỗi lần không được đọc thư mục của các lần trước.

## 3. Kết quả Local

### 3.1 Tổng hợp

| Model | Tỉ lệ đạt rubric | Hỏi lại đúng (3 mẫu mơ hồ) | Không hỏi thừa (7 mẫu rõ) | JSON hợp lệ lần đầu | JSON hợp lệ sau retry | Retry | Lỗi pipeline | Thời gian/mẫu (trung vị / max) |
|---|---|---|---|---|---|---|---|---|
| `qwen3:8b` | **1/10** (10%) | 3/3 | 7/7 | 98,2% | 100% | 1 | 0 | 103 s / 241 s |
| `llama3.1:8b` | **1/10** (10%) | 3/3 | 7/7 | 78,4% | **86,3%** | 11 | 7 (treo ở dedup) | 541 s / 870 s |
| `gemma3:12b` | **3/10** (30%) | 3/3 | 6/7 | 86,8% | 100% | 7 | 0 | 455 s / 664 s |
| `qwen3:14b` | **3/10** (30%) | 3/3 | 7/7 | 96,5% | 100% | 2 | 0 | 303 s / 466 s |

- "Hỏi lại đúng" là Q1 (trả `needs_clarification`, không sinh task). "JSON hợp lệ" tính trên từng lần gọi LLM. Một lần gọi bị timeout vì model lặp vô hạn cũng tính là không hợp lệ.
- Không lần nào bị lỗi cú pháp JSON: Ollama ép theo grammar của schema. Mọi lần bị từ chối là do vi phạm luật (`estimate_hours` > 6, gộp hai task nối tiếp khi dedup).
- Thời gian trung bình theo bước (s): `qwen3:8b` clarify 4,7 / decompose 134 / dedup 12,9; `qwen3:14b` 13,4 / 292 / 46; `gemma3:12b` 13,2 / 482 / 61. Hầu hết thời gian nằm ở bước decompose (các KR chạy tuần tự vì concurrency local = 1).

### 3.2 Theo tiêu chí rubric (điểm đã đối chiếu)

| Model | Q1 | Q2 | Q3 | C1 | C2 | C3 | C4 | C5 | C6 | Đạt vi / en |
|---|---|---|---|---|---|---|---|---|---|---|
| `qwen3:8b` | 3/3 | 1/3 | 3/3 | 0/7 | 3/7 | 0/7 | 1/7 | 0/7 | 7/7 | 0/5 / 1/5 |
| `llama3.1:8b` | 3/3 | 1/3 | 3/3 | – | – | – | – | – | – | 0/5 / 1/5 |
| `gemma3:12b` | 3/3 | 3/3 | 3/3 | 0/6 | 6/6 | 2/6 | 4/6 | 1/6 | 5/6 | 1/5 / 2/5 |
| `qwen3:14b` | 3/3 | 3/3 | 3/3 | 0/7 | 6/7 | 1/7 | 0/7 | 2/7 | 7/7 | 1/5 / 2/5 |

`llama3.1:8b` không có C1–C6 vì cả 7 mẫu rõ ràng đều lỗi pipeline. `gemma3:12b` có 6 mẫu chấm C vì hỏi thừa ở mẫu 02.

### 3.3 Tổng giờ so với khoảng kỳ vọng (mẫu rõ ràng)

| Mẫu | Kỳ vọng (h) | `qwen3:8b` | `gemma3:12b` | `qwen3:14b` |
|---|---|---|---|---|
| 01 SaaS onboarding | 108–194 | 82 ↓ | 133 | 94 ↓ |
| 02 AWS cert | 56–106 | 56 | hỏi thừa | 68 |
| 03 Health | 66–110 | 56 ↓ | 100 | 76 |
| 04 B2B sales | 106–188 | 96 ↓ | 120 | 116 |
| 05 Payment reliability | 128–220 | 92 ↓ | 126 ↓ | 96 ↓ |
| 06 Mobile launch | 110–200 | 100 ↓ | 157 | 122 |
| 09 Master thesis | 120–202 | 90 ↓ | 113 ↓ | 102 ↓ |

↓ = dưới mức tối thiểu. Không kế hoạch nào vượt quỹ giờ dùng được (C6a đạt 100%): model đều ước lượng thấp, không cao.

## 4. Lỗi điển hình (để Backend tối ưu prompt)

Tỉ lệ đạt < 80% ở mọi model, nên dưới đây liệt kê lỗi theo tần suất, kèm ví dụ từ phiếu chấm.

1. **Thiếu việc bắt buộc (C1: 0/20 kế hoạch rõ ràng đạt).** Model làm phần "cốt lõi" của KR nhưng bỏ bước chuẩn bị, bảo vệ và bàn giao. Ví dụ: AWS thiếu billing alert và dọn tài nguyên sau lab, không có buffer thi lại; SaaS thiếu định nghĩa sự kiện activation và dashboard; payment thiếu SLO/SLI, game day đo MTTR và ngưỡng coverage trong CI; B2B thiếu bước định nghĩa ICP; luận văn thiếu bước sửa theo góp ý giảng viên và chưa có task nộp bài.
2. **Ước lượng giờ quá thấp và "mọi task 4 giờ" (C3).** Ví dụ: "gán nhãn 2.000 câu" 4 h (thực tế 17–33 h), "tập sức mạnh cả quý" 6 h, "15 cuộc gọi discovery" 4 h, "nâng coverage 45→75%" 6–10 h. `qwen3:8b` có 6/7 kế hoạch dưới mức giờ tối thiểu. Nguyên nhân chính là prompt decompose ghi "aiming for about 4" và không cho model biết quỹ thời gian của quý.
3. **Trùng việc giữa các KR (C5).** Mỗi KR được phân rã riêng, nên cùng một sản phẩm bị lên kế hoạch hai lần. Ví dụ: "dựng + triển khai in-app guide" có ở cả O1-KR2 và O1-KR3; gán nhãn dữ liệu lặp ở 4 KR của luận văn; hai biến thể giá dựng hai lần ở mẫu 06. Bước dedup gần như không gộp được các trường hợp này.
4. **Phụ thuộc sai (C4, `qwen3:14b` 0/7).** Thiếu phụ thuộc bắt buộc giữa các KR (thi thật không phụ thuộc bài thi thử cuối, chiến dịch không đứng sau bản phát hành). Có cả chuỗi phụ thuộc vô lý, ví dụ runbook lỗi 2→3→4→5 nối nhau dù độc lập. `cross_dependencies` của bước dedup hầu như để trống.
5. **Bước clarify của LLM không bổ sung câu hỏi (Q2).** Ở `qwen3:8b` và `llama3.1:8b`, mẫu 07 và 08 chỉ có câu hỏi của precheck (`llm=0`), nên thiếu câu hỏi bắt buộc về O1-KR1 và O2-KR1. Tái hiện với `qwen3:8b`:
   - Mẫu 07: model trả `{"status": "ok", "questions": [<2 câu hỏi đúng, gồm câu về kỹ năng cụ thể>]}`. Pipeline thấy `status == "ok"` nên **bỏ luôn câu hỏi**, và `clarify_errors` không bắt mâu thuẫn này.
   - Mẫu 08: model trả `ok` với danh sách rỗng, kể cả khi không truyền `already_asked`, tức prompt quá dễ dãi với KR định tính mơ hồ ("Get more customers", "Employees are happier").
6. **Model lặp vô hạn trong JSON (`llama3.1:8b`).** Ở temperature 0, bước dedup sinh `"remove_ids": ["O1-KR1.t2", ..., "O1-KR3.t4", "O1-KR1.t4", "O1-KR2.t4", ...]` lặp mãi không đóng mảng (đã tái hiện với `num_predict=600`: `done_reason=length`). Không có giới hạn token nên mỗi lần treo tốn trọn timeout, và lỗi timeout bị xếp thành `provider_unavailable` nên không được retry.
7. **Hỏi thừa (`gemma3:12b`, mẫu 02).** Model hỏi "điểm đỗ kỳ thi AWS SAA là bao nhiêu". Đây là thông tin công khai, không phải thông tin thiếu của người dùng.

## 5. Đề xuất sửa (Backend)

Sắp theo tác động lên tỉ lệ đạt:

1. **Clarify, sửa pipeline:** coi `questions` không rỗng là `needs_clarification` (hoặc để `clarify_errors` từ chối `status: "ok"` kèm câu hỏi để model sửa khi retry). Sửa này đủ để `qwen3:8b` qua Q2 mẫu 07.
2. **Clarify, sửa prompt:** yêu cầu duyệt **từng KR**. KR nào không có sản phẩm cụ thể hoặc chỉ số đo được thì phải hỏi. `already_asked` chỉ phủ các KR được nêu trong đó, không phải cả OKR. Không hỏi về kiến thức công khai; chỉ hỏi về hoàn cảnh của người dùng.
3. **LocalProvider:** đặt `options.num_predict` (ví dụ 4096 cho decompose, 2048 cho clarify/dedup) để vòng lặp kết thúc sớm thành `InvalidJSONError` rồi retry. Cân nhắc cho timeout của Local được retry một lần thay vì dừng ngay với `provider_unavailable`.
4. **Decompose, ước lượng giờ:** bỏ "aiming for about 4". Cho model biết quỹ thời gian (số ngày làm việc × giờ/ngày của quý) và yêu cầu **ước lượng tổng công sức của KR trước**, rồi mới chia thành khối 2–6 h. Việc lặp lại (buổi tập, cuộc gọi, gán nhãn) gộp thành nhiều khối sao cho tổng giờ thực tế.
5. **Decompose, độ phủ:** thêm checklist vòng đời cho mỗi KR: chuẩn bị/định nghĩa (tiêu chí, template, công cụ) → làm → kiểm tra/review → sửa theo góp ý → bàn giao/nộp/phát hành → đo kết quả. Với KR số đo: đo baseline, theo dõi định kỳ, đo cuối kỳ.
6. **Trùng lặp và phụ thuộc giữa KR:** phân rã các KR của cùng một Objective **tuần tự**, truyền danh sách task đã có của KR trước vào prompt (đổi lại tăng độ trễ), hoặc sửa prompt dedup để so theo *sản phẩm đầu ra* và bắt buộc kiểm tra "task đầu tiên của mỗi KR cần kết quả gì từ KR khác". Thêm luật: chỉ thêm `depends_on` khi task sau cần đầu ra của task trước; các việc lặp độc lập không nối chuỗi.

Sau khi sửa: chạy lại `python -m evals.run_eval run --force ...` cho `qwen3:8b` và `qwen3:14b` (khoảng 20 và 45 phút trên máy dev), rồi chấm lại.

## 5b. Sau tối ưu (eval lần 2)

Backend đã làm mục 5, điểm 1–6, trừ phương án phân rã tuần tự theo Objective (decompose vẫn chạy song song; thay vào đó thêm bước tìm quan hệ giữa các KR và kiểm tra từng KR). Lần 2 chạy lại đúng lệnh ở trên, cùng máy và cùng thiết lập. Thời gian thực tế: khoảng 46 phút cho `qwen3:8b` và 55 phút cho `qwen3:14b`.

### 5b.1 Tổng hợp trước/sau

| Model | Lần | Tỉ lệ đạt rubric | Hỏi lại đúng (3 mẫu mơ hồ) | Không hỏi thừa (7 mẫu rõ) | JSON hợp lệ lần đầu | JSON hợp lệ sau retry | Retry | Lần gọi LLM | Task TB/plan rõ | Trung vị tất cả / 7 mẫu rõ / max |
|---|---|---|---|---|---|---|---|---|---|---|
| `qwen3:8b` | 1 | 1/10 (10%) | 3/3 | 7/7 | 98,2% | 100% | 1 | 57 | 21,4 | 103 / 154 / 241 s |
| `qwen3:8b` | 2 | **3/10 (30%)** | 3/3 | 7/7 | 83,7% | **100%** | 15 | 92 | 37,4 | **364 / 380 / 476 s** |
| `qwen3:14b` | 1 | 3/10 (30%) | 3/3 | 7/7 | 96,5% | 100% | 2 | 57 | 25,3 | 303 / 359 / 466 s |
| `qwen3:14b` | 2 | **3/10 (30%)** | 3/3 | **6/7** | 100% | **100%** | 0 | 84 | 47,0 | **420 / 488 / 658 s** |

- Retry của `qwen3:8b` lần 2: 13 lần decompose bị từ chối vì task > 6 h (có lần model đặt 60 h, 120 h cho một task) và 2 lần dedup bị cắt ở giới hạn token (`response truncated at the token limit`). Cả hai loại đều được retry sửa xong. Không có timeout.
- Thời gian trung bình theo bước lần 2 (s): `qwen3:8b` clarify 7,8 / decompose 282 / dedup 101; `qwen3:14b` 14,0 / 410 / 116. Dedup chậm hơn lần 1 khoảng 8 lần (`qwen3:8b`) và 2,5 lần (`qwen3:14b`) vì có thêm bước tìm và nối quan hệ giữa các KR.

### 5b.2 Theo tiêu chí rubric (điểm đã đối chiếu)

| Model | Lần | Q1 | Q2 | Q3 | C1 | C2 | C3 | C4 | C5 | C6 | Đạt vi / en |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `qwen3:8b` | 1 | 3/3 | 1/3 | 3/3 | 0/7 | 3/7 | 0/7 | 1/7 | 0/7 | 7/7 | 0/5 / 1/5 |
| `qwen3:8b` | 2 | 3/3 | **3/3** | 3/3 | 1/7 | **1/7** | 1/7 | 3/7 | 2/7 | 7/7 | 1/5 / 2/5 |
| `qwen3:14b` | 1 | 3/3 | 3/3 | 3/3 | 0/7 | 6/7 | 1/7 | 0/7 | 2/7 | 7/7 | 1/5 / 2/5 |
| `qwen3:14b` | 2 | 3/3 | 3/3 | 3/3 | 0/6 | **1/6** | 2/6 | 2/6 | 1/6 | **4/6** | 1/5 / 2/5 |

`qwen3:14b` lần 2 có 6 mẫu chấm C vì hỏi thừa ở mẫu 03. Cả hai grader kết luận không áp dụng ngoại lệ: câu hỏi "giao gì cho chuyên gia dinh dưỡng để góp ý thực đơn" là việc kế hoạch phải tự làm, không phải thông tin bộ mẫu bỏ sót, và câu hỏi còn gắn nhầm KR.

Mẫu duy nhất gần đạt là mẫu 01 của `qwen3:8b`: đạt C1, C3, C4, C6, chỉ trượt C2 (5 task mơ hồ, ngưỡng 3) và C5 (hai chuỗi thiết kế lại onboarding song song).

### 5b.3 Tổng giờ so với khoảng kỳ vọng (mẫu rõ ràng)

| Mẫu | Kỳ vọng (h) | `qwen3:8b` lần 1 → 2 | `qwen3:14b` lần 1 → 2 |
|---|---|---|---|
| 01 SaaS onboarding | 108–194 | 82 ↓ → 139 | 94 ↓ → 172 |
| 02 AWS cert | 56–106 | 56 → 110 ↑ | 68 → 155 ↑ (vượt quỹ 118,8) |
| 03 Health | 66–110 | 56 ↓ → 97 | 76 → hỏi thừa |
| 04 B2B sales | 106–188 | 96 ↓ → 152 | 116 → 192 ↑ |
| 05 Payment reliability | 128–220 | 92 ↓ → 151 | 96 ↓ → 162 |
| 06 Mobile launch | 110–200 | 100 ↓ → 181 | 122 → 238 ↑ (vượt quỹ 237,6) |
| 09 Master thesis | 120–202 | 90 ↓ → 165 | 102 ↓ → 206 ↑ |

↓ = dưới mức tối thiểu, ↑ = trên mức tối đa. Tổng giờ trong khoảng: `qwen3:8b` 1/7 → **6/7**; `qwen3:14b` 4/7 → 2/6. Dù vậy C3 vẫn thấp vì tiêu chí C3(c): nhiều task riêng lẻ bị ước lượng lệch quá 2 lần (ví dụ 2 h cho mỗi lượt 5 câu thi thử, 6 h để làm cả chương trình referral, 4 h cho 5 buổi demo cộng ký 5 hợp đồng).

### 5b.4 Lỗi điển hình còn lại

1. **Thiếu `must_cover` (C1: 1/13 kế hoạch đạt).** Checklist vòng đời làm model thêm bước chuẩn bị và đo lường chung chung, nhưng vẫn bỏ các mục cụ thể theo lĩnh vực. Các mục bị cả hai model bỏ (và đã bị bỏ ở lần 1): AWS billing alert và dọn tài nguyên sau lab; payment SLO/SLI và dashboard, health check/failover, game day đo MTTR, ngưỡng coverage trong CI; mobile in-app rating prompt và trả lời review tiêu cực; SaaS định nghĩa sự kiện activation và dashboard; B2B ICP, template proposal, dọn dữ liệu CRM cũ; luận văn đọc ≥ 20 bài, thử ≥ 2 hướng cải tiến, chọn hội thảo và mẫu định dạng.
2. **Task "độn" mơ hồ (C2 giảm: `qwen3:8b` 3/7 → 1/7, `qwen3:14b` 6/7 → 1/6).** Khi được yêu cầu ước lượng đủ công sức của KR, model chia việc thành "Implement rating improvement strategies part 1/2", "Thực hiện cải thiện uptime phần 1/2", "Monitor and adjust", "Đánh giá và điều chỉnh nếu cần", với `done_criteria` chỉ lặp lại tiêu đề ("đã được tối ưu", "ổn định hơn", "strategy revised and finalized").
3. **Trùng việc giữa các KR vẫn còn (C5: 3/13 đạt).** Ví dụ: runbook 5 lỗi viết ở cả O1-KR3 và O2-KR2 (mẫu 05, `qwen3:8b`); thí nghiệm giá dựng hai lần ở O3-KR1 và O3-KR2 (mẫu 06, cả hai model); thực đơn 4 tuần lập và gửi chuyên gia 4 lần (mẫu 03, `qwen3:8b`); đặt lịch thi hai lần, học lại phần đã có ở KR1 (mẫu 02, cả hai model); hai chuỗi thiết kế lại onboarding (mẫu 01, cả hai model).
4. **Phụ thuộc bắt buộc vẫn thiếu hoặc sai thứ tự (C4: 5/13 đạt).** Có tiến bộ (luận văn có đủ chuỗi gán nhãn → thực nghiệm → bài báo → seminar), nhưng: thi thật không phụ thuộc bài thi thử cuối (mẫu 02, cả hai model); chiến dịch ra mắt không phụ thuộc bản phát hành (mẫu 06, `qwen3:8b`); đo baseline sau cải tiến (mẫu 03, 04 với `qwen3:8b`; mẫu 06 với `qwen3:14b`); review runbook trước khi viết xong (mẫu 05, `qwen3:14b`); tập dượt trình bày không phụ thuộc slide (mẫu 09, `qwen3:14b`).
5. **`qwen3:14b` ước lượng thừa và vượt quỹ quý (C6: 4/6).** Mẫu 02: 155 h so với quỹ 118,8 h; mẫu 06: 238 h so với 237,6 h, và thí nghiệm giá thứ hai chỉ bắt đầu sau khi thí nghiệm đầu chạy hết quý.
6. **Hỏi thừa mới (`qwen3:14b`, mẫu 03).** Prompt clarify "duyệt từng KR" làm model 14B hỏi về chi tiết thực thi của một KR đã rõ.
7. **Độ trễ.** Mỗi plan rõ ràng mất 5–11 phút trên máy 32GB, vì số task tăng 1,7–1,9 lần, nhiều lần retry decompose hơn (`qwen3:8b`) và bước dedup/quan hệ KR dài hơn. Máy 16GB sẽ chậm hơn nữa.

### 5b.5 Việc cần CTO quyết định

Tỉ lệ đạt vẫn < 80% và lỗi chính (C1, C2) giống nhau ở cả hai model, nên đổi model local không giải quyết được. Có ba hướng, không loại trừ nhau:

1. **Hiệu chỉnh bộ mẫu cùng Bên A.** Ban đầu đề xuất lấy mốc OpenAI trước để biết `must_cover` của bộ mẫu tạm có quá chặt hay không, nhưng board đã quyết định không chạy OpenAI (mục 6), nên eval này không tách được hai khả năng đó. Hướng còn lại là rà `must_cover` trực tiếp với Bên A, ví dụ chuyển các mục như "billing alert", "in-app rating prompt ở thời điểm tích cực" sang `grader_notes` dạng điểm cộng, và cho C1 chấp nhận thiếu 1 mục mỗi KR.
2. **Vòng tối ưu prompt tiếp (Backend):** cấm task "phần 1/phần 2" và `done_criteria` lặp tiêu đề (thêm vào luật validate để retry); đặt trần tổng giờ theo khoảng ước lượng của KR để chặn ước lượng thừa; nhắc model không hỏi về chi tiết thực thi của KR đã có sản phẩm cụ thể. Nên đổi kèm một mục tiêu độ trễ cho Local, vì độ trễ hiện tại đã gấp 3,5 lần lần 1.
3. **Hạ ngưỡng nghiệm thu cho Local** (ví dụ chỉ yêu cầu 80% với OpenAI, Local là chế độ "bản nháp"). Hướng này cần board đồng ý vì đổi tiêu chí nghiệm thu.

## 5c. Sau tối ưu vòng 3 (eval lần 3)

CTO chọn hướng 2 ở 5b.5 và thêm mục tiêu độ trễ. Backend đã thay đổi:

- **Luật chất lượng task** (retry khi vi phạm): tiêu đề đánh số theo phần ("part 1", "phần 2", "(1/2)"); nhóm task cùng KR chỉ khác số cuối; `done_criteria` chỉ lặp tiêu đề hoặc chung chung ("đã được tối ưu", "finalized").
- **Trần giờ mỗi KR** ghi vào prompt và được kiểm tra; nếu tổng cả kế hoạch vẫn vượt quỹ quý thì hạ trần các KR vượt mức và decompose lại các KR đó một lần.
- Luật chất lượng và luật ngân sách là **luật mềm**: hết retry thì giữ kế hoạch cuối cùng hợp lệ về cấu trúc, không fail cả kế hoạch. Luật cấu trúc (graph, 2–6 h, `kr_id`) vẫn là luật cứng.
- Clarify không hỏi về cách làm; KR đã đủ metric, baseline và target thì bỏ qua bước LLM kiểm tra độ rõ.
- Dedup gửi payload gọn hơn, giới hạn 5 merge và 8 phụ thuộc chéo, `num_predict` dedup 2048 → 1024; **bỏ qua merge và phụ thuộc giữa hai task của cùng một KR**.
- `run_eval.py` lấy số ngày làm việc từ lịch của app: 65 ngày, nên quỹ dùng được là 234 h (4 h/ngày) và 117 h (2 h/ngày). Lần 1 và lần 2 dùng 66 ngày (237,6 h và 118,8 h).

Lần 3 chạy đúng lệnh `run --force` cho hai model, cùng máy và cùng thiết lập với lần 2. Thời gian thực tế: khoảng 48 phút cho `qwen3:8b` và 112 phút cho `qwen3:14b`. Máy dev bị tải rất nặng suốt lần chạy do có máy ảo, iOS simulator và các app khác chạy cùng (load average 70–170 khi chạy `qwen3:8b`, 380–590 khi chạy `qwen3:14b`). Số đo độ trễ ở dưới vì vậy cao hơn số đo trên máy rảnh, nhất là với `qwen3:14b`.

### 5c.1 Tổng hợp ba lần

| Model | Lần | Tỉ lệ đạt rubric | Hỏi lại đúng (3 mẫu mơ hồ) | Không hỏi thừa (7 mẫu rõ) | JSON hợp lệ lần đầu | JSON hợp lệ sau retry | Retry | Lần gọi LLM | Task TB/plan rõ | Trung vị tất cả / 7 mẫu rõ / max |
|---|---|---|---|---|---|---|---|---|---|---|
| `qwen3:8b` | 1 | 1/10 (10%) | 3/3 | 7/7 | 98,2% | 100% | 1 | 57 | 21,4 | 103 / 154 / 241 s |
| `qwen3:8b` | 2 | 3/10 (30%) | 3/3 | 7/7 | 83,7% | 100% | 15 | 92 | 37,4 | 364 / 380 / 476 s |
| `qwen3:8b` | 3 | **3/10 (30%)** | 3/3 | 7/7 | 72,5% | **100%** | 25 | 69 | 37,7 | **358 / 379 / 532 s** |
| `qwen3:14b` | 1 | 3/10 (30%) | 3/3 | 7/7 | 96,5% | 100% | 2 | 57 | 25,3 | 303 / 359 / 466 s |
| `qwen3:14b` | 2 | 3/10 (30%) | 3/3 | 6/7 | 100% | 100% | 0 | 84 | 47,0 | 420 / 488 / 658 s |
| `qwen3:14b` | 3 | **3/10 (30%)** | 3/3 | **7/7** | 80,9% | **100%** | 18 | 68 | 43,1 | **768 / 847 / 1462 s** |

- Không lỗi pipeline, không timeout ở cả hai model. Số lần gọi LLM giảm (92 → 69 và 84 → 68) nhờ bỏ bước kiểm tra độ rõ với KR đã đo được.
- Lý do bị từ chối của `qwen3:8b` (57 lần): 25 task ngoài khoảng 2–6 h (23 lần > 6 h), 18 `done_criteria` không kiểm chứng được, 7 tiêu đề "part/phần", 5 nhóm task chỉ khác số cuối, 1 KR vượt trần giờ, 1 dedup gộp hai bước nối tiếp. Luật cũ "task > 6 h" vẫn là lý do retry nhiều nhất.
- Lý do bị từ chối của `qwen3:14b` (25 lần): 11 `done_criteria` không kiểm chứng được, 7 KR vượt trần giờ, 4 dedup tạo chu trình phụ thuộc chéo, 1 quá nhiều task, 1 nhóm task chỉ khác số cuối, 1 output bị cắt ở giới hạn token.
- Luật mềm hết retry nên giữ kế hoạch còn lỗi: `qwen3:8b` ở 2 KR (mẫu 03 O1-KR2 còn `done_criteria` chung chung; mẫu 05 O2-KR2 còn 5 task chỉ khác số cuối); `qwen3:14b` ở 3 lần decompose (mẫu 01 O1-KR1 `done_criteria`; mẫu 02 O1-KR1 vượt trần giờ cả lần đầu lẫn lần replan).
- Thời gian trung bình theo bước lần 3 (s): `qwen3:8b` clarify 3,9 / decompose 364 / dedup 38; `qwen3:14b` 9,2 / 865 / 83.

### 5c.2 Theo tiêu chí rubric ba lần (điểm đã đối chiếu)

| Model | Lần | Q1 | Q2 | Q3 | C1 | C2 | C3 | C4 | C5 | C6 | Đạt vi / en |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `qwen3:8b` | 1 | 3/3 | 1/3 | 3/3 | 0/7 | 3/7 | 0/7 | 1/7 | 0/7 | 7/7 | 0/5 / 1/5 |
| `qwen3:8b` | 2 | 3/3 | 3/3 | 3/3 | 1/7 | 1/7 | 1/7 | 3/7 | 2/7 | 7/7 | 1/5 / 2/5 |
| `qwen3:8b` | 3 | 3/3 | 3/3 | 3/3 | **0/7** | **6/7** | 2/7 | 3/7 | **0/7** | 7/7 | 1/5 / 2/5 |
| `qwen3:14b` | 1 | 3/3 | 3/3 | 3/3 | 0/7 | 6/7 | 1/7 | 0/7 | 2/7 | 7/7 | 1/5 / 2/5 |
| `qwen3:14b` | 2 | 3/3 | 3/3 | 3/3 | 0/6 | 1/6 | 2/6 | 2/6 | 1/6 | 4/6 | 1/5 / 2/5 |
| `qwen3:14b` | 3 | 3/3 | 3/3 | 3/3 | **0/7** | **7/7** | 3/7 | **5/7** | **4/7** | 6/7 | 1/5 / 2/5 |

- Kế hoạch gần đạt nhất: mẫu 03 và 05 của `qwen3:14b` **chỉ trượt C1**. Mọi kế hoạch rõ của `qwen3:8b` trượt ít nhất 3 tiêu chí.
- Bỏ hẳn C1 (giả định cực đoan), tỉ lệ đạt chỉ thành `qwen3:8b` 3/10 và `qwen3:14b` 5/10. Cho C1 chấp nhận thiếu 1 mục `must_cover` mỗi KR (đề xuất ở 5b.5) cũng không cứu thêm kế hoạch nào, vì cả hai mẫu gần đạt của `qwen3:14b` đều có KR thiếu từ 2 mục trở lên.

### 5c.3 Tổng giờ so với khoảng kỳ vọng (mẫu rõ ràng)

| Mẫu | Kỳ vọng (h) | `qwen3:8b` lần 1 → 2 → 3 | `qwen3:14b` lần 1 → 2 → 3 |
|---|---|---|---|
| 01 SaaS onboarding | 108–194 | 82 ↓ → 139 → 131 | 94 ↓ → 172 → 158 |
| 02 AWS cert | 56–106 | 56 → 110 ↑ → 86 | 68 → 155 ↑ → **129 ↑ (vượt quỹ 117)** |
| 03 Health | 66–110 | 56 ↓ → 97 → 63 ↓ | 76 → hỏi thừa → 106 |
| 04 B2B sales | 106–188 | 96 ↓ → 152 → 164 | 116 → 192 ↑ → 163 |
| 05 Payment reliability | 128–220 | 92 ↓ → 151 → 148 | 96 ↓ → 162 → 204 |
| 06 Mobile launch | 110–200 | 100 ↓ → 181 → 185 | 122 → 238 ↑ → 221 ↑ |
| 09 Master thesis | 120–202 | 90 ↓ → 165 → 137 | 102 ↓ → 206 ↑ → 170 |

Tổng giờ trong khoảng ở lần 3: `qwen3:8b` 6/7 (mẫu 03 thấp hơn mức tối thiểu 3 h), `qwen3:14b` 5/7. Trần giờ mỗi KR kéo `qwen3:14b` về gần khoảng (lần 2 là 2/6), nhưng chưa chặn hết: mẫu 02 vượt quỹ quý, mẫu 06 vượt trần khoảng kỳ vọng dù vẫn trong quỹ 234 h.

### 5c.4 Lỗi điển hình còn lại

Tỉ lệ đạt vẫn < 80%. Lỗi được tách làm hai nhóm: lỗi do model hoặc prompt (sửa được trong pipeline), và lỗi nghi do `must_cover` của bộ mẫu tạm quá chặt.

**A. Lỗi do model hoặc prompt**

1. **Trùng việc (C5: `qwen3:8b` 0/7, `qwen3:14b` 4/7).** Có hai dạng:
   - Task "đo/xác nhận kết quả cuối" ghi lại đúng kết quả mà `done_criteria` của task ngay trước đã ghi. Ví dụ "Practice exam session 3 … confirmed that target score is reached" rồi "Measure final practice exam score" (mẫu 02, `qwen3:8b`); số hợp đồng cuối kỳ ghi hai lần (mẫu 04, `qwen3:8b`); macro-F1 ≥ 0,75 ghi hai lần (mẫu 09, `qwen3:8b`); deal size hiện tại đo hai lần (mẫu 04, `qwen3:14b`). Dạng này nhiều khả năng đến từ checklist "đo cuối kỳ" trong prompt decompose. Vòng 3 lại cho dedup bỏ qua mọi merge giữa hai task cùng KR, nên dedup không còn gộp được các cặp này.
   - Trùng giữa các KR: chỉnh sửa hướng dẫn in-app ở cả O1-KR1 và O1-KR3 (mẫu 01, `qwen3:8b`); kế hoạch ôn thi và lịch học là hai task (mẫu 02, `qwen3:8b`); học nội dung đề thi hai lần ở O1-KR1 và O1-KR3 (mẫu 02, `qwen3:14b`); thí nghiệm giá dựng hai lần (mẫu 06, `qwen3:8b`); bộ slide seminar làm hai lần (mẫu 09, `qwen3:8b`).
2. **Ước lượng thiếu ở từng task (C3: `qwen3:8b` 2/7, `qwen3:14b` 3/7).** Tổng giờ thường nằm trong khoảng, nhưng việc lớn bị nén vào một task 2–6 h: tự code hệ thống referral có dashboard và thưởng trong 5 h, smart reminder theo hành vi kèm test trong 6 h (mẫu 06, `qwen3:8b`); fine-tune BERT trong 2 h, viết trọn chương tổng quan trong 6 h (mẫu 09, `qwen3:8b`); soạn 15 proposal trong 4 h (mẫu 04, `qwen3:8b`); soạn 8 proposal trong 5 h, đàm phán và ký 8 hợp đồng trong 6 h (mẫu 04, `qwen3:14b`). Giả thuyết: luật mới cấm chia "part 1/2" và cấm task chỉ khác số cuối, nên khi việc lớn hơn 6 h, model nén vào một task thay vì chia theo sản phẩm trung gian (thiết kế, backend, giao diện, kiểm thử).
3. **Phụ thuộc (C4: `qwen3:8b` 3/7, `qwen3:14b` 5/7).** Lab không đứng trước bài thi thử cuối (mẫu 02, cả hai model); thí nghiệm giá không phụ thuộc tracking chuyển đổi (mẫu 06, `qwen3:8b`); đo baseline sau cải tiến (mẫu 04 `qwen3:8b`, mẫu 02 `qwen3:14b`); phụ thuộc vô lý giữa các KR (mẫu 01 và 06, `qwen3:8b`).
4. **Thiếu việc mà KR nêu rõ (tính vào C1, nhưng là lỗi của model).** Thiếu số lượng: các task phỏng vấn chỉ phủ 12 trong 15 khách (mẫu 01, cả hai model); 6 và 12 buổi tập sức mạnh thay vì ≥ 20, và `qwen3:8b` không có buổi chạy tập nào (mẫu 03). Thiếu bước kết thúc: không có task nộp bài hội thảo (mẫu 09, `qwen3:14b`), không sửa theo góp ý giảng viên (mẫu 09, cả hai model). KR số đo không có task theo dõi chỉ số (O1-KR1 mẫu 01, `qwen3:8b`).
5. **Vượt quỹ quý mà không cảnh báo (C6, `qwen3:14b` mẫu 02).** O1-KR1 vượt trần giờ ở cả lần decompose đầu và lần replan. Vì luật ngân sách là luật mềm, pipeline giữ kế hoạch 129 h trong khi quỹ dùng được là 117 h, và trường `issues` của kết quả rỗng. Đây là lỗ hổng của pipeline, không chỉ của model: khi replan vẫn vượt quỹ, nên cắt bớt task theo ưu tiên KR hoặc trả cảnh báo cho người dùng.
6. **Retry decompose tăng (`qwen3:8b` 15 → 25)**, kéo dài thời gian decompose. Xem 5c.5.

**B. Lỗi nghi do `must_cover` quá chặt hoặc quá cụ thể**

Các mục dưới đây bị **cả hai model bỏ ở lần 3**; phần lớn cũng đã bị bỏ ở lần 1 và lần 2 (5b.4, điểm 1). Chúng là chi tiết thực hành tốt theo lĩnh vực, không nằm trong câu chữ của KR:

| Mẫu | Mục `must_cover` cả hai model cùng bỏ ở lần 3 | Ghi chú |
|---|---|---|
| 01 SaaS | Kịch bản phỏng vấn; dashboard theo dõi activation | Dashboard activation bị bỏ cả ba lần |
| 02 AWS | Billing alert và dọn tài nguyên sau mỗi lab | Bị mọi model bỏ ở cả ba lần; là mục `must_cover` duy nhất `qwen3:8b` trượt ở mẫu này |
| 03 Health | Danh sách đi chợ; ghi khẩu phần ăn ban đầu | |
| 04 B2B | Template proposal và bảng giá chuẩn; gói upsell theo tầng; dọn dữ liệu CRM cũ; theo dõi lead hằng tuần | Template proposal và dọn CRM bị bỏ cả ba lần |
| 05 Payment | Dashboard uptime; health check và failover; alerting có ngưỡng và quy trình trực; ngưỡng coverage trong CI | `qwen3:14b` còn bỏ SLO/SLI và game day (lần 2 cả hai cùng bỏ) |
| 06 Mobile | Trả lời review tiêu cực | Prompt đánh giá in-app lần 3 chỉ `qwen3:8b` bỏ; lần 2 cả hai cùng bỏ |
| 09 Luận văn | Chọn hội thảo và mẫu định dạng; phân tích lỗi | |

Board đã quyết định không chạy OpenAI (mục 6), nên không có mốc của model flagship để xác nhận các mục này có quá chặt hay không. Đây chỉ là nghi vấn, dựa trên việc mọi model ở mọi lần đều bỏ. Như 5c.2 đã chỉ ra, kể cả hiệu chỉnh hết các mục này thì tỉ lệ đạt cũng chỉ tối đa 5/10. Lỗi ở nhóm A vẫn phải sửa.

### 5c.5 Mục tiêu độ trễ (`qwen3:8b`)

| Chỉ số | Mục tiêu | Lần 2 | Lần 3 |
|---|---|---|---|
| Trung vị 7 mẫu rõ | ≤ 240 s | 380 s | **379 s** (không đạt) |
| Max 7 mẫu rõ | ≤ 360 s | 476 s | **532 s** (không đạt) |
| Clarify TB | | 7,8 s | 3,9 s |
| Decompose TB | | 282 s | 364 s |
| Dedup TB | | 101 s | 38 s |

- Sửa dedup và clarify có hiệu quả: dedup nhanh hơn 2,6 lần, clarify nhanh hơn 2 lần, và số lần gọi LLM giảm 25%. Các mức giảm này đến từ việc giảm token và giảm số lần gọi, nên không phụ thuộc tải máy.
- Phần nghẽn là decompose. Retry tăng từ 15 lên 25, chủ yếu do luật cũ "task > 6 h" (23 lần) và luật mới `done_criteria` (18 lần), mỗi retry là một lần sinh lại cả danh sách task của KR.
- Máy tải nặng (load average 70–170) nên chưa kết luận được SLO. Lần 2 không ghi lại tải máy nên không so trực tiếp được. Cần đo lại trên máy rảnh (tắt máy ảo và simulator) trước khi nghiệm thu mục tiêu độ trễ.

### 5c.6 Việc cần CTO quyết định

1. **Tối ưu tiếp (Backend), theo nhóm A ở 5c.4:** không sinh task "đo cuối" lặp lại kết quả đã có, hoặc cho dedup gộp trùng trong cùng KR khi hai task ra cùng sản phẩm; hướng dẫn chia việc lớn theo sản phẩm trung gian thay vì nén vào một task; xử lý trường hợp replan vẫn vượt quỹ quý (cắt theo ưu tiên hoặc cảnh báo); giảm retry decompose (task > 6 h vẫn là lý do retry số 1).
2. **Hiệu chỉnh `must_cover` cùng Bên A** cho các mục ở bảng 5c.4 B. Việc này cần thiết nhưng không đủ để đạt 80% (tối đa 5/10 với dữ liệu lần 3).
3. **Định vị Local là chế độ "bản nháp"** hoặc hạ ngưỡng cho Local. Cần board duyệt vì đổi tiêu chí nghiệm thu, và hiện không có mốc OpenAI để đặt ngưỡng khác.
4. **Đo lại độ trễ trên máy rảnh** (có thể chỉ 7 mẫu rõ của `qwen3:8b`) để kết luận mục tiêu 240 s / 360 s.

## 6. OpenAI

**Không chạy, theo quyết định của board (2026-10-01).** Board không cấp `OPENAI_API_KEY` cho eval, nên phần OpenAI của eval này dừng tại đây:

- Không có số liệu nào cho `gpt-4o-mini` hay `gpt-4.1` (tỉ lệ đạt, JSON, thời gian). Báo cáo không suy đoán kết quả của OpenAI.
- Mọi kết luận trong báo cáo chỉ áp dụng cho Local. Tiêu chí ≤ 60 s mỗi kế hoạch của OpenAI chưa được kiểm chứng.
- Vì không có mốc OpenAI, báo cáo không tách được "model local yếu" với "`must_cover` của bộ mẫu quá chặt" (xem 5b.5). Lần 3 cũng không có mốc này, nên phần so sánh Local với OpenAI không áp dụng; danh sách `must_cover` nghi quá chặt ở 5c.4 (nhóm B) chỉ dựa trên việc mọi model local đều bỏ.

Nếu sau này board cấp key, việc chạy OpenAI sẽ làm ở một đợt eval riêng. Model đã được duyệt sẵn: `gpt-4o-mini` và flagship `gpt-4.1`. Script đã hỗ trợ sẵn; chạy từ `backend/`:

```bash
OPENAI_API_KEY=... python -m evals.run_eval run --provider openai --model gpt-4o-mini
OPENAI_API_KEY=... python -m evals.run_eval run --provider openai --model gpt-4.1
python -m evals.run_eval grading-pack && python -m evals.run_eval summarize
```

Bảng tổng hợp có cột `over_60s` để đối chiếu với tiêu chí ≤ 60 s.

## 7. Độ đồng thuận và giới hạn

- **Lần 3:** 20 kế hoạch × 2 grader, 102 ô tiêu chí được chấm: **đồng thuận 89,2%** (11 ô lệch), **thấp hơn mục tiêu 90% một chút**. Theo từng model: `qwen3:8b` 86,3% (7 ô lệch: C3 và C4 mẫu 01, C2 và C3 mẫu 02, C5 mẫu 04, C3 mẫu 06, C5 mẫu 09); `qwen3:14b` 92,2% (4 ô lệch: C4 mẫu 02, C3 và C5 mẫu 04, C5 mẫu 05). Kết luận đạt/không đạt trùng 20/20, và không ô nào làm đổi kết luận vì mọi kế hoạch rõ đều đã trượt C1. Các ô lệch dồn vào hai chỗ rubric còn mơ hồ: C3(c) ("lệch rõ rệt" khi ước lượng sát mức gấp đôi, hoặc khi việc có thể do người khác làm) và C5 (task "đo kết quả cuối" có tính là trùng với task trước đã ghi kết quả đó không). Khi đối chiếu, ô C5 được chốt theo một quy ước nhất quán cho cả hai model: tính trùng khi `done_criteria` của task trước đã chứa đúng kết quả mà task sau đo lại. Nên thêm hai quy ước này vào RUBRIC mục 5 trước lần chấm sau. Lý do chốt từng ô ghi trong cột `notes` của dòng `agreed`.
- **Lần 2:** 20 kế hoạch × 2 grader, 96 ô tiêu chí được chấm: **đồng thuận 91,7%** (8 ô lệch; mục tiêu ≥ 90%). Kết luận đạt/không đạt trùng 20/20. Ô lệch: `qwen3:8b` C5 mẫu 01, C4 và C5 mẫu 04, C3 mẫu 06, C2 mẫu 09; `qwen3:14b` C4 mẫu 05, C2 và C5 mẫu 09. Không ô nào làm đổi kết luận, vì các kế hoạch đó đều đã trượt C1. Lý do chốt từng ô ghi trong cột `notes` của dòng `agreed` (`backend/evals/results/scores.csv`). Đồng thuận thấp hơn lần 1 chủ yếu vì kế hoạch dài hơn (37–60 task), nên nhiều ca sát ngưỡng ở C2 (đếm task lỗi) và C5 (chồng lấn một phần).
- **Lần 1:** 40 kế hoạch × 2 grader, 156 ô tiêu chí được chấm: **đồng thuận 97,4%** (4 ô lệch, đều ở `qwen3:14b`: C2 mẫu 02 và 05, C4 mẫu 04 và 05). Kết luận đạt/không đạt trùng 40/40. Bốn ô lệch được đối chiếu theo nghĩa hẹp của rubric; lý do ghi trong cột `notes` của dòng `agreed`. Không ô nào làm đổi kết luận.
- **Grader là hai phiên agent AI** cùng họ model, chấm độc lập, không thấy tên model và không thấy phiếu của nhau. Vì cùng họ model, độ đồng thuận có thể cao hơn so với hai người chấm. Nên có một người chấm thật kiểm tra ngẫu nhiên vài dòng (ví dụ các mẫu 04, 05 của `qwen3:14b`) trước khi dùng số liệu này để nghiệm thu chính thức.
- Bộ mẫu là bộ tạm do team soạn; C1 đòi đủ mọi mục `must_cover` của mọi KR nên rất chặt.
- Mỗi cặp (mẫu, model) chỉ chạy một lần. Thời gian đo trên một máy dev với concurrency 1, chưa phản ánh máy 16GB.
- Lần 3 chạy khi máy dev bị tải rất nặng bởi các ứng dụng khác (load average 70–590). Số đo độ trễ lần 3, nhất là của `qwen3:14b`, cao hơn số đo trên máy rảnh và chỉ nên dùng để so tương đối giữa các bước. Các chỉ số không phụ thuộc thời gian (điểm rubric, JSON, retry, số lần gọi) không bị ảnh hưởng.
- So sánh giữa các lần dùng các cặp phiên grader khác nhau. Rubric giống nhau, nhưng chênh lệch 1–2 kế hoạch ở một tiêu chí có thể nằm trong sai số chấm. Ví dụ C5 của `qwen3:8b` (2/7 → 0/7) một phần do lần 3 chốt rõ quy ước "đo lại kết quả đã có là trùng".
- Lịch: lần 1 và lần 2 dùng 66 ngày làm việc (quỹ 237,6 h / 118,8 h); từ lần 3 `run_eval.py` lấy 65 ngày từ lịch của app (24/11 là ngày lễ), quỹ 234 h / 117 h, khớp `RUBRIC.md`. Chênh 1 ngày không làm đổi kết luận C6 nào.
- Chưa chạy các ứng viên tùy chọn trong ADR 0004 (`qwen2.5:7b`, `phi4:14b`, `gpt-oss:20b`). Máy dev chỉ còn khoảng 20GB đĩa trống nên mỗi model được pull → eval → gỡ; sau lần 2 và lần 3 đều đã gỡ lại `qwen3:14b`, chỉ giữ `qwen3:8b` (model mặc định của app).

## 8. Model mặc định (theo ADR 0004)

### 8.1 Xác nhận sau lần 3

Áp dụng thứ tự chọn model trong mục "Quyết định" của ADR 0004 (khi không model nào đạt tiêu chí 2): tỉ lệ đạt rubric → C6 → không hỏi thừa → độ trễ; hòa thì chọn model nhỏ hơn.

| Bước | `qwen3:8b` lần 3 | `qwen3:14b` lần 3 | Kết quả |
|---|---|---|---|
| Tiêu chí 1: JSON hợp lệ sau retry ≥ 98% | đạt (100%, 69/69 lần gọi) | đạt (100%, 68/68 lần gọi) | cả hai đủ điều kiện |
| Tiêu chí 2: rubric ≥ 80% | không (30%) | không (30%) | áp dụng thứ tự chọn |
| 1. Tỉ lệ đạt rubric | 3/10 | 3/10 | hòa |
| 2. C6 (không vượt quỹ quý) | **7/7** | 6/7 (mẫu 02: 129 h > 117 h) | **`qwen3:8b`** |
| 3. Không hỏi thừa | 7/7 | 7/7 | (không cần xét) |
| 4. Độ trễ, trung vị 7 mẫu rõ | 379 s | 847 s | (không cần xét) |

| Quyết định | Model | Lý do |
|---|---|---|
| Máy 16GB | **`qwen3:8b`** (giữ nguyên) | Model 7–9B duy nhất đạt tiêu chí 1; thắng theo thứ tự chọn của ADR 0004. |
| Máy ≥ 32GB | **`qwen3:8b`** (giữ nguyên; `qwen3:14b` là tùy chọn) | `qwen3:14b` không vượt `qwen3:8b` theo thứ tự của ADR 0004: hòa tỉ lệ đạt, thua ở C6. **Không đề xuất đổi mặc định cho máy ≥32GB.** |

Lưu ý:

- `qwen3:14b` tốt hơn rõ ở C2–C5 (C4 5/7 so với 3/7, C5 4/7 so với 0/7) và là model duy nhất có kế hoạch rõ chỉ trượt C1 (mẫu 03, 05). Lần C6 duy nhất nó trượt đến từ lỗ hổng luật ngân sách mềm của pipeline (5c.4 A5). Kể cả khi Backend sửa lỗ hổng đó và C6 hòa, thứ tự chọn vẫn dẫn tới độ trễ, nơi `qwen3:8b` nhanh hơn khoảng 2,2 lần. Vì vậy `qwen3:14b` chỉ thành mặc định cho máy ≥32GB khi nó **đạt nhiều kế hoạch hơn**, ví dụ sau khi hiệu chỉnh `must_cover` (5c.6 điểm 2). Khi đó nên chạy lại cả hai model.
- Đây vẫn là quyết định "model ít tệ nhất", **không phải nghiệm thu**: không model local nào đạt rubric 80% sau ba lần, và không có mốc OpenAI để so sánh (mục 6).

### 8.2 Chốt sau lần 2

| Tiêu chí ADR 0004 | `qwen3:8b` lần 2 | `qwen3:14b` lần 2 |
|---|---|---|
| 1. JSON hợp lệ sau retry ≥ 98% | **đạt** (100%, 92/92 lần gọi) | **đạt** (100%, 84/84 lần gọi) |
| 2. Rubric ≥ 80% | **không** (30%) | **không** (30%) |

| Quyết định | Model | Lý do |
|---|---|---|
| Máy 16GB | **`qwen3:8b`** | Đạt tiêu chí 1. Tiêu chí 2 không model nào đạt; đây là model 7–9B duy nhất còn lại sau khi loại `llama3.1:8b` ở lần 1 (JSON sau retry 86,3%). Ước lượng tổng giờ sát khoảng kỳ vọng nhất (6/7), không hỏi thừa, không kế hoạch nào vượt quỹ quý. |
| Máy ≥ 32GB | **`qwen3:8b`** (`qwen3:14b` là tùy chọn) | Tiêu chí 3 của ADR 0004 chỉ chuyển sang `qwen3:14b` khi không có model 7–9B nào đạt, với giả định model 14B tốt hơn. Lần 2 cho thấy điều ngược lại: cùng tỉ lệ đạt 3/10, nhưng `qwen3:14b` vượt quỹ giờ của quý ở 2/6 kế hoạch (C6 4/6 so với 7/7), hỏi thừa 1 mẫu rõ ràng, C4 thấp hơn (2/6 so với 3/7) và chậm hơn khoảng 1,3 lần trên mẫu rõ ràng (trung vị 488 s so với 380 s). Điểm mạnh duy nhất là JSON đúng ngay lần đầu 100% (0 retry), nhưng tiêu chí 1 tính sau retry nên điểm này không đổi kết quả. Một model mặc định cho mọi máy cũng giảm cấu hình phải hỗ trợ. |

Lưu ý khi dùng quyết định này:

- Đây là quyết định "model ít tệ nhất", **không phải nghiệm thu**: không model local nào đạt rubric 80%. Quyết định vòng tiếp (tối ưu tiếp, hiệu chỉnh bộ mẫu hay hạ ngưỡng cho Local) nằm ở 5b.5. Không có mốc OpenAI để so sánh (mục 6).
- Chọn `qwen3:8b` cho máy ≥32GB là lệch khỏi câu chữ tiêu chí 3 của ADR 0004 (nhánh dự phòng `qwen3:14b`). CTO cần xác nhận và cập nhật ADR 0004 từ "Đề xuất" sang "Chấp nhận" kèm lựa chọn này.
- Nếu vòng tối ưu sau chặn được ước lượng thừa (5b.5 điểm 2), nên chạy lại `qwen3:14b`: nó theo schema tốt nhất và có thể vượt `qwen3:8b` khi hết lỗi vượt quỹ giờ.
- Nếu cần giảm độ trễ Local, `qwen3:8b` vẫn là lựa chọn đúng; `qwen3:14b` chậm hơn ở mọi bước.

### 8.3 Đề xuất tạm sau lần 1 (giữ để so sánh)

| Tiêu chí ADR 0004 | `qwen3:8b` | `llama3.1:8b` | `gemma3:12b` | `qwen3:14b` |
|---|---|---|---|---|
| 1. JSON hợp lệ sau retry ≥ 98% | đạt (100%) | **không** (86,3%) | đạt (100%) | đạt (100%) |
| 2. Rubric ≥ 80% | không (10%) | không (10%) | không (30%) | không (30%) |

Không model nào đạt cả hai tiêu chí. Theo nhánh dự phòng của ADR 0004 ("không có model 7–9B nào đạt → `qwen3:14b`, yêu cầu máy ≥32GB"):

- **Tạm dùng `qwen3:14b` làm mặc định cho máy ≥32GB.** Cùng tỉ lệ đạt cao nhất với `gemma3:12b`, nhưng JSON lần đầu tốt hơn (96,5% so với 86,8%), không hỏi thừa, và nhanh hơn khoảng 1,5 lần (trung vị 303 s so với 455 s). `gemma3:12b` ước lượng giờ sát hơn (C3 2/6); đáng giữ làm phương án so sánh sau khi sửa prompt.
- **Giữ `qwen3:8b` cho máy 16GB** (cấu hình hiện tại). Nhanh nhất (103 s/mẫu) và JSON tốt; điểm thấp một phần do lỗi pipeline ở mục 5, điểm 1.
- **Loại `llama3.1:8b`**: lặp vô hạn ở dedup và JSON sau retry dưới 98%.
- **Chưa chốt** cho đến khi có mốc OpenAI và kết quả chạy lại sau khi Backend sửa mục 5. (Đã chốt ở 8.1 sau lần 2; mốc OpenAI không chạy theo quyết định board, xem mục 6.)
