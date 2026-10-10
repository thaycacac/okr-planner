# Spec UX đợt 1 — luồng MVP

Wireframe: [`wireframes/wave1.html`](wireframes/wave1.html) (mở trực tiếp trên trình duyệt, nút VI/EN ở góc phải). Ảnh PNG: [`png/vi/`](png/vi/) và [`png/en/`](png/en/), tên file `wave1-<mã màn>.png`.

Ký hiệu trong spec: **[C]** = component shadcn/ui hoặc thư viện đã chốt, `--token` = CSS variable. Số hồng trong wireframe (①②…) khớp mục "Ghi chú" cạnh frame.

Dữ liệu mẫu (giả lập, dùng lại được làm fixture cho test):

| Kịch bản | Objective | Giờ cần (D) | Giờ có (S) | Kết quả |
|---|---|---|---|---|
| Xanh | O1 + O2 | 212h | 260h | Xong 15/12/2026, còn 48h (82%) |
| Vàng | O1 + O2 + một phần O3 | 250h | 260h | Xong 29/12, dùng 18h/28h buffer, 5 task trong buffer (96%) |
| Đỏ | O1 + O2 + O3 | 318h | 260h | Thiếu 58h, 15 task (KR 3.1: 7 task/28h, KR 3.2: 8 task/30h) không xếp được |

Q4/2026: 01/10–31/12, 65 ngày làm việc (T2–T6, trừ lễ 24/11 Ngày Văn hóa Việt Nam theo seed `backend/app/calendar/data/vn_holidays_2026.json`), 4h/ngày = 260h, buffer ≈10% làm tròn theo ngày = 28h (23/12–31/12), phần trước buffer = 232h.

---

## Khung ứng dụng (dùng chung)

- **Topbar** (cao 56): logo · [C] `Select` quý (`Q4/2026`) · pill khả thi (S7) · [C] `ToggleGroup` VI/EN · nút `Đăng xuất`.
- **Sidebar desktop** (220): Kế hoạch OKR · Công việc · Lịch · Cài đặt; cuối: Chính sách dữ liệu. Đợt 2 thêm Workload, Quản lý quý.
- **Tab bar mobile** (cao 64, đáy): OKR · Công việc · Lịch · Cài đặt. Ẩn trong wizard S1–S4.
- **Wizard S1–S4**: không sidebar, [C] stepper 5 bước (Chọn quý · Nhập OKR · Làm rõ · Sinh kế hoạch · Kế hoạch), CTA chính ở góc phải dưới (desktop) / dính đáy (mobile).
- **Breakpoint** theo nội dung: `<768` mobile; `768–1279` sidebar thu thành icon, rail khả thi thành chip ở topbar; `≥1280` sidebar + rail 320.
- **Màu Objective**: `--chart-1..5` theo thứ tự Objective, luôn đi kèm mã `O1`, `O2`… (không dùng màu làm tín hiệu duy nhất). Token đã đổi sang 5 màu phân loại (giá trị light/dark ở README, mục Design system).
- **Khả thi**: dùng token đã có `--success`/`--success-muted`, `--warning`/`--warning-muted`, `--destructive` (nền `destructive/10`). Mỗi mức luôn có ký hiệu (✓ ! ×) và chữ.

---

## S9 — Mật khẩu truy cập chung · `/login`

**Mục đích**: vào app bằng một mật khẩu chung (đọc từ env, hash argon2).

- [C] `Card` giữa màn 400px; `Input type=password` có nút Hiện/Ẩn; `Button` full-width cao 44.
- Enter để gửi; autofocus ô mật khẩu; không có "Ghi nhớ" (cookie phiên httpOnly đã xử lý).
- VI/EN chọn được ngay trên màn đăng nhập.

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | Mặc định như wireframe |
| Đang tải | Nút chuyển thành spinner + "Đang kiểm tra…", khóa ô nhập |
| Lỗi sai mật khẩu | Viền đỏ + "Mật khẩu không đúng. Còn N lần thử trước khi tạm khóa 60 giây." |
| Lỗi bị giới hạn | [C] `Alert` đỏ + đếm ngược, nút bị khóa |
| Hết phiên | [C] `Alert` info "Phiên đã hết hạn… dữ liệu vẫn được giữ", sau đăng nhập quay về URL cũ |
| Quá tải | Không áp dụng |

**AC**: Enter gửi form; thông báo lỗi không tiết lộ độ dài mật khẩu; sau khi đăng nhập về lại đúng trang trước đó.

---

## S1 — Chọn Quý + Năm · `/plan/new`

**Mục đích**: chọn quý và thấy ngay khoảng ngày, số ngày làm việc, số giờ khả dụng.

- [C] `ToggleGroup` Q1–Q4 (lớn) + `Select` năm (năm hiện tại ± 1).
- Mặc định: quý hiện tại; nếu quý hiện tại còn `< 10` ngày làm việc thì chọn quý kế tiếp.
- Thẻ kết quả: khoảng ngày · badge trạng thái quý · 4 chỉ số (Ngày, Ngày làm việc, Giờ khả dụng, Buffer) · dòng "Theo cài đặt: … · Sửa" → S8.
- Badge trạng thái quý (chữ + màu): `Sắp bắt đầu · còn N ngày` (info), `Đang diễn ra` (warning), `Đã kết thúc` (neutral).
- Quý đang diễn ra: mọi số liệu tính từ `max(đầu quý, hôm nay)` và hiện banner vàng "Quý đã bắt đầu từ … — lịch chỉ được xếp từ hôm nay (…) → còn N ngày làm việc · Xh".

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | Không có: luôn có quý mặc định |
| Đang tải | Skeleton cho thẻ kết quả (khi tải ngày lễ/kế hoạch đã có) |
| Lỗi | Banner đỏ "Không tải được danh sách ngày lễ — số ngày làm việc tạm tính" + Thử lại; vẫn cho tiếp tục |
| Đã có kế hoạch | Banner "Q4/2026 đã có kế hoạch (3 Objective · 7 KR…)" + `Mở kế hoạch` (chính) / `Thêm Objective vào kế hoạch` |
| Quý đã kết thúc | Banner neutral, CTA tiếp tục bị khóa, gợi ý xem lại (đợt 2) |
| Quá tải | Không áp dụng; thay bằng cảnh báo "quý quá ngắn" khi còn `< 10` ngày làm việc |

**AC**: đổi quý/năm cập nhật số liệu `< 100ms` (tính phía client từ cấu hình đã tải); ví dụ hôm nay 30/09/2026 chọn Q3/2026 phải hiện "còn 1 ngày làm việc · 4h".

---

## S2 — Form OKR động · `/plan/new/okr` (và "Kế hoạch OKR" khi sửa)

**Mục đích**: nhập nhiều Objective, mỗi Objective nhiều KR, có loại KR, baseline/target, ngữ cảnh tùy chọn.

- Objective = [C] `Card` + `Collapsible`: tay kéo `⋮⋮` · mã màu `O1` · `Input` tiêu đề · `ToggleGroup` ưu tiên **Cao / TB / Thấp** (mặc định TB) · menu `⋯` (Nhân bản, Xóa) · nút thu gọn.
- "Ngữ cảnh (tùy chọn)": ẩn mặc định; mở ra có `Select` Lĩnh vực (danh sách gợi ý + nhập tự do) và `Input` Ràng buộc.
- Dòng KR: mã `KR 1.1` · `Input` nội dung · `Select` loại. Loại quyết định trường phụ:
  - **Số đo**: Baseline, Target, Đơn vị (bắt buộc cả baseline và target).
  - **Milestone**: Ngày mong muốn (tùy chọn, `DatePicker` trong quý).
  - **Có/Không**: không có trường phụ.
  - **Khác**: Ghi chú (tùy chọn).
- `＋ Thêm KR`, `＋ Thêm Objective`. Giới hạn mềm: ≤ 5 Objective, ≤ 5 KR/Objective (chỉ cảnh báo).
- Rail phải: Tóm tắt (số Objective/KR + số lỗi), checklist "KR tốt là…", link "Xem ví dụ OKR mẫu", banner "AI có thể hỏi lại tối đa 5 câu, không bịa số liệu".
- Footer dính: `← Quay lại` · trạng thái ("Sửa 1 lỗi để tiếp tục") · `Kiểm tra & tiếp tục →`.
- **Tự lưu nháp** (debounce 1s) → "Đã lưu nháp HH:mm".
- **Pre-check deterministic** (không gọi AI): KR số đo thiếu baseline/target; KR trống; KR trùng văn bản trong cùng Objective; Objective không có KR. Validate khi blur và khi bấm tiếp tục; banner tổng hợp lỗi có link nhảy tới trường.
- Xóa KR/Objective: không hỏi xác nhận, hiện [C] `Toast` "Đã xóa KR 1.3 · Hoàn tác" trong 5s.

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | 1 thẻ Objective + 1 dòng KR sẵn, placeholder là ví dụ; link "Điền OKR ví dụ" |
| Đang tải | Skeleton thẻ Objective |
| Lỗi | Banner tổng hợp lỗi pre-check; banner vàng khi lưu nháp thất bại (giữ dữ liệu ở localStorage, tự thử lại) |
| Cảnh báo sớm | > 5 Objective hoặc tổng KR lớn → banner vàng về nguy cơ quá tải; chế độ sửa kế hoạch cũ → banner info "Chỉ KR thay đổi mới được sinh lại; task đã xong/đã ghim giữ nguyên" |
| Quá tải | Chưa tính được ở bước này (chỉ cảnh báo sớm theo số lượng) |

**Mobile**: 1 cột; Objective dạng accordion; mỗi KR là thẻ con, Baseline/Target/Đơn vị xếp 3 cột nhỏ; "Thêm ngữ cảnh" là link; CTA `Kiểm tra & tiếp tục` dính đáy; thanh tiến trình bước 2/5 dưới header.

**AC**: đổi loại KR đổi trường ngay, không mất dữ liệu đã nhập (giữ ẩn nếu đổi lại); không thể qua bước 3 khi còn lỗi pre-check; Tab đi đúng thứ tự trường; kéo-thả có phương án bàn phím (menu `⋯` → Lên/Xuống).

---

## S3 — Câu hỏi làm rõ · `/plan/new/clarify`

**Mục đích**: AI hỏi tối đa 5 câu trước khi sinh kế hoạch.

- Header: tiêu đề "AI cần làm rõ N điểm" · phụ đề "AI sẽ không tự bịa số liệu" · badge provider + model (`AI: Local · qwen2.5:7b`).
- Tiến độ "k/N đã trả lời" + [C] `Progress` + "Vòng 1/2".
- Mỗi câu = [C] `Card`: chip KR/Objective liên quan · badge **Bắt buộc**/**Không bắt buộc** · câu hỏi · "Vì sao hỏi" · gợi ý trả lời nhanh (nếu AI trả về options, dạng [C] `Badge` bấm được) · `Textarea` · link "Sửa thẳng KR" (mở inline editor của KR đó) · "Bỏ qua câu này" (chỉ câu không bắt buộc).
- Câu đã trả lời thu gọn, có nút Sửa.
- Footer: `← Sửa OKR` (về S2, giữ câu trả lời) · "Còn N câu bắt buộc" · `Gửi câu trả lời →` (bật khi đủ câu bắt buộc).
- Sau khi gửi: chạy lại pre-check + clarify; nếu vẫn cần hỏi → vòng 2; tối đa 2 vòng rồi sang S4.

| Trạng thái | Hiển thị |
|---|---|
| Đang tải | "AI đang đọc OKR của bạn…" + thời gian đã chạy + "Local LLM có thể mất 10–60 giây" + skeleton + `Hủy` |
| Rỗng (OKR đã rõ) | Banner xanh "Không cần làm rõ thêm", tự sang S4 sau 3s; nút `Ở lại sửa OKR` / `Sinh kế hoạch ngay` |
| Lỗi kết nối LLM | Banner đỏ nêu URL + nguyên nhân · dòng "Ứng dụng không tự chuyển sang OpenAI…" · `Mở Cài đặt AI` / `Thử lại` |
| Lỗi JSON sau 2 lần thử | Banner đỏ + gợi ý model lớn hơn hoặc OpenAI · `Mở Cài đặt AI` / `Thử lại` |
| Quá tải | Không áp dụng |

**Mobile**: 1 câu/màn, nút `Tiếp` / `Quay lại`, thanh tiến độ ở đầu.

**AC**: không thể gửi khi còn câu bắt buộc trống; quay về S2 rồi trở lại vẫn giữ câu trả lời; câu bị bỏ qua được lưu để task liên quan gắn nhãn "Giả định chưa xác nhận" (xem quyết định mở D3).

---

## S4 — Tiến trình sinh kế hoạch · `/plan/new/generate`

**Mục đích**: hiển thị job nền (SSE/polling) có thể > 60s.

- Cột trái: checklist pipeline — Kiểm tra OKR · Làm rõ · Phân rã theo KR (k/N) · Gộp trùng & phụ thuộc · Kiểm tra hợp lệ · Xếp lịch (thuật toán, không dùng AI); badge provider/model.
- Cột chính: tiêu đề · "Đã chạy mm:ss · <kỳ vọng theo provider>" · % tổng lớn + [C] `Progress` · banner info (sau 60s) · bảng KR: mã · tên · `Progress` · kết quả (`✓ 9 task · 38h` / spinner % / `Thử lại 1/2` / `Đang chờ` / lỗi).
- `Hủy sinh kế hoạch` (outline đỏ) → [C] `AlertDialog`: "KR đã xong được giữ lại".
- Rời trang được: job chạy tiếp; quay lại `/plan/new/generate` hoặc mở app sẽ thấy tiến trình/kết quả.
- Xong: banner xanh "Đã sinh 42 task · 318h" → tự chuyển S5 sau 1,5s; nếu đỏ, S5 mở kèm panel S7 đỏ.

| Trạng thái | Hiển thị |
|---|---|
| Đang chạy | Như wireframe |
| > 60 giây | Banner info (không phải lỗi) + gợi ý model nhỏ hơn/OpenAI, **không tự chuyển** |
| Lỗi 1 KR | Dòng KR đỏ + `Bỏ qua KR này` / `Thử lại KR 3.1`; KR khác chạy tiếp |
| Lỗi toàn cục | Banner đỏ, giữ KR đã xong, `Tiếp tục từ KR x` / `Mở Cài đặt AI` |
| Rỗng | Không có job → chuyển về S2 |
| Quá tải | Biết sau bước xếp lịch → chuyển sang S5 với panel đỏ |

**AC**: % cập nhật ít nhất mỗi 2s hoặc theo sự kiện SSE; reload trang không mất tiến trình; hủy không xóa KR đã xong.

---

## S5 — Danh sách task phân cấp · `/q/{year}-Q{n}/tasks`

**Mục đích**: xem Objective → KR → Task với tên, mô tả, giờ, tiêu chí hoàn thành, phụ thuộc, ngày bắt đầu/kết thúc.

- Pagehead: "Kế hoạch Q4/2026" + dòng nguồn gốc (số Objective/KR/task/giờ · provider · model · thời điểm sinh).
- [C] `Tabs`: Danh sách · Lịch tuần (đợt 2 thêm Lịch tháng).
- Toolbar: `Input` tìm task · `Select` lọc Objective · `Mở rộng tất cả`.
- Bảng cây ([C] `Table` + `Collapsible` hàng): cột Tên · Giờ · Bắt đầu · Kết thúc · Phụ thuộc · (trạng thái xếp lịch khi có vàng/đỏ).
  - Hàng Objective: mã màu, tên, badge ưu tiên, tổng giờ, khoảng ngày.
  - Hàng KR: mã KR, tên, badge loại (+ `baseline → target` với số đo), tổng giờ, khoảng ngày.
  - Hàng Task: tên, giờ, ngày, chip phụ thuộc (`T1.1.1`; hover = tên, click = nhảy tới).
- Click task → [C] `Sheet` phải 460px: mã task + KR · tên · 3 chỉ số (ước lượng, bắt đầu, kết thúc) · Mô tả · Tiêu chí hoàn thành (checklist) · Phụ thuộc (và "Chặn:") · Phân bổ theo ngày (ngày → giờ).
- Rail phải = S7 (xem S6 cho bố cục rail).

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | Empty state "Chưa có task nào trong Q4/2026" + `Nhập OKR` |
| Đang tải | Skeleton hàng |
| Lỗi | Banner đỏ + Thử lại |
| Vàng | Task trong buffer có badge "Trong buffer" (warning) |
| Quá tải | Banner đỏ đầu bảng "15 task (58h) không kịp trước 31/12/2026"; task không xếp được có badge "× Không kịp", ngày để "—", gom cuối KR, không bao giờ ẩn |

**Mobile**: header Objective/KR dính khi cuộn; task là thẻ (tên, giờ, khoảng ngày, chip "← T1.1.1"); chạm → sheet toàn màn; chip khả thi ở header.

**AC**: mở/đóng nhóm giữ trạng thái khi đổi tab; drawer đóng bằng Esc và trả focus về hàng; 50 task (kịch bản xanh) / 77 task (kịch bản đỏ) render không giật (không cần virtualize ở MVP).

---

## S6 — Lịch tuần · `/q/{year}-Q{n}/calendar?view=week`

**Mục đích**: xem task đã xếp theo ngày trong tuần.

- FullCalendar `dayGridWeek`, bắt đầu Thứ 2, `eventContent` tùy biến; **không dùng timeGrid** vì task phân bổ theo giờ/ngày, không theo khung giờ.
- Header mỗi ngày: "T2 05" · "đã xếp/capacity" (VD `4/4h`) · thanh capacity (không bao giờ > 100%).
- Khối task: nền nhạt theo màu Objective + viền trái màu đậm · tên (+ "(1/2)" nếu trải nhiều ngày) · "O1 · KR 1.1 · 3h"; chiều cao tối thiểu tỉ lệ với giờ.
- Ngày nghỉ (T7/CN tắt, lễ, nghỉ phép): hoa văn xám + chữ "Nghỉ"; vùng buffer: hoa văn vàng nhạt; chú giải dưới lịch.
- Điều hướng `‹ Tuần này ›`, phím ← →. Click khối → cùng `Sheet` chi tiết như S5.
- Rail phải 320: S7 + thẻ "Tuần này" (đã xếp, capacity, số task).

| Trạng thái | Hiển thị |
|---|---|
| Rỗng | Empty state trong lịch: "Tuần 52 không có task… Task cuối cùng kết thúc 15/12" + `Tới task cuối` |
| Đang tải | 7 cột skeleton (T7/CN mờ hơn) |
| Lỗi | Banner đỏ + Thử lại |
| Quá tải | Banner đỏ trên lịch "15 task (58h) không xếp được trước 31/12" + link chi tiết; các ngày buffer đầy |

**Mobile**: dải 7 ngày (thứ, ngày, chấm tải; ngày nghỉ mờ) + agenda ngày đang chọn (capacity bar, thẻ task kèm tiêu chí); vuốt trái/phải đổi ngày; `‹ ›` đổi tuần.

**AC**: tổng giờ khối trong một ngày = số ở header; ngày nghỉ không bao giờ có khối (trừ task ghim ở đợt 2); tuần đầu quý bắt đầu từ ngày đầu quý hoặc hôm nay; task phụ thuộc chỉ bắt đầu từ ngày D+1 sau khi task trước xong ở ngày D (ADR-0003) — wireframe tuần 41 minh họa: "Nhắc đọc" chờ tới T3 dù T2 còn 3h trống, giờ đó dành cho task khác sẵn sàng.

---

## S7 — Panel cảnh báo khả thi (cơ bản)

**Mục đích**: cho biết kế hoạch có kịp trong quý không, bằng con số.

- Ngưỡng: **Xanh** `D ≤ S − buffer` · **Vàng** `S − buffer < D ≤ S` · **Đỏ** `D > S`.
- Nội dung chung: tiêu đề mức (ký hiệu + chữ) · câu tóm tắt · 3 chỉ số (Cần, Có, Sử dụng % hoặc Thiếu) · thanh với vạch mốc bắt đầu buffer · ngày dự kiến xong.
- Vàng: thêm "đã dùng Xh trong Yh buffer · N task nằm trong buffer" + link gợi ý.
- Đỏ: "Thiếu Xh để kịp trước <ngày cuối quý>" · danh sách KR bị ảnh hưởng (số task · giờ), click → lọc S5 · link "Tăng giờ/ngày hoặc bật Thứ 7 trong Cài đặt" / "Sửa OKR" · nút mờ "Xem phương án có số liệu (đợt 2)" — **không hiển thị nút mờ này trong bản build** nếu đợt 2 chưa có; chỉ giữ 2 link.
- Vị trí: rail phải desktop (≥1280); pill ở topbar mọi màn (click mở panel dạng `Popover` khi không có rail); mobile: chip ở header → [C] `Drawer` (bottom sheet).
- Ngôn ngữ trung tính, không đổ lỗi.

| Trạng thái | Hiển thị |
|---|---|
| Đang tính | Spinner + skeleton |
| Lỗi | Banner đỏ nhỏ + Thử lại |
| Rỗng | Thẻ viền đứt "Chưa có kế hoạch — khả thi sẽ hiện sau khi sinh task" |
| Xanh / Vàng / Đỏ | Như wireframe |

**AC**: pill topbar và rail luôn cùng trạng thái; trạng thái đọc được bằng screen reader (`role="status"`, chữ đầy đủ, không chỉ màu).

---

## S8 — Cài đặt · `/settings/calendar`, `/settings/ai`

### Tab Lịch làm việc
- Bảng 7 thứ: tên thứ · [C] `Switch` Làm việc · stepper giờ (`−` `Input` `＋`, bước 0,5h, 0–12h). T7, CN mặc định tắt; tắt thì ẩn stepper và ghi "Không làm".
- Thẻ "Làm việc vào ngày lễ" + `Switch` + số ngày lễ trong quý hiện tại/kế tiếp.
- Thẻ "Buffer cuối quý 10%" (chỉ đọc ở MVP).
- **Xem trước ảnh hưởng** (cột phải, chỉ khi có thay đổi chưa lưu): giờ khả dụng quý hiện tại `cũ → mới (+Δ)` và trạng thái khả thi `cũ → mới`, tính bằng scheduler (không tốn AI).
- Footer dính: "N thay đổi chưa lưu" · `Hủy thay đổi` · `Lưu & xếp lại lịch`. Rời trang khi chưa lưu → hỏi xác nhận.

### Tab AI (LLM)
- 2 thẻ radio ([C] `RadioGroup` dạng card):
  - **Local LLM** — "Ollama / LM Studio / vLLM · Dữ liệu không rời máy · 0 USD · có thể chậm (1–4 phút/kế hoạch)", badge "Khuyến nghị cho OKR nhạy cảm".
  - **OpenAI** — "Nhanh, ổn định · ~0,03–0,45 USD/kế hoạch · Nội dung OKR được gửi tới OpenAI".
- Local: `Base URL` (mặc định `http://localhost:11434`) · `Model` (`Combobox` lấy danh sách sau khi kiểm tra kết nối, cho nhập tay).
- OpenAI: `API key` dạng password; sau khi lưu chỉ hiện `sk-••••3F9a` + nút `Thay` (không có nút hiện lại key); `Model` select.
- `Kiểm tra kết nối` → gửi 1 prompt nhỏ; kết quả inline: `✓ Kết nối OK · <model> · <độ trễ> · JSON schema: đạt` hoặc lỗi có hướng dẫn cụ thể (connection refused → kiểm tra `ollama serve`; model chưa có → `ollama pull <model>`; sai schema → chọn model lớn hơn; 401 → key sai/thu hồi).
- Banner vàng **luôn hiện**: "Không tự chuyển sang OpenAI — nếu Local LLM lỗi hoặc chậm, ứng dụng báo lỗi và dừng…".
- Chọn OpenAI lần đầu → [C] `AlertDialog` đồng ý gửi dữ liệu: `Giữ Local` / `Đồng ý, dùng OpenAI` (hai nút ngang hàng, không confirmshaming).
- `Lưu cài đặt AI`.

| Trạng thái | Hiển thị |
|---|---|
| Rỗng (lần đầu) | Banner info "Chưa cấu hình AI — không tìm thấy Ollama…"; nút sinh kế hoạch ở S2 dẫn về đây |
| Đang tải | Skeleton thẻ |
| Kiểm tra đang chạy | Nút spinner "Đang kiểm tra… (gửi 1 prompt nhỏ)" |
| Lỗi | Lỗi kiểm tra kết nối (4 loại trên); lưu thất bại (giữ dữ liệu trên form) |
| Quá tải | Thể hiện qua xem trước ảnh hưởng ở tab Lịch |

**Mobile**: [C] `Tabs` Lịch/AI; nhóm "Thứ 2 – Thứ 6" một stepper chung + "Chỉnh từng thứ ▾"; T7/CN/Lễ là dòng switch; xem trước thành thẻ nhỏ; nút lưu dính đáy trên tab bar.

**AC**: không lưu API key ra localStorage hay log; đổi provider không tự chạy lại AI; "Lưu & xếp lại lịch" chạy scheduler và cập nhật pill khả thi.
