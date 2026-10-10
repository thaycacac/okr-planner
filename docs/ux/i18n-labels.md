# Nhãn UI song ngữ (vi / en)

Sinh tự động từ wireframe bằng `python3 docs/ux/tools/extract_labels.py` — không sửa tay.
Nhãn trong wireframe là nguồn chuẩn; Frontend đặt key next-intl theo màn (VD `okrForm.addKr`).
Chuỗi có số liệu mẫu (giờ, ngày, tên OKR) là ví dụ: thay bằng tham số ICU (`{hours}h`, `{date}`).

## Khung ứng dụng (topbar, sidebar, tab bar)

| vi | en |
|---|---|
| Khả thi | Feasible |
| Sát – dùng buffer | Tight – using buffer |
| Quá tải – thiếu 58h | Overloaded – 58h short |
| Đang tính… | Calculating… |
| ⟳ Cần xếp lại | Needs rescheduling |
| Đăng xuất | Sign out |
| Kế hoạch OKR | OKR plan |
| Công việc | Tasks |
| Lịch | Calendar |
| Workload | Workload |
| Quản lý quý | Quarters |
| Cài đặt | Settings |
| Chính sách dữ liệu | Data policy |
| Thêm | More |

## Đợt 1 — MVP

### S9 — Nhập mật khẩu truy cập chung

| vi | en |
|---|---|
| Nhập mật khẩu truy cập | Enter access password |
| Ứng dụng dùng một mật khẩu chung cho người dùng duy nhất. | This app uses one shared password for its single user. |
| Mật khẩu | Password |
| Hiện | Show |
| Vào ứng dụng | Enter app |
| Quên mật khẩu? Liên hệ người quản trị máy chủ (mật khẩu đặt qua biến môi trường). | Forgot it? Ask the server admin (set via environment variable). |
| Đang kiểm tra… | Checking… |
| Mật khẩu không đúng. Còn 4 lần thử trước khi tạm khóa 60 giây. | Incorrect password. 4 attempts left before a 60-second lock. |
| Tạm khóa đăng nhập | Sign-in temporarily locked |
| Thử lại sau 0:48. | Try again in 0:48. |
| Phiên đã hết hạn. Đăng nhập lại để tiếp tục — dữ liệu của bạn vẫn được giữ. | Your session expired. Sign in again to continue — your data is kept. |

### S1 — Chọn Quý + Năm

| vi | en |
|---|---|
| Chọn quý | Quarter |
| Nhập OKR | OKRs |
| Làm rõ | Clarify |
| Sinh kế hoạch | Generate |
| Kế hoạch | Plan |
| Bạn lập kế hoạch cho quý nào? | Which quarter are you planning? |
| Lịch chỉ xếp trong khoảng ngày của quý này, trừ 10% buffer cuối quý. | Tasks are scheduled only inside this quarter, keeping a 10% end-of-quarter buffer. |
| Sắp bắt đầu · còn 1 ngày | Starts in 1 day |
| Ngày | Days |
| Ngày làm việc | Workdays |
| Giờ khả dụng | Available hours |
| Buffer 10% từ 23/12 | 10% buffer from Dec 23 |
| Theo cài đặt: 4h/ngày, Thứ 2–Thứ 6, không làm T7/CN/lễ · 1 ngày lễ trong quý (24/11, Ngày Văn hóa Việt Nam). | Per settings: 4h/day, Mon–Fri, no Sat/Sun/holidays · 1 holiday this quarter (Nov 24, Vietnamese Culture Day). |
| Sửa | Edit |
| Các quý khác | Other quarters |
| Đang diễn ra, kết thúc hôm nay | In progress, ends today |
| Đã kết thúc | Ended |
| Tiếp tục: Nhập OKR → | Continue: enter OKRs → |
| Quý đã bắt đầu từ 01/07/2026 | Quarter started on Jul 1, 2026 |
| Lịch chỉ được xếp từ hôm nay (30/09/2026) → còn 1 ngày làm việc · 4h. Nên chọn Q4/2026. | Scheduling starts today (Sep 30, 2026) → 1 workday · 4h left. Consider Q4/2026. |
| Chọn Q4/2026 | Pick Q4/2026 |
| Vẫn tiếp tục | Continue anyway |
| Q4/2026 đã có kế hoạch | Q4/2026 already has a plan |
| 3 Objective · 7 KR · 42 task · cập nhật 29/09. | 3 Objectives · 7 KRs · 42 tasks · updated Sep 29. |
| Thêm Objective vào kế hoạch | Add Objectives to plan |
| Mở kế hoạch | Open plan |
| Q2/2026 đã kết thúc — không thể xếp lịch mới. Bạn có thể xem lại kế hoạch cũ (đợt 2). | Q2/2026 has ended — no new scheduling. You can review the old plan (wave 2). |
| Tiếp tục | Continue |
| Không tải được danh sách ngày lễ | Couldn't load the holiday list |
| Số ngày làm việc tạm tính chưa trừ ngày lễ. | Workday count is provisional (holidays not excluded). |
| Thử lại | Retry |

### S2 — Form OKR động

| vi | en |
|---|---|
| Chọn quý | Quarter |
| Nhập OKR | OKRs |
| Làm rõ | Clarify |
| Sinh kế hoạch | Generate |
| Kế hoạch | Plan |
| OKR quý Q4/2026 | OKRs for Q4/2026 |
| 01/10 – 31/12/2026 · 260h khả dụng | Oct 1 – Dec 31, 2026 · 260h available |
| Đã lưu nháp 23:41 | Draft saved 23:41 |
| Ra mắt phiên bản 2.0 của ứng dụng đọc sách | Launch version 2.0 of the reading app |
| Cao | High |
| TB | Med |
| Thấp | Low |
| Ngữ cảnh (tùy chọn) | Context (optional) |
| Ẩn | Hide |
| Lĩnh vực | Domain |
| Sản phẩm / phần mềm | Product / software |
| Ràng buộc | Constraints |
| Làm một mình, chỉ buổi tối | Solo, evenings only |
| KẾT QUẢ THEN CHỐT | KEY RESULT |
| LOẠI | TYPE |
| ĐƠN VỊ | UNIT |
| Tăng người dùng hoạt động hằng tuần (WAU) | Grow weekly active users (WAU) |
| Số đo | Metric |
| Phát hành v2.0 lên App Store | Ship v2.0 to the App Store |
| Mốc mong muốn (tùy chọn): 30/11/2026 | Desired date (optional): Nov 30, 2026 |
| Giảm tỉ lệ crash | Reduce crash rate |
| KR số đo cần có target. | Metric KRs need a target. |
| Thêm KR | Add KR |
| 3/5 KR — nên giữ ≤ 5 KR mỗi Objective | 3/5 KRs — keep ≤ 5 per Objective |
| Đạt JLPT N4 trước kỳ thi tháng 12 | Pass JLPT N4 before the December exam |
| Trung bình | Medium |
| Xây dựng thương hiệu cá nhân | Build a personal brand |
| Thêm Objective | Add Objective |
| 1 lỗi cần sửa: KR 1.3 thiếu target | 1 issue to fix: KR 1.3 missing target |
| Đo được (có số hoặc có/không) | Measurable (number or yes/no) |
| Nằm trong khả năng của bạn | Within your control |
| Kết quả, không phải việc làm | An outcome, not an activity |
| Xem ví dụ OKR mẫu | See example OKRs |
| Bước tiếp theo AI có thể hỏi lại tối đa 5 câu nếu OKR còn mơ hồ. AI không tự bịa số liệu. | Next, the AI may ask up to 5 questions if anything is vague. It never invents numbers. |
| Quay lại | Back |
| Sửa 1 lỗi để tiếp tục | Fix 1 issue to continue |
| Kiểm tra & tiếp tục → | Check & continue → |
| Bước 2/5 · Nhập OKR | Step 2/5 · OKRs |
| Đã lưu | Saved |
| Thêm ngữ cảnh (tùy chọn) | Add context (optional) |
| Tăng WAU | Grow WAU |
| Đơn vị | Unit |
| 1 lỗi | 1 issue |
| Cần có target. | Target required. |
| Đạt JLPT N4 | Pass JLPT N4 |
| Thương hiệu cá nhân | Personal brand |
| Kiểm tra & tiếp tục | Check & continue |
| VD: Ra mắt phiên bản 2.0 của ứng dụng | e.g. Launch version 2.0 of the app |
| VD: Tăng WAU từ 800 lên 2.000 | e.g. Grow WAU from 800 to 2,000 |
| Chưa biết bắt đầu từ đâu? | Not sure where to start? |
| Điền OKR ví dụ | Fill in an example |
| 2 KR cần sửa trước khi tiếp tục | 2 KRs need fixing before you continue |
| thiếu target | missing target |
| trùng nội dung với KR 3.2 | duplicates KR 3.2 |
| Không lưu được nháp (mất kết nối). Đang thử lại… Thay đổi vẫn giữ trên trình duyệt. | Couldn't save draft (offline). Retrying… Changes are kept in this browser. |
| 6 Objective, 19 KR — nhiều khả năng quá tải (260h khả dụng). Cân nhắc giữ ≤ 5 Objective. | 6 Objectives, 19 KRs — likely to overload (260h available). Consider ≤ 5 Objectives. |
| Bạn đang sửa kế hoạch đã có. Chỉ KR thay đổi mới được AI sinh lại task; task đã xong hoặc đã ghim được giữ nguyên. | You're editing an existing plan. Only changed KRs get regenerated; done or pinned tasks are kept. |

### S3 — Câu hỏi làm rõ

| vi | en |
|---|---|
| Chọn quý | Quarter |
| Nhập OKR | OKRs |
| Làm rõ | Clarify |
| Sinh kế hoạch | Generate |
| Kế hoạch | Plan |
| AI cần làm rõ 3 điểm | The AI needs 3 clarifications |
| Trả lời để kế hoạch sát thực tế hơn. AI sẽ không tự bịa số liệu. | Answer so the plan fits reality. The AI won't invent numbers. |
| 1/3 đã trả lời | 1/3 answered |
| Vòng 1/2 | Round 1/2 |
| Sửa | Edit |
| WAU 800 được đo bằng công cụ nào, và 2.000 là WAU trung bình 4 tuần cuối quý hay chỉ một tuần? | Which tool measures the 800 WAU, and is 2,000 the average of the last 4 weeks or a single week? |
| Firebase Analytics; trung bình 4 tuần cuối quý. | Firebase Analytics; average of the last 4 weeks. |
| Bắt buộc | Required |
| "Dưới 1%" tính theo phiên hay theo người dùng? Áp dụng cho iOS, Android hay cả hai? | Is "under 1%" per session or per user? iOS, Android or both? |
| Vì sao hỏi: KR 1.3 chưa có target và cách đo, nên AI không thể lập task đo lường. | Why: KR 1.3 has no target or measurement, so the AI can't plan measurement tasks. |
| Theo phiên | Per session |
| Theo người dùng | Per user |
| Cả hai nền tảng | Both platforms |
| Nhập câu trả lời… | Type your answer… |
| Sửa thẳng KR 1.3 | Edit KR 1.3 directly |
| Thương hiệu | Brand |
| Không bắt buộc | Optional |
| Blog đăng ở đâu và mỗi bài dài khoảng bao nhiêu từ? | Where will the blog be published and roughly how long is each post? |
| Sửa thẳng Objective | Edit the Objective |
| Bỏ qua câu này | Skip this one |
| Sửa OKR | Edit OKRs |
| Còn 1 câu bắt buộc | 1 required left |
| Gửi câu trả lời → | Submit answers → |
| AI đang đọc OKR của bạn… | The AI is reading your OKRs… |
| 00:18 · Local LLM có thể mất 10–60 giây. | 00:18 · A local LLM may take 10–60 seconds. |
| Hủy | Cancel |
| Không cần làm rõ thêm | No clarification needed |
| Đang chuyển sang sinh kế hoạch sau 3 giây… | Moving to plan generation in 3 seconds… |
| Ở lại sửa OKR | Stay and edit |
| Sinh kế hoạch ngay | Generate now |
| Không kết nối được Local LLM | Can't reach the local LLM |
| connection refused. Kiểm tra Ollama đang chạy. | connection refused. Check that Ollama is running. |
| Ứng dụng không tự chuyển sang OpenAI. Bạn có thể đổi provider trong Cài đặt. | The app won't switch to OpenAI on its own. You can change provider in Settings. |
| Mở Cài đặt AI | Open AI settings |
| Thử lại | Retry |
| AI trả kết quả không hợp lệ | The AI returned an invalid result |
| Đã thử lại 2 lần. Thử model lớn hơn, hoặc chọn OpenAI trong Cài đặt. | Retried twice. Try a larger model, or choose OpenAI in Settings. |

### S4 — Tiến trình sinh kế hoạch

| vi | en |
|---|---|
| Chọn quý | Quarter |
| Nhập OKR | OKRs |
| Làm rõ | Clarify |
| Sinh kế hoạch | Generate |
| Kế hoạch | Plan |
| Kiểm tra OKR | Pre-check OKRs |
| Phân rã theo KR (4/7) | Decompose per KR (4/7) |
| Gộp trùng & phụ thuộc | Dedupe & dependencies |
| Kiểm tra hợp lệ | Validate |
| Xếp lịch (thuật toán, không dùng AI) | Schedule (algorithm, no AI) |
| Đang sinh kế hoạch Q4/2026 | Generating your Q4/2026 plan |
| Đã chạy 01:24 · Local LLM thường mất 1–4 phút. | Elapsed 01:24 · A local LLM usually takes 1–4 minutes. |
| 4/7 KR xong · 27 task · 118h | 4/7 KRs done · 27 tasks · 118h |
| Chậm hơn 60 giây là bình thường với Local LLM. Bạn có thể đóng tab — kế hoạch vẫn chạy và sẽ hiện khi bạn quay lại. | Over 60 seconds is normal for a local LLM. You can close this tab — the job keeps running and will be here when you return. |
| Tên | Name |
| Tiến độ | Progress |
| Kết quả | Result |
| Tăng WAU 800 → 2.000 | Grow WAU 800 → 2,000 |
| 9 task · 38h | 9 tasks · 38h |
| Phát hành v2.0 | Ship v2.0 |
| 6 task · 22h | 6 tasks · 22h |
| Crash 3,2% → <1% | Crash 3.2% → <1% |
| 7 task · 30h | 7 tasks · 30h |
| Hoàn thành bài 6→25 Minna | Finish Minna lessons 6→25 |
| 5 task · 28h | 5 tasks · 28h |
| Đề thi thử N4 40% → 70% | N4 mock exam 40% → 70% |
| Viết 6 bài blog | Write 6 blog posts |
| Thử lại 1/2 | Retry 1/2 |
| Trình bày tại 1 meetup | Speak at 1 meetup |
| Đang chờ | Queued |
| Hủy sinh kế hoạch | Cancel generation |
| Tự chuyển sang kế hoạch khi xong | Opens the plan automatically when done |
| KR 3.1 chưa sinh được task | KR 3.1 has no tasks yet |
| Model trả JSON không hợp lệ sau 2 lần thử. Các KR khác vẫn tiếp tục. | Invalid JSON after 2 retries. Other KRs continue. |
| Bỏ qua KR này | Skip this KR |
| Thử lại KR 3.1 | Retry KR 3.1 |
| Mất kết nối Local LLM ở KR 2.2 | Lost the local LLM at KR 2.2 |
| 4 KR đã xong được giữ lại. Ứng dụng không tự chuyển sang OpenAI. | The 4 finished KRs are kept. The app won't switch to OpenAI on its own. |
| Mở Cài đặt AI | Open AI settings |
| Tiếp tục từ KR 2.2 | Resume from KR 2.2 |
| Đã sinh 42 task · 318h | Generated 42 tasks · 318h |
| Đang mở kế hoạch… Lịch cho thấy quá tải 58h, xem panel cảnh báo. | Opening your plan… The schedule is 58h over capacity — see the feasibility panel. |
| Hủy sinh kế hoạch? | Cancel generation? |
| 4 KR đã xong sẽ được giữ lại, bạn có thể tiếp tục sau. | The 4 finished KRs are kept; you can resume later. |
| Tiếp tục chạy | Keep running |
| Hủy | Cancel |

### S5 — Danh sách task phân cấp Objective → KR → Task

| vi | en |
|---|---|
| Kế hoạch Q4/2026 | Q4/2026 plan |
| 2 Objective · 5 KR · 50 task · 212h · sinh bởi Local · qwen2.5:7b lúc 23:52 | 2 Objectives · 5 KRs · 50 tasks · 212h · generated by Local · qwen2.5:7b at 23:52 |
| Danh sách | List |
| Lịch tuần | Week |
| Tìm task… | Search tasks… |
| Tất cả Objective | All Objectives |
| Mở rộng tất cả | Expand all |
| Tên | Name |
| Giờ | Hrs |
| Bắt đầu | Start |
| Kết thúc | End |
| Phụ thuộc | Depends on |
| Ra mắt v2.0 ứng dụng đọc sách | Launch v2.0 of the reading app |
| Cao | High |
| Tăng WAU | Grow WAU |
| Số đo 800 → 2.000 | Metric 800 → 2,000 |
| Phân tích funnel onboarding hiện tại | Analyse the current onboarding funnel |
| Thiết kế lại onboarding 3 bước | Redesign the 3-step onboarding |
| Triển khai nhắc đọc hằng ngày | Ship the daily reading reminder |
| + 6 task khác | + 6 more tasks |
| Phát hành v2.0 lên App Store | Ship v2.0 to the App Store |
| Giảm crash | Reduce crashes |
| Số đo 3,2% → 1% | Metric 3.2% → 1% |
| Đạt JLPT N4 | Pass JLPT N4 |
| TB | Med |
| Ước lượng | Estimate |
| Mô tả | Description |
| Rút onboarding từ 5 xuống 3 bước, giữ bước chọn thể loại sách yêu thích. | Cut onboarding from 5 to 3 steps, keeping the favourite-genre step. |
| Tiêu chí hoàn thành | Done criteria |
| Wireframe 3 bước được duyệt | 3-step wireframe approved |
| Prototype test với 3 người | Prototype tested with 3 people |
| Phụ thuộc | Dependencies |
| Phân tích funnel onboarding — xong 01/10 | Analyse onboarding funnel — ends Oct 1 |
| Chặn: | Blocks: |
| Phân bổ theo ngày | Per-day allocation |
| T6 02/10 | Fri Oct 2 |
| T2 05/10 | Mon Oct 5 |
| Sửa, dời, ghim task có ở đợt 2 (S10). | Edit, move and pin arrive in wave 2 (S10). |
| Khả thi | Feasible |
| Tuần | Week |
| Ra mắt v2.0 | Launch v2.0 |
| Chưa có task nào trong Q4/2026 | No tasks in Q4/2026 yet |
| Nhập OKR, AI sẽ phân rã thành các task khoảng 4 giờ và xếp vào lịch. | Enter your OKRs; the AI breaks them into ~4-hour tasks and schedules them. |
| Nhập OKR | Enter OKRs |
| Không tải được kế hoạch | Couldn't load the plan |
| Kiểm tra kết nối tới máy chủ rồi thử lại. | Check the server connection and retry. |
| Thử lại | Retry |
| 15 task (58h) không kịp trước 31/12/2026 | 15 tasks (58h) don't fit before Dec 31, 2026 |
| Thuộc KR 3.1 và KR 3.2 (Objective ưu tiên thấp). Xem panel khả thi. | From KR 3.1 and KR 3.2 (low-priority Objective). See the feasibility panel. |
| Viết bài blog #4: kiến trúc offline | Blog post #4: offline architecture |
| Trong buffer | In buffer |
| Viết bài blog #5: đo lường WAU | Blog post #5: measuring WAU |
| Không kịp | Won't fit |
| Soạn slide meetup | Draft meetup slides |

### S6 — Lịch tuần

| vi | en |
|---|---|
| Lịch tuần | Week |
| Tuần 41 · 05/10 – 11/10/2026 · 20/20h đã xếp | Week 41 · Oct 5 – 11, 2026 · 20/20h scheduled |
| Tuần này | This week |
| Danh sách | List |
| T2 05 | Mon 5 |
| T3 06 | Tue 6 |
| T4 07 | Wed 7 |
| T5 08 | Thu 8 |
| T6 09 | Fri 9 |
| T7 10 | Sat 10 |
| Nghỉ | Off |
| CN 11 | Sun 11 |
| Thiết kế lại onboarding (2/2) | Redesign onboarding (2/2) |
| A/B test màn chào | A/B test welcome screen |
| Triển khai nhắc đọc hằng ngày | Ship the daily reading reminder |
| ← chờ T1.1.2 xong (T2) | ← waits for T1.1.2 (Mon) |
| Thiết lập dashboard WAU | Set up WAU dashboard |
| Chiến dịch email kích hoạt lại | Re-activation email campaign |
| Khảo sát người dùng rời bỏ | Churned-user survey |
| Ngày nghỉ | Day off |
| Buffer 10% (từ 23/12) | 10% buffer (from Dec 23) |
| "(1/2)" = task trải nhiều ngày | "(1/2)" = multi-day task |
| Khả thi | Feasible |
| Cần 212h / Có 260h (82%). Dự kiến xong 15/12/2026, còn 48h dự phòng. | Needs 212h / Has 260h (82%). Expected finish Dec 15, 2026, 48h to spare. |
| ▲ 90% = bắt đầu buffer | ▲ 90% = buffer starts |
| Đã xếp | Scheduled |
| Task | Tasks |
| Tuần 41 | Week 41 |
| T2 | Mo |
| T3 | Tu |
| T4 | We |
| T5 | Th |
| T6 | Fr |
| T7 | Sa |
| CN | Su |
| Thứ 4, 07/10 | Wednesday, Oct 7 |
| Tiêu chí: dashboard hiển thị WAU 4 tuần | Criteria: dashboard shows 4-week WAU |
| Vuốt trái/phải để đổi ngày. | Swipe left/right to change day. |
| Tuần 52 không có task | No tasks in week 52 |
| Đây là vùng buffer cuối quý. Task cuối cùng kết thúc 15/12. | This is the end-of-quarter buffer. The last task ends Dec 15. |
| Tới task cuối | Go to last task |
| Không tải được lịch | Couldn't load the calendar |
| Thử lại | Retry |
| 15 task (58h) không xếp được trước 31/12. | 15 tasks (58h) couldn't be scheduled before Dec 31. |
| Xem chi tiết | Details |
| T2 28 | Mon 28 |
| 4/4h · buffer | 4/4h · buffer |
| T3 29 | Tue 29 |
| T4 30 | Wed 30 |
| T5 31 | Thu 31 |
| 4/4h · hết quý | 4/4h · quarter end |
| Blog #4 (2/2) | Blog #4 (2/2) |
| Biên tập blog #4 | Edit blog #4 |
| Dàn ý blog #5 | Outline blog #5 |
| Số liệu cho blog #5 | Data for blog #5 |

### S7 — Panel cảnh báo khả thi (cơ bản)

| vi | en |
|---|---|
| Khả thi | Feasible |
| Kế hoạch vừa trong quý, chưa cần dùng buffer. | The plan fits the quarter without using the buffer. |
| Cần | Need |
| Có | Have |
| Sử dụng | Used |
| Dự kiến xong: 15/12/2026 | Expected finish: Dec 15, 2026 |
| Buffer ≈10% cuối quý (28h, từ 23/12) được giữ trống để hấp thụ trễ. | The ≈10% end-of-quarter buffer (28h, from Dec 23) stays free to absorb slips. |
| Sát – đang dùng buffer | Tight – using buffer |
| Kịp trong quý nhưng đã dùng 18h trong 28h buffer. | Fits the quarter but uses 18h of the 28h buffer. |
| Dự kiến xong: 29/12/2026 · 5 task nằm trong buffer | Expected finish: Dec 29, 2026 · 5 tasks in buffer |
| Gợi ý | Suggestions |
| Tăng giờ/ngày trong Cài đặt → | Increase hours/day in Settings → |
| Sửa OKR để giảm phạm vi → | Edit OKRs to cut scope → |
| Quá tải | Overloaded |
| Thiếu 58 giờ để kịp trước 31/12/2026. | 58 hours short of finishing by Dec 31, 2026. |
| Thiếu | Short |
| 15 task không xếp được | 15 tasks not scheduled |
| 7 task · 28h | 7 tasks · 28h |
| 8 task · 30h | 8 tasks · 30h |
| Bạn có thể | You can |
| Tăng giờ/ngày hoặc bật Thứ 7 trong Cài đặt → | Add hours/day or enable Saturdays in Settings → |
| Sửa OKR: bỏ hoặc thu nhỏ KR ưu tiên thấp → | Edit OKRs: drop or shrink low-priority KRs → |
| Xem phương án có số liệu (đợt 2) | See quantified options (wave 2) |
| Đang tính khả thi… | Checking feasibility… |
| Không tính được khả thi. | Couldn't compute feasibility. |
| Thử lại | Retry |
| Chưa có kế hoạch — khả thi sẽ hiện sau khi sinh task. | No plan yet — feasibility appears after tasks are generated. |
| Kế hoạch Q4/2026 | Q4/2026 plan |
| Quá tải — thiếu 58h | Overloaded — 58h short |
| Task trễ | Late tasks |
| Mở Cài đặt lịch | Open calendar settings |
| Sửa OKR | Edit OKRs |

### S8 — Cài đặt: Lịch làm việc & AI (LLM)

| vi | en |
|---|---|
| Cài đặt | Settings |
| Áp dụng cho mọi quý (có thể ghi đè theo quý ở đợt 2). | Applies to all quarters (per-quarter overrides in wave 2). |
| Lịch làm việc | Work calendar |
| AI (LLM) | AI (LLM) |
| Giờ làm việc mỗi ngày | Hours per day |
| Thứ | Day |
| Làm việc | Working |
| Giờ/ngày | Hours/day |
| Thứ 2 | Monday |
| Thứ 3 | Tuesday |
| Thứ 4 | Wednesday |
| Thứ 5 | Thursday |
| Thứ 6 | Friday |
| Thứ 7 | Saturday |
| Đã đổi | Changed |
| Chủ nhật | Sunday |
| Không làm | Off |
| Bước 0,5h, tối đa 12h/ngày. 24h/tuần. | 0.5h steps, max 12h/day. 24h/week. |
| Làm việc vào ngày lễ | Work on public holidays |
| Q4/2026: 1 ngày lễ (24/11) · Q1/2027: 8 ngày (Tết Dương lịch + Tết Nguyên đán, dự kiến). Danh sách lễ chỉnh ở đợt 2. | Q4/2026: 1 holiday (Nov 24) · Q1/2027: 8 days (New Year + Lunar New Year, provisional). Holiday list editing in wave 2. |
| Buffer cuối quý | End-of-quarter buffer |
| 10% quỹ giờ cuối quý được giữ trống. | 10% of hours at quarter-end stay free. |
| Giờ khả dụng Q4/2026 | Q4/2026 available hours |
| Trạng thái | Status |
| Thiếu 58h | 58h short |
| Thiếu 6h | 6h short |
| Tính bằng scheduler, không tốn AI. | Computed by the scheduler, no AI cost. |
| 1 thay đổi chưa lưu | 1 unsaved change |
| Hủy thay đổi | Discard |
| Lưu & xếp lại lịch | Save & reschedule |
| Nhà cung cấp AI | AI provider |
| Dùng để hỏi lại, phân rã task và gộp trùng. Xếp lịch luôn chạy bằng thuật toán, không cần AI. | Used for clarifying, task breakdown and dedupe. Scheduling is always algorithmic. |
| Local LLM | Local LLM |
| Khuyến nghị cho OKR nhạy cảm | Recommended for sensitive OKRs |
| Ollama / LM Studio / vLLM · Dữ liệu không rời máy · 0 USD · có thể chậm (1–4 phút/kế hoạch) | Ollama / LM Studio / vLLM · Data stays on your machine · $0 · can be slow (1–4 min/plan) |
| Nhanh, ổn định · ~0,03–0,45 USD/kế hoạch · Nội dung OKR được gửi tới OpenAI | Fast, consistent · ~$0.03–0.45/plan · OKR content is sent to OpenAI |
| Endpoint tương thích OpenAI (/v1/chat/completions). | OpenAI-compatible endpoint (/v1/chat/completions). |
| Danh sách lấy từ máy chủ sau khi kiểm tra kết nối. | Listed from the server after a connection test. |
| Kiểm tra kết nối | Test connection |
| Kết nối OK · qwen2.5:7b-instruct · 1,8s · JSON schema: đạt | Connected · qwen2.5:7b-instruct · 1.8s · JSON schema: pass |
| Không tự chuyển sang OpenAI | No automatic switch to OpenAI |
| Nếu Local LLM lỗi hoặc chậm, ứng dụng sẽ báo lỗi và dừng — không tự gửi dữ liệu sang OpenAI. Bạn tự đổi provider ở đây nếu muốn. | If the local LLM fails or is slow, the app reports it and stops — it never sends your data to OpenAI on its own. Switch provider here if you want to. |
| Lưu cài đặt AI | Save AI settings |
| Lịch | Calendar |
| Thứ 2 – Thứ 6 | Mon – Fri |
| Chỉnh từng thứ ▾ | Per weekday ▾ |
| Ngày lễ | Holidays |
| Q4: 1 ngày | Q4: 1 day |
| XEM TRƯỚC | PREVIEW |
| Thiếu 58h → 6h | 58h → 6h short |
| Hủy | Discard |
| Lưu & xếp lại | Save & reschedule |
| Dữ liệu không rời máy · 0 USD | Data stays local · $0 |
| Nhanh · có phí · dữ liệu gửi tới OpenAI | Fast · paid · data sent to OpenAI |
| Thay | Replace |
| Key lưu phía máy chủ, không hiển thị lại đầy đủ. | Stored server-side, never shown in full again. |
| gpt-…-mini (tầng mini) | gpt-…-mini (mini tier) |
| 401 — API key không hợp lệ hoặc đã bị thu hồi. | 401 — API key is invalid or revoked. |
| Gửi nội dung OKR tới OpenAI? | Send OKR content to OpenAI? |
| Từ giờ, Objective, KR, ngữ cảnh và câu trả lời làm rõ sẽ được gửi tới OpenAI để sinh kế hoạch. Không gửi mật khẩu hay thông tin định danh. Xem Chính sách dữ liệu. | From now on, Objectives, KRs, context and clarification answers are sent to OpenAI to generate plans. No password or identifying data is sent. See the Data policy. |
| Giữ Local | Keep Local |
| Đồng ý, dùng OpenAI | Agree, use OpenAI |
| Đang kiểm tra… (gửi 1 prompt nhỏ) | Testing… (sending one tiny prompt) |
| Không kết nối được | Can't connect |
| tại | at |
| Kiểm tra Ollama đang chạy (ollama serve). | Check Ollama is running (ollama serve). |
| Chưa có model | Model not found |
| Chạy: ollama pull qwen2.5:7b | Run: ollama pull qwen2.5:7b |
| Model trả sai JSON schema | Model failed the JSON schema |
| nên chọn model lớn hơn. | consider a larger model. |
| Chưa cấu hình AI | AI not configured |
| không tìm thấy Ollama trên máy. Chọn provider và kiểm tra kết nối trước khi sinh kế hoạch. | no Ollama found locally. Pick a provider and test it before generating a plan. |
| Không lưu được cài đặt. Thay đổi vẫn còn trên form. | Couldn't save settings. Your changes are still in the form. |
| Thử lại | Retry |

## Đợt 2 — hoàn thiện giai đoạn 1

### S10 — Sửa, thêm, xóa, dời, ghim task & xếp lại lịch

| vi | en |
|---|---|
| Kế hoạch Q4/2026 | Q4/2026 plan |
| 2 Objective · 5 KR · 50 task · 214h · 4/50 task đã xong | 2 Objectives · 5 KRs · 50 tasks · 214h · 4/50 tasks done |
| 2 thay đổi chưa xếp lại | 2 changes not rescheduled |
| Hoàn tác tất cả | Undo all |
| Xếp lại lịch | Reschedule |
| Danh sách | List |
| Lịch tuần | Week |
| Tìm task… | Search tasks… |
| Tất cả Objective | All Objectives |
| Mọi trạng thái | Any status |
| Thêm task | Add task |
| Tên | Name |
| Giờ | Hrs |
| Bắt đầu | Start |
| Kết thúc | End |
| Phụ thuộc | Depends |
| Trạng thái | Status |
| Ra mắt v2.0 ứng dụng đọc sách | Launch v2.0 of the reading app |
| Tăng WAU 800 → 2.000 | Grow WAU 800 → 2,000 |
| 4/9 xong | 4/9 done |
| Phân tích funnel onboarding hiện tại | Analyse the current onboarding funnel |
| Xong | Done |
| Thiết kế lại onboarding 3 bước | Redesign the 3-step onboarding |
| A/B test màn chào | A/B test welcome screen |
| Triển khai nhắc đọc hằng ngày | Ship the daily reading reminder |
| Thiết lập dashboard WAU | Set up WAU dashboard |
| Hôm nay | Today |
| Chiến dịch email kích hoạt lại | Re-activation email campaign |
| Đã sửa: 4h → 6h | Edited: 4h → 6h |
| Khảo sát người dùng rời bỏ | Churned-user survey |
| Ghim · 09/10 | Pinned · Oct 9 |
| Mới | New |
| Push thông báo cá nhân hóa | Personalised push notifications |
| + 1 task khác · + Thêm task vào KR 1.1 | + 1 more task · + Add task to KR 1.1 |
| Phát hành v2.0 lên App Store | Ship v2.0 to the App Store |
| Giảm crash 3,2% → 1% | Reduce crashes 3.2% → 1% |
| Đạt JLPT N4 | Pass JLPT N4 |
| Sửa… | Edit… |
| Dời sang ngày… | Move to date… |
| Ghim vào ngày hiện tại | Pin to current date |
| Đánh dấu hoàn thành | Mark as done |
| Nhân bản | Duplicate |
| Xóa task | Delete task |
| Sửa task | Edit task |
| Tên task | Task name |
| Ước lượng (giờ) | Estimate (hours) |
| 2–6h. Lớn hơn thì tách task. | 2–6h. Split anything larger. |
| Hoàn thành | Done |
| Đánh dấu đã xong | Mark as done |
| Tiêu chí hoàn thành | Done criteria |
| Gửi 3 email cho nhóm không hoạt động 14 ngày | Send 3 emails to users inactive for 14 days |
| Đo tỉ lệ quay lại sau 7 ngày | Measure 7-day return rate |
| Thêm tiêu chí | Add criterion |
| Phụ thuộc | Depends on |
| Dashboard WAU | WAU dashboard |
| + chọn task… | + pick a task… |
| Ghim vào ngày | Pin to date |
| Task ghim không bị scheduler dời. Nếu ngày ghim bị đầy, bạn sẽ được hỏi trước khi xếp lại. | Pinned tasks are never moved by the scheduler. If the pinned day overflows you'll be asked before rescheduling. |
| Lưu chỉ ghi nhận thay đổi. Ngày của các task khác cập nhật khi bạn bấm "Xếp lại lịch". | Saving only records the change. Other tasks' dates update when you click "Reschedule". |
| Hủy | Cancel |
| Lưu thay đổi | Save changes |
| 1 task ghim bị xung đột | 1 pinned task has a conflict |
| Chọn cách xử lý cho từng task. Không có gì thay đổi cho tới khi bạn xác nhận. | Choose how to handle each task. Nothing changes until you confirm. |
| Ghim · T6 09/10 | Pinned · Fri Oct 9 |
| T6 09/10 cần 6h nhưng chỉ có 4h — vì "Chiến dịch email" tăng 4h → 6h và tràn sang ngày này. | Fri Oct 9 needs 6h but has 4h — "Email campaign" grew 4h → 6h and spills into this day. |
| Giữ ghim | Keep pin |
| phần còn lại của "Chiến dịch email" (2h) dời sang T2 12/10 | the remaining 2h of "Email campaign" moves to Mon Oct 12 |
| Bỏ ghim & xếp tự động | Unpin & auto-schedule |
| khảo sát thành 09/10 (2h) + 12/10 (2h) | survey becomes Oct 9 (2h) + Oct 12 (2h) |
| Tiếp tục xem trước | Continue to preview |
| Xếp lại lịch: 44 task đổi ngày | Reschedule: 44 tasks change dates |
| Vẫn khả thi | Still feasible |
| Cần 212h → 214h · Dự kiến xong 15/12 → 16/12 · Task ghim giữ nguyên | Needs 212h → 214h · Finish Dec 15 → Dec 16 · Pinned tasks unchanged |
| Trước | Before |
| Sau | After |
| Chiến dịch email kích hoạt lại (6h) | Re-activation email campaign (6h) |
| + 36 task khác, mỗi task dời tối đa 1 ngày | + 36 other tasks, each moves ≤ 1 day |
| Xem tất cả | Show all |
| Quay lại | Back |
| Áp dụng lịch mới | Apply new schedule |
| T2 05 | Mon 5 |
| T3 06 | Tue 6 |
| T4 07 | Wed 7 |
| T5 08 | Thu 8 |
| T6 09 | Fri 9 |
| A/B test màn chào | A/B test welcome |
| Nhắc đọc hằng ngày | Daily reminder |
| Chiến dịch email | Email campaign |
| Ghim · 4h | Pinned · 4h |
| Đã dời "Khảo sát" sang T5 08/10 và ghim. Ngày này đang vượt 4h. | Moved "Survey" to Thu Oct 8 and pinned it. That day is 4h over. |
| Hoàn tác | Undo |
| Xếp lại ngay | Reschedule now |
| Xóa "Thiết lập dashboard WAU"? | Delete "Set up WAU dashboard"? |
| 1 task đang phụ thuộc vào task này: "Báo cáo WAU 4 tuần" (4h). | 1 task depends on it: "4-week WAU report" (4h). |
| Chỉ xóa task này, bỏ liên kết phụ thuộc | Delete only this task, remove the link |
| Xóa cả task phụ thuộc (tổng 8h) | Also delete the dependent task (8h total) |
| Xóa | Delete |
| Đã xóa "Push thông báo cá nhân hóa" · 3 thay đổi chưa xếp lại | Deleted "Personalised push notifications" · 3 changes pending |
| Tạo vòng lặp: T1.1.6 → T1.1.8 → T1.1.6. Chọn task khác. | Creates a cycle: T1.1.6 → T1.1.8 → T1.1.6. Pick another task. |
| Tối đa 6h. | Max 6h. |
| Tách thành 2 task (5h + 4h) | Split into 2 tasks (5h + 4h) |
| Báo cáo WAU 4 tuần | 4-week WAU report |
| Ghim · T4 07/10 | Pinned · Wed Oct 7 |
| Phụ thuộc "Dashboard WAU" xong 07/10 → sớm nhất 08/10 (quy tắc D+1). | Depends on "WAU dashboard" ending Oct 7 → earliest Oct 8 (D+1 rule). |
| Dời ghim sang T5 08/10 | Move pin to Thu Oct 8 |
| Bỏ liên kết phụ thuộc, giữ 07/10 | Remove the dependency, keep Oct 7 |
| Đang xếp lại… | Rescheduling… |
| Scheduler, không dùng AI · thường < 2 giây | Scheduler, no AI · usually < 2 s |
| Xếp lại thất bại | Rescheduling failed |
| Máy chủ không phản hồi. Lịch cũ được giữ nguyên, 2 thay đổi của bạn vẫn còn. | Server didn't respond. The old schedule is kept and your 2 changes are still there. |
| Thử lại | Retry |
| Sau khi xếp lại: thiếu 6h | After rescheduling: 6h short |
| Bạn đã thêm 9 task (+54h) → Cần 266h / Có 260h. 2 task không kịp trước 31/12. | You added 9 tasks (+54h) → Needs 266h / Has 260h. 2 tasks don't fit before Dec 31. |
| Xem phương án → | See options → |
| KR 2.3 chưa có task | KR 2.3 has no tasks |
| Thêm thủ công hoặc để AI sinh task cho riêng KR này. | Add tasks manually or let the AI generate tasks for this KR only. |
| Sinh task bằng AI | Generate with AI |
| Đã sửa | Edited |
| Sửa chi tiết | Edit details |
| Ghim ngày 08/10 | Pin to Oct 8 |
| Đóng | Close |
| thay đổi chưa xếp lại | changes pending |
| Xếp lại | Reschedule |

### S11 — Lịch tháng

| vi | en |
|---|---|
| Tháng 10/2026 | October 2026 |
| 22 ngày làm việc · 88/88h đã xếp · 22 task | 22 workdays · 88/88h scheduled · 22 tasks |
| Tuần | Week |
| Tháng | Month |
| Tháng này | This month |
| T2 | Mon |
| T3 | Tue |
| T4 | Wed |
| T5 | Thu |
| T6 | Fri |
| T7 | Sat |
| CN | Sun |
| Phân tích funnel | Funnel analysis |
| Thiết kế onboarding (1/2) | Redesign onboarding (1/2) |
| Thiết kế onboarding (2/2) | Redesign onboarding (2/2) |
| A/B test màn chào | A/B test welcome |
| Nhắc đọc hằng ngày | Daily reading reminder |
| Dashboard WAU | WAU dashboard |
| Chiến dịch email | Email campaign |
| Khảo sát rời bỏ | Churn survey |
| Push cá nhân hóa | Personalised push |
| Tối ưu tốc độ mở app (1/2) | App start-up speed (1/2) |
| Tối ưu tốc độ (2/2) | Start-up speed (2/2) |
| Chốt tính năng v2.0 | Feature freeze v2.0 |
| Kiểm thử hồi quy | Regression testing |
| Sửa lỗi beta | Fix beta bugs |
| Ảnh chụp App Store | App Store screenshots |
| Mô tả & từ khóa ASO | ASO copy & keywords |
| Gửi duyệt App Store | Submit to App Store |
| Mốc KR 1.2 | KR 1.2 milestone |
| Tích hợp Crashlytics | Integrate Crashlytics |
| Phân loại top 10 crash | Triage top 10 crashes |
| Sửa crash #1–3 | Fix crashes #1–3 |
| Sửa crash #4–6 | Fix crashes #4–6 |
| Sửa crash #7–10 | Fix crashes #7–10 |
| Kiểm thử máy đời cũ | Test on older devices |
| Theo dõi crash sau vá (1/2) | Monitor crashes post-fix (1/2) |
| Ngày nghỉ | Day off |
| Ngày lễ | Holiday |
| Nghỉ phép | Leave |
| Mốc KR | KR milestone |
| Thứ 4, 21/10/2026 | Wednesday, Oct 21, 2026 |
| 4/4h đã xếp | 4/4h scheduled |
| Hoàn thành task này = đạt KR 1.2 "Phát hành v2.0" | Finishing this task = KR 1.2 "Ship v2.0" achieved |
| Mở chi tiết | Open details |
| Xem tuần 43 | View week 43 |
| T2 | M |
| T3 | T |
| T4 | W |
| T5 | T |
| T6 | F |
| T7 | S |
| CN | S |
| Thứ 4, 21/10 | Wednesday, Oct 21 |
| Luyện nghe N4 | N4 listening |
| Ngày Văn hóa Việt Nam | Vietnamese Culture Day |
| Lễ · 0h | Holiday · 0h |
| Đề thi thử #3 | Mock exam #3 |
| 0h · ví dụ | 0h · example |
| Ôn Kanji bài 16–18 | Kanji lessons 16–18 |
| Ô lễ/nghỉ phép ghi rõ tên + "0h", không chỉ tô màu. | Holiday/leave cells state the name + "0h", not colour alone. |
| 15 task (58h) không xếp được trong quý. | 15 tasks (58h) don't fit in the quarter. |
| Xem phương án → | See options → |
| Blog #4 (2/2) | Blog #4 (2/2) |
| Biên tập blog #4 | Edit blog #4 |
| Dàn ý blog #5 | Outline blog #5 |
| Số liệu cho blog #5 | Data for blog #5 |
| Chưa xếp (15) | Unscheduled (15) |
| Blog #5: đo lường WAU | Blog #5: measuring WAU |
| Soạn slide meetup | Draft meetup slides |
| + 13 task · kéo vào ngày để ghim | + 13 tasks · drag onto a day to pin |
| Tháng 1/2027 chưa có task | No tasks in January 2027 |
| Tháng này thuộc Q1/2027. 1 KR đã được dời sang đây từ Q4/2026. | This month belongs to Q1/2027. 1 KR was moved here from Q4/2026. |
| Lập kế hoạch Q1/2027 | Plan Q1/2027 |
| Không tải được lịch tháng | Couldn't load the month |
| Thử lại | Retry |

### S12 — Dashboard workload & mốc KR

| vi | en |
|---|---|
| Cập nhật sau lần xếp lịch gần nhất · 07/10 09:12 | Updated after the latest scheduling run · Oct 7 09:12 |
| Xuất dữ liệu | Export |
| Cần / Có | Needs / Has |
| Sử dụng 82% · còn 48h | 82% used · 48h spare |
| Dự kiến xong | Expected finish |
| Trước buffer (23/12) 1 tuần | 1 week before buffer (Dec 23) |
| Tuần đầy 100% | Weeks at 100% |
| 11 / 14 tuần | 11 / 14 weeks |
| T40–T50; T51 40%; T52–T53 trống | W40–W50; W51 40%; W52–W53 free |
| Tiến độ thực tế | Actual progress |
| 4/50 task · 16h | 4/50 tasks · 16h |
| Đúng kế hoạch | On plan |
| Giờ theo tuần so với capacity | Hours per week vs capacity |
| Theo tuần | Weekly |
| Theo tháng | Monthly |
| T40 | W40 |
| T41 | W41 |
| T42 | W42 |
| T43 | W43 |
| T44 | W44 |
| T45 | W45 |
| T46 | W46 |
| T47 | W47 |
| T48 · lễ | W48 · hol. |
| T49 | W49 |
| T50 | W50 |
| T51 | W51 |
| T52 | W52 |
| T53 | W53 |
| O1 Ra mắt v2.0 | O1 Launch v2.0 |
| O2 JLPT N4 | O2 JLPT N4 |
| Capacity còn trống | Free capacity |
| Buffer 10% (từ 23/12) | 10% buffer (from Dec 23) |
| % = giờ đã xếp / capacity tuần (T40: 2 ngày, T48: lễ 24/11, T53: 4 ngày) | % = scheduled / weekly capacity (W40: 2 days, W48: Nov 24 holiday, W53: 4 days) |
| Mốc KR dạng số theo tháng | Numeric KR milestones by month |
| Cách tính mốc: | Milestone method: |
| Theo tiến độ task (mặc định) | By task progress (default) |
| Tháng | Month |
| Tuần | Week |
| Cuối T10 | End Oct |
| Cuối T11 | End Nov |
| Cuối T12 (target) | End Dec (target) |
| Thực tế gần nhất | Latest actual |
| WAU | WAU |
| 2.000 | 2,000 |
| Chỉ số trễ | Lagging metric |
| Tỉ lệ crash | Crash rate |
| 3,2% | 3.2% |
| 1,1% | 1.1% |
| 1,0% | 1.0% |
| Nhập… | Enter… |
| Bài Minna đã học | Minna lessons done |
| Điểm thi thử N4 | N4 mock score |
| Phát hành v2.0 | Ship v2.0 |
| Milestone, không phải số | Milestone, not numeric |
| Mốc = mức kỳ vọng nếu task xong đúng lịch, nội suy tuyến tính theo giờ task đã hoàn thành của KR. Không phải dự báo kết quả. | Milestone = expected level if tasks finish on schedule, linearly interpolated by the KR's completed task hours. Not a forecast of results. |
| Cần/Có | Needs/Has |
| Xong dự kiến | Finish |
| Sử dụng | Used |
| Tiến độ | Progress |
| Theo tuần | By week |
| T48 | W48 |
| Mốc KR (cuối T11) | KR milestones (end Nov) |
| Bài Minna | Minna lessons |
| Thi thử N4 | N4 mock |
| T52 · buffer | W52 · buffer |
| T53 · buffer | W53 · buffer |
| Chưa xếp | Unscheduled |
| Buffer bị lấp kín (vẽ đậm hơn) và cột "Chưa xếp 58h" gạch chéo đỏ nằm ngoài trục thời gian. Nút cạnh tiêu đề: "Xem phương án" → S13. | Buffer fully used (drawn darker) and a red hatched "Unscheduled 58h" column outside the timeline. Header button: "See options" → S13. |
| Chưa có dữ liệu | No data yet |
| Tạo kế hoạch để xem workload. | Create a plan to see workload. |
| Không tải được số liệu. | Couldn't load data. |
| Thử lại | Retry |

### S13 — Panel phương án xử lý quá tải

| vi | en |
|---|---|
| Phương án xử lý quá tải | Overload options |
| Hiện tại: Cần 318h / Có 260h · thiếu 58h · 15 task không kịp (KR 3.1, KR 3.2) | Now: Needs 318h / Has 260h · 58h short · 15 tasks don't fit (KR 3.1, KR 3.2) |
| Tăng giờ mỗi ngày (T2–T6) | More hours per weekday (Mon–Fri) |
| +65h trên 65 ngày · +1,5h/ngày thì thành Xanh | +65h over 65 days · +1.5h/day turns it Green |
| Vàng | Amber |
| dùng 28h / 35h buffer | uses 28h / 35h buffer |
| Làm Thứ 7 (4h) | Work Saturdays (4h) |
| 13 ngày Thứ 7 (03/10 → 26/12) · +52h | 13 Saturdays (Oct 3 → Dec 26) · +52h |
| Đỏ | Red |
| một mình: còn thiếu 6h (2 task) | alone: still 6h short (2 tasks) |
| Làm Chủ nhật (4h) | Work Sundays (4h) |
| 13 ngày · +52h · kết hợp với Thứ 7 = +104h → Xanh | 13 days · +52h · with Saturdays = +104h → Green |
| một mình: còn thiếu 6h | alone: still 6h short |
| Làm ngày lễ 24/11 | Work the Nov 24 holiday |
| còn thiếu 54h | still 54h short |
| Bỏ KR 3.2 "Trình bày tại 1 meetup" | Drop KR 3.2 "Speak at 1 meetup" |
| 8 task · −30h · không dùng cùng "Dời KR 3.2" | 8 tasks · −30h · can't combine with "Move KR 3.2" |
| Đỏ · thiếu 28h | Red · 28h short |
| Bỏ cả O3 "Xây dựng thương hiệu cá nhân" | Drop all of O3 "Build a personal brand" |
| 2 KR · 27 task · −106h | 2 KRs · 27 tasks · −106h |
| Xanh | Green |
| xong 15/12 | finish Dec 15 |
| Nhờ AI thu gọn phạm vi O3 | Ask AI to trim O3 scope |
| Gộp/bỏ task phụ, giữ nguyên Objective. Tốn 1 lần gọi Local · qwen2.5:7b (~40 giây). | Merge/drop minor tasks, keep the Objective. Costs 1 call to Local · qwen2.5:7b (~40 s). |
| Chạy đề xuất | Run suggestion |
| chưa chạy | not run yet |
| Dời KR 3.2 sang Q1/2027 | Move KR 3.2 to Q1/2027 |
| 8 task · 30h · thành nháp trong Q1/2027 | 8 tasks · 30h · becomes a draft in Q1/2027 |
| một mình: còn thiếu 28h | alone: still 28h short |
| Dời KR 3.1 sang Q1/2027 | Move KR 3.1 to Q1/2027 |
| 19 task · 76h | 19 tasks · 76h |
| dùng 10h buffer | uses 10h buffer |
| Xem trước: 2 phương án | Preview: 2 options |
| Làm Thứ 7 | Saturdays |
| Dời KR 3.2 | Move KR 3.2 |
| Trước | Before |
| Sau | After |
| Cần | Needs |
| Có | Has |
| Chênh lệch | Balance |
| Trạng thái | Status |
| Dự kiến xong | Finish |
| không kịp | won't fit |
| Task không kịp | Late tasks |
| Mức sử dụng | Utilisation |
| 92% · dùng 8h / 32h buffer | 92% · uses 8h / 32h buffer |
| Sẽ thay đổi | What changes |
| 13 Thứ 7 thành ngày làm việc 4h trong Cài đặt | 13 Saturdays become 4h workdays in Settings |
| KR 3.2 (8 task, 30h) chuyển sang Q1/2027 dạng nháp | KR 3.2 (8 tasks, 30h) moves to Q1/2027 as a draft |
| Task ghim giữ nguyên · không gọi AI | Pinned tasks unchanged · no AI call |
| Áp dụng phương án | Apply options |
| Bỏ chọn tất cả | Clear selection |
| AI đề xuất thu gọn O3: −30h | AI suggests trimming O3: −30h |
| Sinh bởi Local · qwen2.5:7b lúc 30/09 21:40. Bỏ chọn mục bạn không đồng ý. | Generated by Local · qwen2.5:7b on Sep 30 21:40. Untick anything you disagree with. |
| Giảm KR 3.1 từ 6 → 5 bài blog | Reduce KR 3.1 from 6 → 5 blog posts |
| Đổi target KR | Changes KR target |
| Dùng lại slide nội bộ cho meetup | Reuse internal slides for the meetup |
| Bỏ buổi tập dượt lần 2 | Drop the second rehearsal |
| Rút biên tập blog #5, #6 từ 4h → 2h | Cut editing for blog #5, #6 from 4h → 2h |
| Gộp "chọn chủ đề" và "dàn ý" meetup | Merge meetup "pick topic" and "outline" |
| Kết quả nếu áp dụng cả 5: Cần 288h / Có 260h → vẫn Đỏ, thiếu 28h. Có thể kết hợp với phương án khác. | If all 5 applied: Needs 288h / Has 260h → still Red, 28h short. Can be combined with other options. |
| Bỏ qua | Discard |
| Thêm vào lựa chọn (5/5) | Add to selection (5/5) |
| Đang tính 9 phương án (scheduler, không dùng AI)… | Computing 9 options (scheduler, no AI)… |
| Không tính được (Q1/2027 chưa có lịch làm việc). | Couldn't compute (Q1/2027 has no work calendar). |
| Thử lại | Retry |
| AI không phản hồi sau 2 lần thử. Các phương án khác vẫn dùng được. | AI didn't respond after 2 retries. Other options still work. |
| Mở Cài đặt AI | Open AI settings |
| Không cần phương án | No options needed |
| Kế hoạch Q4/2026 đang khả thi, còn 48h dự phòng. | The Q4/2026 plan fits with 48h to spare. |
| Đã áp dụng 2 phương án · Kế hoạch: Sát – dùng buffer | Applied 2 options · Plan: Tight – using buffer |
| Hoàn tác | Undo |
| Phương án | Options |
| Làm Thứ 7 | Work Saturdays |
| thiếu 6h | 6h short |
| Tăng lên 5h/ngày | Raise to 5h/day |
| Bỏ cả O3 | Drop all of O3 |
| thiếu 28h | 28h short |
| + 4 phương án khác | + 4 more options |
| 2 đã chọn · −58h → +24h | 2 selected · −58h → +24h |
| Xem trước & áp dụng | Preview & apply |

### S14 — Quản lý quý: danh sách, xem lại quý cũ, xóa

| vi | en |
|---|---|
| Quản lý quý | Quarters |
| 5 quý · 1 đang diễn ra · 1 nháp | 5 quarters · 1 in progress · 1 draft |
| Lập kế hoạch quý mới | Plan a new quarter |
| Các quý | Quarters |
| Nghỉ phép | Leave |
| Ngày lễ | Holidays |
| Xuất dữ liệu | Export |
| Đang diễn ra | In progress |
| 01/10 – 31/12/2026 · 3 Objective · 69 task | Oct 1 – Dec 31, 2026 · 3 Objectives · 69 tasks |
| Sát – dùng buffer | Tight – using buffer |
| 4/69 task xong | 4/69 tasks done |
| Mở kế hoạch | Open plan |
| Nháp | Draft |
| 01/01 – 31/03/2027 · 8 ngày lễ (Tết dự kiến) | Jan 1 – Mar 31, 2027 · 8 holidays (Tết provisional) |
| 1 KR được dời từ Q4/2026: KR 3.2 "Trình bày tại 1 meetup" (8 task · 30h) | 1 KR moved from Q4/2026: KR 3.2 "Speak at 1 meetup" (8 tasks · 30h) |
| Tiếp tục lập kế hoạch | Continue planning |
| Chưa xem lại | Not reviewed |
| Kết thúc 30/09/2026 · 2 Objective · 36 task | Ended Sep 30, 2026 · 2 Objectives · 36 tasks |
| task xong (29/36) · 3/4 KR đạt | tasks done (29/36) · 3/4 KRs met |
| Xem lại quý | Review quarter |
| Đã xem lại | Reviewed |
| Kết thúc 30/06/2026 · 3 Objective · 44 task | Ended Jun 30, 2026 · 3 Objectives · 44 tasks |
| task xong (38/44) · 4/6 KR đạt | tasks done (38/44) · 4/6 KRs met |
| Xem | View |
| Không có kế hoạch | No plan |
| Quý đã qua, chưa từng lập kế hoạch. | Past quarter, never planned. |
| Sao chép OKR sang quý khác… | Copy OKRs to another quarter… |
| Xuất dữ liệu… | Export… |
| Xóa quý… | Delete quarter… |
| Xem lại Q3/2026 | Q3/2026 review |
| Đánh dấu đã xem lại | Mark as reviewed |
| Chỉ xem — quý đã kết thúc. Ghi kết quả cuối cho từng KR; không thể sửa task hay xếp lại lịch. | Read-only — this quarter has ended. Record the final result for each KR; tasks can't be edited or rescheduled. |
| Task xong | Tasks done |
| Giờ đã làm | Hours done |
| KR đạt | KRs met |
| Task trễ hạn | Late tasks |
| Kết quả cuối | Final result |
| Đánh giá | Outcome |
| Đạt người dùng beta | Beta users |
| Đạt 86% | 86% met |
| Điểm đánh giá beta | Beta rating |
| ≥ 4,5★ | ≥ 4.5★ |
| 4,6★ | 4.6★ |
| Đạt | Met |
| Điểm thi thử N5 | N5 mock score |
| Học xong Minna bài 1–5 | Finish Minna lessons 1–5 |
| Sao chép KR chưa đạt sang Q4/2026… | Copy unmet KRs to Q4/2026… |
| Tạo KR mới ở quý đích; quý này không đổi. | Creates new KRs in the target quarter; this quarter stays unchanged. |
| Xóa Q2/2026? | Delete Q2/2026? |
| Xóa vĩnh viễn 3 Objective, 44 task và kết quả review. Không thể hoàn tác. Nên xuất dữ liệu trước. | Permanently deletes 3 Objectives, 44 tasks and the review. This can't be undone. Export first if you need it. |
| Gõ "Q2/2026" để xác nhận | Type "Q2/2026" to confirm |
| Xuất trước | Export first |
| Hủy | Cancel |
| Xóa vĩnh viễn | Delete permanently |
| Q4/2026 đang diễn ra nên không xóa được. Bạn có thể xóa từng Objective trong Kế hoạch OKR. | Q4/2026 is in progress and can't be deleted. You can delete individual Objectives in OKR plan. |
| Chưa có quý nào | No quarters yet |
| Lập kế hoạch quý đầu tiên để bắt đầu. | Plan your first quarter to get started. |
| Lập kế hoạch | Plan a quarter |
| Không tải được danh sách quý. | Couldn't load quarters. |
| Thử lại | Retry |

### S14B — Nghỉ phép & chỉnh ngày lễ Việt Nam

| vi | en |
|---|---|
| Các quý | Quarters |
| Nghỉ phép | Leave |
| Ngày lễ | Holidays |
| Xuất dữ liệu | Export |
| Thêm nghỉ phép | Add leave |
| Từ ngày | From |
| T6 16/10/2026 | Fri Oct 16, 2026 |
| Đến ngày | To |
| Thời lượng | Duration |
| Cả ngày | Full day |
| Nửa ngày | Half day |
| Ghi chú (không bắt buộc) | Note (optional) |
| VD: Việc gia đình — không cần ghi lý do | e.g. Family matter — no reason needed |
| Tác động nếu lưu | Impact if saved |
| −4h capacity · Dự kiến xong 24/12 → 25/12 · Buffer dùng 8h → 12h (vẫn Vàng) · 1 task dời sang ngày sau | −4h capacity · Finish Dec 24 → Dec 25 · Buffer used 8h → 12h (still Amber) · 1 task moves to a later day |
| Hủy | Cancel |
| Lưu nghỉ phép | Save leave |
| Đã lưu | Saved |
| Ngày | Date |
| Quý | Quarter |
| Ghi chú | Note |
| T2 17/08/2026 | Mon Aug 17, 2026 |
| Cả ngày · 4h | Full day · 4h |
| Q3/2026 · đã qua | Q3/2026 · past |
| Nghỉ phép rơi vào task đã ghim sẽ hỏi giữ/bỏ ghim như S10. | Leave on a pinned task's day triggers the keep/unpin prompt from S10. |
| Khôi phục mặc định | Restore defaults |
| Thêm ngày | Add day |
| Có đề xuất nghỉ dài hơn dịp 24/11/2026 nhưng chưa chính thức — ứng dụng chỉ dùng ngày đã có văn bản. Bạn có thể thêm thủ công. | A longer break around Nov 24, 2026 has been proposed but isn't official — the app only uses dates with a published decision. You can add days manually. |
| Tên | Name |
| Loại | Type |
| Trạng thái | Status |
| Nguồn | Source |
| T5 01/01 | Thu Jan 1 |
| Tết Dương lịch | New Year's Day |
| Nghỉ lễ | Holiday |
| Chính thức | Official |
| T2 16/02 – T6 20/02 | Mon Feb 16 – Fri Feb 20 |
| Tết Nguyên đán (5 ngày) | Lunar New Year (5 days) |
| CN 26/04 | Sun Apr 26 |
| Giỗ Tổ Hùng Vương | Hung Kings' Day |
| Nghỉ lễ (CN) | Holiday (Sun) |
| T2 27/04 | Mon Apr 27 |
| Nghỉ bù Giỗ Tổ | Hung Kings' Day (in lieu) |
| Nghỉ bù | In lieu |
| T5 30/04 – T6 01/05 | Thu Apr 30 – Fri May 1 |
| Chiến thắng · Quốc tế Lao động | Reunification · Labour Day |
| T7 22/08 | Sat Aug 22 |
| Làm bù cho nghỉ 31/08 | Make-up day for Aug 31 |
| Làm bù | Make-up workday |
| T2 31/08 | Mon Aug 31 |
| Nghỉ hoán đổi dịp Quốc khánh | National Day (swapped day off) |
| Nghỉ hoán đổi | Swapped day off |
| T3 01/09 – T4 02/09 | Tue Sep 1 – Wed Sep 2 |
| Quốc khánh | National Day |
| T3 24/11 | Tue Nov 24 |
| Ngày Văn hóa Việt Nam | Vietnamese Culture Day |
| T5 31/12 | Thu Dec 31 |
| Nghỉ cuối năm (tự thêm) | Year-end day off (custom) |
| Nghỉ riêng | Custom day off |
| Chưa lưu | Unsaved |
| Bạn | You |
| Lưu | Save |
| Thêm 31/12: Q4/2026 có 312h → 308h; buffer 32h bắt đầu sớm hơn (22/12), dùng 12h thay vì 8h. Vẫn Vàng, vẫn xong 24/12. Kế hoạch sẽ chuyển sang "Cần xếp lại". | Adding Dec 31: Q4/2026 has 312h → 308h; the 32h buffer starts earlier (Dec 22), 12h used instead of 8h. Still Amber, still finishes Dec 24. The plan becomes "Needs rescheduling". |
| T6 01/01 | Fri Jan 1 |
| T5 04/02 – T2 08/02 | Thu Feb 4 – Mon Feb 8 |
| Tết Nguyên đán | Lunar New Year |
| Dự kiến | Provisional |
| T3 09/02 – T4 10/02 | Tue Feb 9 – Wed Feb 10 |
| Nghỉ bù Tết (mùng 4, 5) | Tết in lieu (days 4, 5) |
| T6 16/04 | Fri Apr 16 |
| T7 01/05 → T2 03/05 | Sat May 1 → Mon May 3 |
| Quốc tế Lao động + nghỉ bù | Labour Day + in lieu |
| T6 03/09 | Fri Sep 3 |
| Quốc khánh (ngày liền kề) | National Day (adjacent day) |
| + 30/04, 02/09, 24/11 (chính thức) | + Apr 30, Sep 2, Nov 24 (official) |
| Ngày dự kiến vẫn được dùng để xếp lịch. Khi dữ liệu mặc định cập nhật khác đi, quý bị ảnh hưởng sẽ hiện pill "Cần xếp lại" kèm lý do. | Provisional dates are still used for scheduling. If the default data changes, affected quarters show a "Needs rescheduling" pill with the reason. |
| Khôi phục ngày lễ 2026 mặc định? | Restore default 2026 holidays? |
| 1 ngày tự thêm (31/12) sẽ bị xóa. Q4/2026 sẽ cần xếp lại. | 1 custom day (Dec 31) will be removed. Q4/2026 will need rescheduling. |
| Khôi phục | Restore |
| T3 24/11/2026 | Tue Nov 24, 2026 |
| Ngày này đã là ngày lễ "Ngày Văn hóa Việt Nam". | This date is already the holiday "Vietnamese Culture Day". |
| Không lưu được. Thay đổi vẫn giữ trong form. | Couldn't save. Your changes are kept in the form. |
| Thử lại | Retry |

### S14C — Xuất CSV/Excel & trang Chính sách dữ liệu

| vi | en |
|---|---|
| Xuất dữ liệu | Export data |
| Quý | Quarter |
| Định dạng | Format |
| 3 sheet: OKR · Task · Lịch theo ngày | 3 sheets: OKR · Tasks · Daily schedule |
| 1 file task, UTF-8 có BOM (Excel mở đúng tiếng Việt) | 1 task file, UTF-8 with BOM (Excel shows Vietnamese correctly) |
| Bao gồm | Include |
| Tiêu chí hoàn thành | Done criteria |
| Phụ thuộc giữa task | Task dependencies |
| Ghi chú nghỉ phép | Leave notes |
| File chứa nội dung OKR của bạn. Không bao giờ chứa mật khẩu hay API key. | The file contains your OKR content. It never includes the password or API key. |
| Hủy | Cancel |
| Tải xuống okr-q4-2026.xlsx | Download okr-q4-2026.xlsx |
| Objective, ưu tiên, KR, loại, baseline, target, kết quả | Objective, priority, KR, type, baseline, target, result |
| Task | Tasks |
| mã, tên, KR, giờ, bắt đầu, kết thúc, phụ thuộc, ghim, trạng thái | code, name, KR, hours, start, end, depends on, pinned, status |
| Lịch theo ngày | Daily schedule |
| ngày, mã task, số giờ, capacity ngày, loại ngày (làm/nghỉ/lễ/buffer) | date, task code, hours, day capacity, day type (work/off/holiday/buffer) |
| Ngày dạng ISO (2026-10-07) để máy đọc; tên cột theo ngôn ngữ đang chọn. | ISO dates (2026-10-07) for machines; column names follow the current language. |
| Đang tạo file… | Creating file… |
| Không tạo được file. Thử lại hoặc chọn CSV. | Couldn't create the file. Retry or choose CSV. |
| Thử lại | Retry |
| Tải xuống | Download |
| Q1/2026 không có dữ liệu để xuất. | Q1/2026 has no data to export. |
| Chính sách dữ liệu | Data policy |
| Tóm tắt dễ đọc · cập nhật 30/09/2026 | Plain-language summary · updated Sep 30, 2026 |
| Bạn đang dùng AI cục bộ (Local · qwen2.5:7b) | You're using a local AI (Local · qwen2.5:7b) |
| Nội dung OKR được gửi tới | OKR content is sent to |
| — chạy trên máy chủ của bạn, không rời khỏi hệ thống. | — it runs on your server and doesn't leave your system. |
| Đổi trong Cài đặt | Change in Settings |
| Dữ liệu được lưu | What's stored |
| OKR, câu trả lời làm rõ, task, lịch, nghỉ phép, ngày lễ tự thêm | OKRs, clarifying answers, tasks, schedule, leave, custom holidays |
| Cài đặt capacity và AI (API key được mã hóa, chỉ hiện 4 ký tự cuối) | Capacity and AI settings (API key encrypted, only last 4 chars shown) |
| Nhật ký sinh kế hoạch: provider, model, thời điểm — không lưu API key | Generation log: provider, model, time — never the API key |
| Dữ liệu gửi tới AI | What's sent to the AI |
| Nội dung Objective, KR, câu trả lời làm rõ | Objective and KR text, clarifying answers |
| Không gửi: mật khẩu truy cập, nghỉ phép, ghi chú, lịch | Never sent: access password, leave, notes, schedule |
| Lịch và phương án quá tải do scheduler tính trên máy chủ, không cần AI | Schedules and overload options are computed by the scheduler, no AI needed |
| Truy cập | Access |
| Một mật khẩu dùng chung; phiên đăng nhập bằng cookie httpOnly | One shared password; session via httpOnly cookie |
| Ai có mật khẩu đều xem/sửa được mọi quý | Anyone with the password can view/edit all quarters |
| Quyền của bạn | Your controls |
| Xuất toàn bộ dữ liệu (CSV/Excel) bất cứ lúc nào | Export all data (CSV/Excel) at any time |
| Xóa từng quý trong Quản lý quý | Delete individual quarters in Quarters |
| Xuất tất cả | Export all |
| Xóa toàn bộ dữ liệu… | Delete all data… |
| Bạn đang dùng OpenAI (gpt-4o-mini) | You're using OpenAI (gpt-4o-mini) |
| Nội dung Objective, KR và câu trả lời làm rõ được gửi tới api.openai.com và chịu chính sách dữ liệu của OpenAI. Ứng dụng không bao giờ tự chuyển sang OpenAI — bạn đã chọn trong Cài đặt. | Objective, KR and clarifying-answer text is sent to api.openai.com under OpenAI's data policy. The app never switches to OpenAI on its own — you chose it in Settings. |
| Chuyển về Local | Switch back to Local |
| Xóa toàn bộ dữ liệu? | Delete all data? |
| Xóa 4 quý, mọi task, nghỉ phép và ngày lễ tự thêm. Cài đặt AI và mật khẩu giữ nguyên. Không thể hoàn tác. | Deletes 4 quarters, all tasks, leave and custom holidays. AI settings and password stay. Can't be undone. |
| Nhập lại mật khẩu truy cập để xác nhận | Re-enter the access password to confirm |
| Mật khẩu dùng chung, nên yêu cầu nhập lại thay vì chỉ gõ chữ. | The password is shared, so re-entry is required instead of typing a word. |
| Xuất trước | Export first |
| Xóa tất cả | Delete everything |
