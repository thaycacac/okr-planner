# ADR 0004 — Tập model local ứng viên để eval

- Trạng thái: Chấp nhận phần chọn model mặc định (2026-10-01). Chất lượng Local chưa đạt tiêu chí 2, xem mục "Quyết định"
- Ngày: 2026-09-30, cập nhật 2026-10-01

## Bối cảnh

Giả định phần cứng mặc định: Mac Apple Silicon ≥16GB. Máy dev hiện tại: 32GB RAM, Ollama đã cài. Pipeline cần model instruct theo được JSON Schema, xử lý tốt tiếng Việt và tiếng Anh, ước lượng giờ và phụ thuộc hợp lý. Tất cả tag dưới đây đã kiểm tra tồn tại trên Ollama library ngày 2026-09-30.

## Tập ứng viên

| Tầng | Model (tag Ollama) | RAM tham khảo (Q4) | Lý do đưa vào |
|---|---|---|---|
| 7–9B (máy 16GB) | `qwen3:8b` | ~5–6 GB | Ứng viên mặc định: đa ngôn ngữ tốt (có tiếng Việt), theo schema tốt. Tắt chế độ thinking khi gọi để giảm độ trễ |
| 7–9B | `llama3.1:8b` | ~5 GB | Baseline phổ biến, so sánh chất lượng tiếng Anh |
| 7–9B | `qwen2.5:7b` | ~5 GB | Thế hệ trước của Qwen, ổn định với structured output |
| 12–14B (máy ≥32GB) | `qwen3:14b` | ~9–10 GB | Ứng viên chất lượng cao cho máy 32GB |
| 12–14B | `gemma3:12b` | ~8–9 GB | Đa ngôn ngữ, so sánh chéo họ model |
| 12–14B | `phi4:14b` | ~9 GB | Suy luận tốt, kiểm tra chất lượng tiếng Việt |
| Tham khảo trên (tùy chọn) | `gpt-oss:20b` | ~13–14 GB | Chỉ chạy nếu còn thời gian; kiểm tra trần chất lượng local trên máy 32GB |

`qwen2.5:3b` (đang có trên máy dev) chỉ dùng cho smoke test kết nối, không phải ứng viên chất lượng.

## Cách eval (phase 1 chạy sớm, phase 3 báo cáo chính thức)

- Bộ 10 OKR mẫu tạm (team tự soạn; thay bằng bộ Bên A khi có), trộn vi/en, có 2 OKR cố ý mơ hồ.
- Mỗi model × mỗi OKR, `temperature=0`, ghi: tỉ lệ JSON hợp lệ lần đầu, số retry, tỉ lệ hỏi lại đúng với OKR mơ hồ, thời gian từng bước và tổng, điểm rubric "hợp lý và khả thi" (0/1 theo từng kế hoạch).
- Chạy cùng bộ với OpenAI (`gpt-4o-mini` và một model flagship) để có đường cơ sở.

## Tiêu chí chọn model mặc định

1. Tỉ lệ JSON hợp lệ sau retry ≥ 98%.
2. Điểm rubric ≥ 80% (tiêu chí nghiệm thu).
3. Trong các model đạt 1 và 2, chọn model nhỏ nhất chạy được trên máy 16GB; nếu không có model 7–9B nào đạt, mặc định là `qwen3:14b` và ghi rõ yêu cầu máy ≥32GB.

## Quyết định (sau eval lần 2, `docs/eval-report.md` mục 5b và 8)

- **Model mặc định: `qwen3:8b` cho mọi máy (16GB và ≥32GB).** `qwen3:14b` là tùy chọn trong màn Cài đặt LLM, không phải mặc định.
- Kết quả lần 2: cả hai model đạt tiêu chí 1 (JSON sau retry 100%), cả hai trượt tiêu chí 2 (rubric 3/10).
- **Sửa tiêu chí 3:** nhánh dự phòng `qwen3:14b` giả định model 14B tốt hơn. Dữ liệu lần 2 bác bỏ giả định này: cùng 3/10, nhưng `qwen3:14b` vượt quỹ giờ của quý ở 2/6 kế hoạch, hỏi thừa 1 mẫu rõ ràng và chậm hơn khoảng 1,3 lần. Từ nay, khi không model nào đạt tiêu chí 2, chọn model đạt tiêu chí 1 có kết quả tốt nhất theo thứ tự: tỉ lệ đạt rubric, C6 (không vượt quỹ quý), không hỏi thừa, độ trễ. Hòa thì chọn model nhỏ hơn.
- Đây là quyết định đảo ngược được: đổi model mặc định chỉ là đổi giá trị cấu hình, không cần migration dữ liệu.
- **Chưa nghiệm thu chất lượng Local.** Tiêu chí 2 (≥ 80%) giữ nguyên cho đến khi có mốc OpenAI. Nếu model OpenAI flagship cũng trượt C1 hàng loạt, hiệu chỉnh `must_cover` của bộ mẫu trước; mọi đề xuất hạ ngưỡng cho Local phải được board duyệt vì đổi tiêu chí nghiệm thu.
- Chạy lại `qwen3:14b` sau vòng tối ưu chặn ước lượng thừa; nếu nó vượt `qwen3:8b` theo thứ tự ở trên thì đề xuất nó làm mặc định cho máy ≥32GB.
