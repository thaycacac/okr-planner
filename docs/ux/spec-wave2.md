# Spec UX đợt 2 — hoàn thiện giai đoạn 1

Wireframe: [`wireframes/wave2.html`](wireframes/wave2.html) (nút VI/EN góc phải). Ảnh PNG: [`png/vi/`](png/vi/), [`png/en/`](png/en/), tên file `wave2-<mã màn>.png`. Quy ước giống [`spec-wave1.md`](spec-wave1.md): **[C]** = component shadcn/ui hoặc thư viện đã chốt; số hồng trong wireframe khớp mục "Ghi chú".

## Dữ liệu mẫu đợt 2 (giả lập, dùng làm fixture)

"Hôm nay" trong wireframe: **T4 07/10/2026** (tuần 41).

| Màn | Kịch bản | Số liệu |
|---|---|---|
| S10, S11, S12 | Xanh | Cần 212h / Có 260h (82%), xong 15/12, 50 task (KR 1.1: 9 · KR 1.2: 6 · KR 1.3: 7 · KR 2.1: 5 · KR 2.2: 23), 4 task đã xong (16h) |
| S13 | Đỏ, lúc lập kế hoạch 30/09 | Cần 318h / Có 260h, thiếu 58h, 15 task không kịp (KR 3.1: 7 task/28h · KR 3.2: 8 task/30h). O3 = 106h (KR 3.1: 19 task/76h · KR 3.2: 8 task/30h) |
| S14 | Sau khi áp dụng "Làm Thứ 7 + Dời KR 3.2" | Cần 288h / Có 312h, Vàng, dùng 8h/32h buffer, xong 24/12, 69 task |

Capacity theo tuần Q4/2026 (T2–T6, 4h/ngày, lễ 24/11): T40 8h · T41–T47 20h · T48 16h · T49–T52 20h · T53 16h = **260h / 65 ngày**. Buffer làm tròn lên theo ngày (xem D5): 28h từ 23/12; khi bật Thứ 7: 312h, buffer 8 ngày = 32h từ 23/12.

Số liệu phương án S13 (mỗi dòng = một lần chạy `schedule()` với tham số khác):

| Phương án | Thay đổi | Kết quả khi dùng một mình |
|---|---|---|
| 5h/ngày T2–T6 | +65h (S = 325h, buffer 35h) | Vàng, dùng 28h/35h buffer; 5,5h/ngày → Xanh |
| Làm Thứ 7 | +52h (13 ngày) | Đỏ, thiếu 6h (2 task) |
| Làm Chủ nhật | +52h | Đỏ, thiếu 6h; cùng Thứ 7 = +104h → Xanh |
| Làm ngày lễ 24/11 | +4h | Đỏ, thiếu 54h |
| Bỏ KR 3.2 | −30h | Đỏ, thiếu 28h |
| Bỏ O3 | −106h | Xanh, xong 15/12 |
| AI thu gọn O3 | −30h (5 đề xuất) | Đỏ, thiếu 28h |
| Dời KR 3.2 → Q1/2027 | −30h | Đỏ, thiếu 28h |
| Dời KR 3.1 → Q1/2027 | −76h | Vàng, dùng 10h buffer |
| **Làm Thứ 7 + Dời KR 3.2** | 288h / 312h | **Vàng, dùng 8h/32h buffer, xong 24/12, 0 task trễ** |

---

## Mẫu hành vi chung đợt 2

- **Kế hoạch lỗi thời**: mọi thay đổi ảnh hưởng lịch (sửa/thêm/xóa/dời/ghim task, nghỉ phép, ngày lễ) chỉ ghi nhận thay đổi. Topbar đổi pill khả thi thành "⟳ Cần xếp lại" (viền đứt, không hiện số cũ), trang hiện badge "N thay đổi chưa xếp lại" + `Hoàn tác tất cả` + `Xếp lại lịch`.
- **Xếp lại** = gọi scheduler ở chế độ xem trước (dry-run), trả về: xung đột ghim, danh sách task đổi ngày, trạng thái khả thi mới. Chỉ ghi vào DB khi người dùng bấm `Áp dụng lịch mới`.
- **Hoàn tác**: mọi thao tác áp dụng có [C] `sonner` toast 8 giây "Hoàn tác" (dừng đếm khi hover/focus). Thao tác không hoàn tác được (xóa quý, xóa toàn bộ) dùng `AlertDialog` xác nhận mạnh.
- **Task ghim**: scheduler không bao giờ dời. Xung đột (ngày ghim vượt capacity, ghim trước khi phụ thuộc xong theo quy tắc D+1, ngày ghim thành ngày nghỉ) luôn hỏi người dùng.
- **Task đã xong**: không bị dời; tiến độ tính từ hôm nay cho task chưa xong.

**Yêu cầu API cho Backend** (UX cần, CTO chốt hình dạng): `POST /schedule/preview` (nhận danh sách thay đổi, trả `conflicts[]`, `changes[]` gồm task/ngày cũ/ngày mới, `feasibility`), `POST /schedule/apply`, `POST /options/evaluate` (nhận tổ hợp phương án, trả trước/sau), `GET /options` (kết quả từng phương án một mình). Thời gian mục tiêu < 2 giây cho preview.

---

## S10 — Sửa, thêm, xóa, dời, ghim task & xếp lại lịch · `/q/{year}-Q{n}/tasks`

**Mục đích**: chỉnh kế hoạch mà không tốn AI, không mất kiểm soát ngày.

- Bảng cây S5 thêm: cột checkbox hoàn thành (đầu hàng), cột Trạng thái (badge `✓ Xong`, `Hôm nay`, `Đã sửa: 4h → 6h`, `Ghim · 09/10`, `Mới`), cột `⋯`.
- [C] `DropdownMenu` hàng: Sửa… (E) · Dời sang ngày… (mở [C] `Calendar` trong `Popover`, dời + ghim) · Ghim vào ngày hiện tại / Bỏ ghim · Đánh dấu hoàn thành (X) · Nhân bản · — · Xóa task (⌫, màu đỏ).
- `+ Thêm task` ở toolbar và cuối mỗi KR ("+ Thêm task vào KR 1.1"); task mới mở cùng Sheet sửa.
- [C] `Sheet` sửa (phải, 460px): Tên · Ước lượng (stepper 2–6h, gợi ý tách nếu lớn hơn) · Hoàn thành · Tiêu chí hoàn thành (danh sách, thêm/xóa) · Phụ thuộc ([C] `Command` combobox, chip có ✕) · Ghim vào ngày ([C] `Switch` + date picker) · ghi chú "Lưu chỉ ghi nhận thay đổi" · `Xóa task` (outline đỏ) · `Hủy` · `Lưu thay đổi`.
- `Xếp lại lịch` → nếu có xung đột: [C] `Dialog` "N task ghim bị xung đột", mỗi task một thẻ với nguyên nhân bằng số và [C] `RadioGroup` (mặc định **Giữ ghim**; hoặc **Bỏ ghim & xếp tự động**; với xung đột phụ thuộc thêm "Dời ghim sang ngày sớm nhất hợp lệ" và "Bỏ liên kết phụ thuộc"). Sau đó (hoặc khi không có xung đột): `Dialog` xem trước diff — dòng tóm tắt (khả thi, Cần trước → sau, ngày xong trước → sau), bảng Task · Trước → Sau (tối đa 3 dòng + "N task khác", `Xem tất cả`), `Quay lại` / `Áp dụng lịch mới`.
- Kéo-thả khối task trên lịch tuần/tháng = dời + ghim; ô đích hiện ngay "! 8/4h" nếu vượt capacity; toast "Đã dời … và ghim. Ngày này đang vượt 4h." + `Hoàn tác` + `Xếp lại ngay`. Luôn có đường thay thế bằng bàn phím: menu "Dời sang ngày…".
- Xóa: nếu có task phụ thuộc → `AlertDialog` chọn "Chỉ xóa task này, bỏ liên kết" (mặc định) / "Xóa cả task phụ thuộc (tổng Xh)"; nếu không → xóa ngay + toast Hoàn tác.

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | KR không có task: empty "KR 2.3 chưa có task" + `+ Thêm task` / `Sinh task bằng AI` (chỉ KR đó) |
| Đang tải | Nút `Đang xếp lại…` có spinner + "Scheduler, không dùng AI · thường < 2 giây"; bảng giữ nguyên, không khóa cuộn |
| Lỗi | Vòng lặp phụ thuộc: lỗi cạnh combobox nêu chuỗi `T1.1.6 → T1.1.8 → T1.1.6`. Giờ ngoài 2–6h: lỗi cạnh ô + `Tách thành 2 task`. Xếp lại thất bại: banner đỏ "Lịch cũ được giữ nguyên, N thay đổi vẫn còn" + Thử lại |
| Quá tải | Sau xếp lại mà thành đỏ: banner "Sau khi xếp lại: thiếu Xh … N task không kịp" + `Xem phương án →` (S13) |

**Mobile**: nhấn giữ thẻ task → [C] `Drawer` action sheet (Sửa chi tiết · Dời sang ngày… · Ghim · Đánh dấu hoàn thành · Xóa · Đóng); checkbox hoàn thành vùng chạm 44px; thanh dính trên tab bar "N thay đổi chưa xếp lại · Xếp lại"; Sheet sửa thành toàn màn.

**AC**
- Sửa/thêm/xóa/ghim không đổi ngày của task khác cho tới khi bấm `Áp dụng lịch mới`.
- Pill "Cần xếp lại" xuất hiện ngay sau thay đổi đầu tiên và biến mất sau khi áp dụng hoặc `Hoàn tác tất cả`.
- Task ghim giữ nguyên ngày sau mọi lần xếp lại trừ khi người dùng chọn "Bỏ ghim" trong hộp xung đột.
- Xung đột phụ thuộc tuân quy tắc D+1 (ADR-0003).
- Mọi thao tác kéo-thả có đường thay thế bằng bàn phím và có Hoàn tác.
- Fixture: sửa "Chiến dịch email" 4h → 6h + ghim "Khảo sát" 09/10 → 1 xung đột; chọn Giữ ghim → 44 task đổi ngày, Cần 214h, xong 16/12, vẫn Xanh.

---

## S11 — Lịch tháng · `/q/{year}-Q{n}/calendar?view=month&m=YYYY-MM`

**Mục đích**: nhìn toàn cảnh tháng, thấy tuần căng/trống, mốc KR.

- FullCalendar `dayGridMonth`, bắt đầu Thứ 2, cùng nguồn dữ liệu S6. [C] `ToggleGroup` Tuần/Tháng trong pagehead, giữ ngày đang xem khi chuyển.
- Ô ngày: số ngày · "đã xếp/capacity" · thanh tải · tối đa 3 chip task (màu Objective, cắt chữ) + "+N" · mốc KR là chip viền "◆ Mốc KR 1.2". Hôm nay: số ngày nền đậm + viền ô.
- Ngày nghỉ / ngày lễ / nghỉ phép / buffer: 4 hoa văn khác nhau; ô lễ và nghỉ phép ghi tên + "0h". Chú giải dưới lịch.
- Click ô → [C] `Popover`: ngày đầy đủ · giờ đã xếp · khối task · dòng mốc KR · `Mở chi tiết` / `Xem tuần N`. Kéo chip = dời + ghim (S10).

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | Tháng thuộc quý chưa lập kế hoạch: "Tháng 1/2027 chưa có task… 1 KR đã được dời sang đây" + `Lập kế hoạch Q1/2027` |
| Đang tải | Lưới skeleton 7 cột (T7/CN mờ) |
| Lỗi | Banner đỏ + Thử lại |
| Quá tải | Banner "15 task (58h) không xếp được trong quý" + `Xem phương án →`; khay "Chưa xếp (15)" cạnh lịch liệt kê task, kéo vào ngày để ghim |

**Mobile**: lưới tháng gọn (số ngày + chấm màu Objective, ngày nghỉ mờ), chạm ngày → agenda bên dưới; seg Tuần/Tháng dưới header.

**AC**: tổng giờ chip trong một ô = số trên ô; ô lễ 24/11/2026 hiện "Ngày Văn hóa Việt Nam · 0h"; tháng 10/2026 kịch bản xanh = 22 ngày làm việc, 88/88h; task không kịp không bao giờ biến mất khỏi giao diện.

---

## S12 — Dashboard workload & mốc KR · `/q/{year}-Q{n}/workload`

**Mục đích**: biết tuần nào căng và KR dạng số nên đạt bao nhiêu theo thời gian.

- 4 thẻ KPI ([C] `Card`): Cần/Có + % sử dụng · Dự kiến xong (so với ngày bắt đầu buffer) · Số tuần đầy 100% · Tiến độ thực tế (task/giờ đã xong, "Đúng kế hoạch" / "Chậm Xh").
- Biểu đồ Recharts `ComposedChart`: mỗi tuần một cột = capacity tuần; phần dưới chồng theo Objective (`--chart-n`), phần còn trống vẽ mờ viền đứt, phần buffer hoa văn buffer; nhãn % trên đầu cột; trục X "T40…T53" (ghi chú "lễ" ở tuần có ngày lễ). `ToggleGroup` Theo tuần / Theo tháng. Tooltip: tuần, capacity, giờ theo Objective, % .
- Bảng mốc KR ([C] `Table`): KR · Baseline · Cuối T10 · Cuối T11 · Cuối T12 (target) · Thực tế gần nhất (ô nhập số + ngày) · nhãn. `Select` "Cách tính mốc": Theo tiến độ task (mặc định) / Tuyến tính theo thời gian / Tự nhập; `ToggleGroup` Tháng/Tuần. KR milestone (không phải số) hiện "◆ ngày". Chú thích dưới bảng: "Mốc = mức kỳ vọng nếu task xong đúng lịch… Không phải dự báo kết quả."
- Nội suy theo tiến độ task: `mốc = baseline + (target − baseline) × giờ task của KR đã xong tới cuối kỳ / tổng giờ KR`. Fixture: KR 1.3 3,2% → 1% với 28/30h xong trong tháng 10 → 1,1%; KR 2.2 40% → 70% với 50/94h xong trong tháng 11 → 56%.
- KR gắn cờ chỉ số trễ (người dùng đánh dấu ở S2 hoặc AI gợi ý) có badge "! Chỉ số trễ".

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | "Chưa có dữ liệu — tạo kế hoạch để xem workload" |
| Đang tải | Skeleton KPI + skeleton biểu đồ |
| Lỗi | Banner đỏ + Thử lại |
| Quá tải | Buffer bị lấp vẽ đậm; thêm cột "Chưa xếp 58h" gạch chéo đỏ ngoài trục thời gian; nút "Xem phương án" → S13 |

**Mobile**: KPI 2×2; danh sách tuần dạng thanh ngang "T41 ▓▓▓ 20/20h"; mốc KR của tháng hiện tại dạng thẻ; truy cập qua tab "Thêm".

**AC**: chiều cao cột luôn = capacity tuần (T40 = 8h, T48 = 16h, T53 = 16h); tổng giờ các cột = Cần; % không chỉ thể hiện bằng màu; nhập "Thực tế" không chạy lại scheduler; bảng dùng `<th>` và số căn phải.

---

## S13 — Panel phương án xử lý quá tải · `/q/{year}-Q{n}/options`

**Mục đích**: biến "quá tải" thành lựa chọn có số liệu, áp dụng trong một bước.

- Vào từ: nút trong S7 đỏ, banner quá tải S5/S6/S10/S11, S12.
- Pagehead nhắc lại vấn đề: "Cần 318h / Có 260h · thiếu 58h · 15 task không kịp (KR 3.1, KR 3.2)".
- 3 nhóm thẻ `OverloadOptionCard` ([C] `Checkbox` + nội dung + cột kết quả bên phải):
  - Tăng thời gian: giờ/ngày T2–T6 (stepper, mặc định +1h, gợi ý mức tối thiểu thành Xanh) · Làm Thứ 7 · Làm Chủ nhật · Làm ngày lễ trong quý.
  - Giảm phạm vi: Bỏ KR ưu tiên thấp nhất bị ảnh hưởng · Bỏ Objective ưu tiên thấp nhất · Nhờ AI thu gọn phạm vi (nút `Chạy đề xuất`, ghi provider/model và thời gian ước tính).
  - Dời sang quý sau: từng KR bị ảnh hưởng.
- Kết quả mỗi thẻ = khi dùng một mình: badge ký hiệu + chữ (✓ Xanh / ! Vàng / × Đỏ) + dòng số (thiếu Xh, dùng Xh buffer, ngày xong).
- Phương án loại trừ nhau (Bỏ KR 3.2 vs Dời KR 3.2) → thẻ mờ + lý do, không ẩn. **Không chọn sẵn phương án nào.**
- Rail phải 400px "Xem trước: N phương án": chip đã chọn (✕ để bỏ) · bảng Trước/Sau (Cần, Có, Chênh lệch, Trạng thái, Dự kiến xong, Task không kịp) · 2 thanh mức sử dụng (vạch bắt đầu buffer) · "Sẽ thay đổi" (hệ quả ngoài lịch: Cài đặt, quý sau, task ghim, có gọi AI không) · `Áp dụng phương án` (primary, lớn) · `Bỏ chọn tất cả`. Cập nhật mỗi lần tick (gọi `/options/evaluate`, debounce 300ms).
- AI thu gọn: `Dialog` duyệt từng đề xuất (checkbox, số giờ tiết kiệm, badge "Đổi target KR" nếu đụng target), kết quả tổng hợp, `Bỏ qua` / `Thêm vào lựa chọn (n/N)`.
- Áp dụng: một giao dịch; toast "Đã áp dụng 2 phương án · Kế hoạch: Sát – dùng buffer" + `Hoàn tác`.

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | Kế hoạch khả thi: "Không cần phương án — còn 48h dự phòng" |
| Đang tải | "Đang tính 9 phương án (scheduler, không dùng AI)…" + skeleton thẻ; thẻ nào xong hiện trước |
| Lỗi | Lỗi từng thẻ ngay trong thẻ + Thử lại (VD "Q1/2027 chưa có lịch làm việc"); AI lỗi sau 2 lần thử: banner + `Mở Cài đặt AI`, các phương án khác vẫn dùng được |
| Quá tải | Chính là trạng thái mặc định của màn này; nếu tổ hợp vẫn đỏ, nút Áp dụng vẫn bật nhưng rail ghi "Vẫn thiếu Xh" |

**Mobile**: thẻ gọn (tên, ±giờ, badge kết quả); thanh dính đáy "2 đã chọn · −58h → +24h · ! Vàng" + `Xem trước & áp dụng` mở [C] `Drawer` chứa nội dung rail.

**AC**: số trên mọi thẻ khớp một lần chạy scheduler thật với cùng dữ liệu; không phương án nào được chọn sẵn; phương án AI không bao giờ tự chạy; "Dời KR" tạo KR nháp ở quý sau (S14) với đủ task; Hoàn tác khôi phục cả Cài đặt lẫn KR bị dời; fixture "Làm Thứ 7 + Dời KR 3.2" → 288h/312h, Vàng, 8h buffer, xong 24/12.

---

## S14 — Quản lý quý · `/quarters`

**Mục đích**: quản lý mọi thứ ngoài quý hiện tại. [C] `Tabs`: Các quý · Nghỉ phép · Ngày lễ · Xuất dữ liệu.

- Lưới thẻ quý (`QuarterCard`), sắp: đang diễn ra → nháp → chưa xem lại → đã xem lại → không có kế hoạch. Thẻ: tên quý · badge trạng thái · khoảng ngày · số Objective/task · pill khả thi (quý hiện tại) hoặc % task xong + số KR đạt (quý cũ) · banner "1 KR được dời từ Q4/2026" (quý nháp) · nút chính · `⋯` ([C] `DropdownMenu`: Xem lại quý · Sao chép OKR sang quý khác… · Xuất dữ liệu… · — · Xóa quý…).
- Xem lại quý cũ: banner "Chỉ xem — quý đã kết thúc"; 4 KPI (task xong, giờ đã làm, KR đạt, task trễ hạn); bảng KR · Baseline · Target · Kết quả cuối (ô nhập được) · Đánh giá (✓ Đạt / ! Đạt X%); `Sao chép KR chưa đạt sang Q…`; `Đánh dấu đã xem lại`.
- Xóa quý: `AlertDialog` nêu số Objective/task sẽ mất · ô "Gõ "Q2/2026" để xác nhận" · `Xuất trước` · `Xóa vĩnh viễn` (tắt tới khi gõ đúng). Quý đang diễn ra không có mục Xóa (banner giải thích).

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | "Chưa có quý nào" + `Lập kế hoạch` |
| Đang tải | 3 skeleton thẻ |
| Lỗi | Banner đỏ + Thử lại |
| Quá tải | Thẻ quý hiện tại mang pill đỏ "Quá tải – thiếu Xh" + nút `Xem phương án` |

**AC**: quý cũ không sửa được task/lịch; KR dời từ S13 luôn hiện ở quý đích; xóa quý cần gõ đúng tên; không thể xóa quý đang diễn ra.

## S14b — Nghỉ phép & ngày lễ

- **Nghỉ phép**: form Từ ngày · Đến ngày ([C] `Calendar` range) · Thời lượng (Cả ngày / Nửa ngày) · Ghi chú (không bắt buộc, không hỏi lý do). Banner "Tác động nếu lưu" tính trước: giờ mất, ngày xong mới, buffer, số task dời (fixture: nghỉ T6 16/10 → −4h, xong 24/12 → 25/12, buffer 8h → 12h). Bảng đã lưu (Ngày · Thời lượng · Quý · Ghi chú · ⋯). Nghỉ phép trùng task ghim → hộp xung đột S10.
- **Ngày lễ**: `ToggleGroup` năm · `Khôi phục mặc định` · `+ Thêm ngày`. Bảng: Ngày (gộp ngày liền nhau, ▾ mở) · Tên · Loại (Nghỉ lễ / Nghỉ bù / Nghỉ hoán đổi / Làm bù / Nghỉ riêng) · Trạng thái (Chính thức / ! Dự kiến / Chưa lưu) · Nguồn (link văn bản) · ⋯. Hàng thuộc quý hiện tại tô nhấn + badge quý. Nguồn dữ liệu: `backend/app/calendar/data/vn_holidays_{year}.json` (trường `kind`, `status`, `source`, `makeup_days`).
- Thêm/sửa/xóa ngày → banner tác động (fixture: thêm 31/12 → 312h → 308h, buffer bắt đầu 22/12, dùng 12h; vẫn Vàng, vẫn xong 24/12) → lưu → kế hoạch "Cần xếp lại".
- Banner thông tin khi có đề xuất chưa chính thức (VD nghỉ dài hơn dịp 24/11/2026): "ứng dụng chỉ dùng ngày đã có văn bản".
- Năm có ngày dự kiến (2027: Tết 04–10/02, 03/09): badge "! Dự kiến"; khi dữ liệu mặc định cập nhật khác đi → quý bị ảnh hưởng hiện "Cần xếp lại" kèm lý do.

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | Chưa có nghỉ phép: "Chưa có ngày nghỉ phép nào" + form |
| Đang tải | Skeleton bảng |
| Lỗi | Trùng ngày lễ: lỗi cạnh ô ngày. Lưu thất bại: banner "Thay đổi vẫn giữ trong form" + Thử lại |
| Quá tải | Banner tác động đổi sang đỏ khi nghỉ phép/ngày lễ làm kế hoạch thành quá tải, kèm `Xem phương án` |

**AC**: mọi thay đổi capacity có xem trước tác động bằng số trước khi lưu; `Khôi phục mặc định` chỉ xóa ngày tự thêm/sửa và có xác nhận; ngày dự kiến được dùng để xếp lịch và có nhãn.

## S14c — Xuất dữ liệu & Chính sách dữ liệu · `/policy`

- **Xuất**: `Dialog` Quý · Định dạng (Excel .xlsx 3 sheet: OKR · Task · Lịch theo ngày — mặc định; CSV UTF-8 có BOM, 1 file task) · Bao gồm (tiêu chí hoàn thành, phụ thuộc, ghi chú nghỉ phép — tắt mặc định) · ghi chú "Không bao giờ chứa mật khẩu hay API key" · `Tải xuống okr-q4-2026.xlsx`. Ngày dạng ISO; tên cột theo ngôn ngữ đang chọn. Trạng thái: đang tạo file (spinner), lỗi (Thử lại / chọn CSV), quý trống (nút tắt + lý do).
- **Chính sách dữ liệu**: callout đầu trang theo provider trong Cài đặt — Local: xanh, "Nội dung OKR được gửi tới `http://localhost:11434` — không rời khỏi hệ thống"; OpenAI: vàng, "gửi tới api.openai.com, chịu chính sách dữ liệu của OpenAI; ứng dụng không bao giờ tự chuyển sang OpenAI" + `Chuyển về Local`. 4 khối: Dữ liệu được lưu · Dữ liệu gửi tới AI (và những gì không gửi) · Truy cập (mật khẩu chung, cookie httpOnly) · Quyền của bạn (`Xuất tất cả`, `Xóa toàn bộ dữ liệu…`).
- Xóa toàn bộ: `AlertDialog` nêu phạm vi (quý, task, nghỉ phép, ngày lễ tự thêm; giữ cài đặt AI và mật khẩu) · nhập lại mật khẩu truy cập · `Xuất trước` · `Xóa tất cả` (xem D13).

**AC**: callout đổi ngay khi đổi provider trong S8; file xuất mở đúng tiếng Việt trong Excel; file không chứa secret; trang chính sách không có văn phong pháp lý, mỗi khối ≤ 4 dòng.

---

## Quyết định mở liên quan đợt 2

D8 (cách tính mốc KR), D9 (xếp lại gom hay tự động), D10 (kéo-thả có tự ghim), D11 (tự tạo quý nháp khi dời KR), D12 (quý cũ chỉ đọc), D13 (nút xóa toàn bộ dữ liệu) — chi tiết trong [`README.md`](README.md#quyết-định-ux-còn-mở-cần-ceoboard-chốt).
