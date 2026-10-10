# ADR 0003 — Scheduler deterministic (list scheduling) và feasibility

- Trạng thái: Chấp nhận
- Ngày: 2026-09-30

## Bối cảnh

Tiêu chí nghiệm thu yêu cầu: không xếp task vào T7/CN/lễ khi tắt; không vượt cuối quý; không vi phạm phụ thuộc; tổng giờ mỗi ngày không vượt capacity (kể cả nhiều OKR, task trải nhiều ngày); cùng đầu vào thì cùng kết quả; khi quá tải phải cảnh báo và đề xuất phương án thay vì nhồi task.

## Quyết định

### Đầu vào / đầu ra thuần

```python
def schedule(inp: ScheduleInput) -> ScheduleResult: ...
```

- `ScheduleInput`: quý/năm, `today`, `CalendarConfig` (capacity theo thứ, bật T7/CN/lễ, danh sách lễ, nghỉ phép, ngày làm bù), danh sách task chưa xong của mọi OKR active trong quý (id, giờ, phụ thuộc, `objective_priority`, `kr_order`, `task_order`), task ghim.
- `ScheduleResult`: với mỗi task `start_date`, `end_date`, `allocations: [(date, hours)]`; danh sách task không xếp được; cảnh báo (xanh/vàng/đỏ); chỉ số D (demand), S (supply), ngày cắt buffer.
- Hàm **thuần**: không đọc đồng hồ hệ thống (nhận `today`), không đọc DB, không random. Giờ biểu diễn bằng số nguyên **phút** (hoặc `Decimal`) để tránh sai số float khi so sánh capacity.

### Thuật toán

1. Khoảng lịch: `max(ngày đầu quý, today) → ngày cuối quý`; tính các ngày hợp lệ theo `calendar/`.
2. Buffer mềm 10%: tìm ngày cắt sao cho capacity từ ngày cắt đến cuối quý ≈ 10% S. Task xếp trước ngày cắt; nếu không đủ thì được dùng buffer và gắn cảnh báo **vàng**; vượt cuối quý thì **đỏ** và không xếp.
3. Cấp phát task ghim trước, trừ capacity; xung đột thì cảnh báo, không tự dời.
4. Topo sort theo phụ thuộc, tie-break ổn định `(objective_priority, kr_order, task_order, task_id)`; phát hiện chu trình thì từ chối đầu vào.
5. List scheduling: lấy task sẵn sàng có khóa ưu tiên nhỏ nhất, bắt đầu từ ngày sớm nhất **sau** ngày kết thúc của các task phụ thuộc (phụ thuộc xong trong ngày D thì task sau bắt đầu từ D+1, trừ khi board đổi giả định); mỗi ngày lấy `min(capacity còn lại, giờ còn lại)`, trải tiếp các ngày hợp lệ kế tiếp. Task trải nhiều ngày được dùng chung ngày với task khác.
6. Ưu tiên Objective nghiêm ngặt (giả định mặc định). Task quá hạn chưa xong được dời về từ `today`.

### Feasibility và what-if

Mỗi phương án là **một lần chạy lại `schedule()`** với cấu hình sửa đổi, nên số liệu là thật: tăng giờ/ngày (tìm giá trị nhỏ nhất đủ bằng tìm kiếm nhị phân), bật T7/CN/lễ, bỏ KR ưu tiên thấp nhất, dời KR sang quý sau. Gợi ý cắt/gộp task là bước LLM riêng, người dùng duyệt.

### Kiểm thử

Property tests (hypothesis) là **bắt buộc** cho module này, sinh ngẫu nhiên lịch, capacity, đồ thị phụ thuộc (DAG), task ghim; kiểm các bất biến:

- Không có allocation vào ngày không hợp lệ (T7/CN/lễ/nghỉ phép khi tắt).
- Không có allocation sau ngày cuối quý.
- Với mọi cạnh `a → b`: `end(a) < start(b)`.
- Tổng giờ mỗi ngày ≤ capacity ngày đó.
- Tổng giờ allocation của task = `estimate` (nếu được xếp).
- Chạy hai lần với cùng đầu vào (kể cả đảo thứ tự danh sách task đầu vào) → kết quả giống hệt.
- Task ghim giữ nguyên vị trí.

## Phương án đã cân nhắc

| Phương án | Lý do không chọn |
|---|---|
| CP-SAT / MILP | Tối ưu hơn nhưng khó giải thích, chậm hơn khi what-if chạy nhiều lần, tie-break khó ổn định. Module độc lập nên có thể thay sau |
| LLM đề xuất ngày | Không deterministic, không đảm bảo bất biến |

## Hệ quả

- Xếp lại lịch không tốn LLM, chạy mili-giây, what-if chạy được nhiều lần mỗi request.
- List scheduling không tối ưu toàn cục (có thể để trống giờ lẻ); chấp nhận vì dễ đoán và dễ giải thích cho người dùng.
