# Plan Mc88b — sample 05_payment_reliability_vi

- Pipeline status: `ok`

## Tasks (41 tasks, 148 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 2 | — | Xác định tiêu chí và phạm vi cho uptime | Định nghĩa rõ ràng về uptime, các điểm kiểm tra và thời gian đo lường được ghi lại trong tài liệu. |
| O1-KR1.t2 | O1-KR1 | 3 | O1-KR1.t1 | Lập kế hoạch cải thiện uptime | Kế hoạch cải thiện uptime được lập, bao gồm các nguyên nhân và giải pháp cụ thể. |
| O1-KR1.t3 | O1-KR1 | 3 | O1-KR1.t2 | Kiểm tra hệ thống hiện tại | Kết quả kiểm tra uptime hiện tại được ghi lại và phân tích. |
| O1-KR1.t4 | O1-KR1 | 6 | O1-KR1.t3 | Thực hiện các cải tiến hệ thống | Các giải pháp cải thiện uptime đã được triển khai và ghi lại. |
| O1-KR1.t5 | O1-KR1 | 3 | O1-KR1.t4 | Kiểm tra lại uptime sau cải tiến | Kết quả kiểm tra uptime sau cải tiến được ghi lại và phân tích. |
| O1-KR1.t6 | O1-KR1 | 2 | O1-KR1.t5 | Đo lường uptime cuối kỳ | Kết quả đo lường uptime cuối kỳ được ghi lại và so sánh với mục tiêu 99.9%. |
| O1-KR2.t1 | O1-KR2 | 2 | — | Xác định tiêu chí và phạm vi của độ trễ p95 | Đã xác định rõ p95 và danh sách API liên quan. |
| O1-KR2.t2 | O1-KR2 | 3 | O1-KR2.t1 | Thu thập dữ liệu độ trễ hiện tại | Đã có dữ liệu độ trễ p95 trong 7 ngày qua. |
| O1-KR2.t3 | O1-KR2 | 4 | O1-KR2.t2 | Phân tích nguyên nhân độ trễ p95 | Đã có báo cáo phân tích nguyên nhân độ trễ p95. |
| O1-KR2.t4 | O1-KR2 | 4 | O1-KR2.t3 | Thiết kế giải pháp tối ưu hóa API | Đã có tài liệu thiết kế giải pháp tối ưu hóa API. |
| O1-KR2.t5 | O1-KR2 | 6 | O1-KR2.t4 | Thực hiện tối ưu hóa API | Đã hoàn thành tối ưu hóa toàn bộ API tạo giao dịch. |
| O1-KR2.t6 | O1-KR2 | 3 | O1-KR2.t5 | Kiểm tra độ trễ sau tối ưu hóa | Đã có dữ liệu độ trễ p95 sau tối ưu hóa. |
| O1-KR2.t7 | O1-KR2 | 3 | O1-KR2.t6 | Đo lường kết quả và báo cáo | Đã có báo cáo so sánh độ trễ p95 trước và sau tối ưu hóa. |
| O1-KR3.t1 | O1-KR3 | 2 | — | Xác định tiêu chí và phạm vi cho MTTR | Định nghĩa rõ ràng MTTR và điều kiện đo lường được ghi lại trong tài liệu. |
| O1-KR3.t2 | O1-KR3 | 3 | O1-KR3.t1 | Thu thập dữ liệu MTTR hiện tại | Dữ liệu lịch sử MTTR được thu thập và lưu trữ trong một file CSV. |
| O1-KR3.t3 | O1-KR3 | 4 | O1-KR3.t2 | Phân tích nguyên nhân gây ra MTTR cao | Báo cáo phân tích nguyên nhân được tạo và gửi cho nhóm kỹ thuật. |
| O1-KR3.t4 | O1-KR3 | 4 | O1-KR3.t3 | Thiết kế quy trình khắc phục sự cố nhanh | Quy trình khắc phục sự cố được thiết kế và lưu trữ trong tài liệu. |
| O1-KR3.t5 | O1-KR3 | 4 | O1-KR3.t4 | Thực hiện kiểm thử quy trình khắc phục sự cố | Kết quả kiểm thử được ghi lại và gửi cho nhóm kỹ thuật. |
| O1-KR3.t6 | O1-KR3 | 3 | O1-KR3.t5 | Đánh giá kết quả và điều chỉnh quy trình | Báo cáo đánh giá và điều chỉnh quy trình được gửi cho nhóm kỹ thuật. |
| O1-KR3.t7 | O1-KR3 | 4 | O1-KR3.t6 | Theo dõi và đo lường MTTR trong suốt quý | Kết quả theo dõi MTTR được ghi lại trong bảng theo dõi. |
| O1-KR3.t8 | O1-KR3 | 3 | O1-KR3.t7 | Đánh giá kết quả cuối quý | Báo cáo đánh giá cuối quý được gửi cho quản lý. |
| O2-KR1.t1 | O2-KR1 | 2 | — | Xác định mục tiêu và phạm vi test coverage | Định nghĩa rõ ràng các thành phần cần test và phạm vi test coverage trong tài liệu. |
| O2-KR1.t2 | O2-KR1 | 3 | O2-KR1.t1 | Lên kế hoạch test coverage | Kế hoạch test coverage chi tiết với danh sách module và phân bổ thời gian được ghi lại. |
| O2-KR1.t3 | O2-KR1 | 6 | O2-KR1.t2 | Viết test case cho module 1-5 | Test case cho 5 module đầu tiên được viết và lưu trữ trong repository. |
| O2-KR1.t4 | O2-KR1 | 6 | O2-KR1.t2 | Viết test case cho module 6-10 | Test case cho 5 module tiếp theo được viết và lưu trữ trong repository. |
| O2-KR1.t5 | O2-KR1 | 6 | O2-KR1.t2 | Viết test case cho module 11-15 | Test case cho 5 module cuối cùng được viết và lưu trữ trong repository. |
| O2-KR1.t6 | O2-KR1 | 4 | O2-KR1.t3, O2-KR1.t4, O2-KR1.t5 | Chạy test và kiểm tra kết quả | Kết quả chạy test được ghi lại và test coverage hiện tại được xác định. |
| O2-KR1.t7 | O2-KR1 | 4 | O2-KR1.t6 | Đánh giá và điều chỉnh test case | Test case được điều chỉnh và lưu trữ trong repository. |
| O2-KR1.t8 | O2-KR1 | 6 | O2-KR1.t7 | Viết test case cho module 16-20 | Test case cho 5 module tiếp theo được viết và lưu trữ trong repository. |
| O2-KR1.t9 | O2-KR1 | 6 | O2-KR1.t7 | Viết test case cho module 21-25 | Test case cho 5 module cuối cùng được viết và lưu trữ trong repository. |
| O2-KR1.t10 | O2-KR1 | 4 | O2-KR1.t8, O2-KR1.t9 | Chạy test và kiểm tra kết quả lần nữa | Kết quả chạy test được ghi lại và test coverage hiện tại được xác định. |
| O2-KR1.t11 | O2-KR1 | 4 | O2-KR1.t10 | Đánh giá và điều chỉnh test case lần nữa | Test case được điều chỉnh và lưu trữ trong repository. |
| O2-KR1.t12 | O2-KR1 | 3 | O2-KR1.t11 | Kiểm tra lại test coverage sau khi tăng | Test coverage đạt 75% và được xác nhận bằng công cụ đo lường. |
| O2-KR1.t13 | O2-KR1 | 2 | O2-KR1.t12 | Ghi nhận kết quả và báo cáo | Báo cáo kết quả đạt được và test coverage đạt 75% được gửi cho team. |
| O2-KR2.t1 | O2-KR2 | 3 | — | Xác định 5 lỗi vận hành phổ biến nhất | Danh sách 5 lỗi vận hành phổ biến nhất được xác định từ dữ liệu lỗi. |
| O2-KR2.t2 | O2-KR2 | 3 | O2-KR2.t1 | Lập runbook cho lỗi 1 | Runbook cho lỗi 1 được hoàn thành và lưu trữ trong hệ thống. |
| O2-KR2.t3 | O2-KR2 | 3 | O2-KR2.t1 | Lập runbook cho lỗi 2 | Runbook cho lỗi 2 được hoàn thành và lưu trữ trong hệ thống. |
| O2-KR2.t4 | O2-KR2 | 3 | O2-KR2.t1 | Lập runbook cho lỗi 3 | Runbook cho lỗi 3 được hoàn thành và lưu trữ trong hệ thống. |
| O2-KR2.t5 | O2-KR2 | 3 | O2-KR2.t1 | Lập runbook cho lỗi 4 | Runbook cho lỗi 4 được hoàn thành và lưu trữ trong hệ thống. |
| O2-KR2.t6 | O2-KR2 | 3 | O2-KR2.t1 | Lập runbook cho lỗi 5 | Runbook cho lỗi 5 được hoàn thành và lưu trữ trong hệ thống. |
| O2-KR2.t7 | O2-KR2 | 3 | O2-KR2.t2, O2-KR2.t3, O2-KR2.t4, O2-KR2.t5, O2-KR2.t6 | Kiểm tra runbook với team | Runbook cho 5 lỗi được team kỹ thuật review và chấp nhận. |

### Descriptions

- **O1-KR1.t1**: Định nghĩa rõ uptime là gì, các điểm kiểm tra, và thời gian đo lường.
- **O1-KR1.t2**: Xác định các nguyên nhân gây downtime và lên kế hoạch khắc phục.
- **O1-KR1.t3**: Thực hiện kiểm tra uptime hiện tại và ghi lại kết quả.
- **O1-KR1.t4**: Áp dụng các giải pháp đã lên kế hoạch để cải thiện uptime.
- **O1-KR1.t5**: Kiểm tra uptime sau khi triển khai các cải tiến và ghi lại kết quả.
- **O1-KR1.t6**: Đo lường uptime cuối kỳ và so sánh với mục tiêu.
- **O1-KR2.t1**: Định nghĩa rõ p95 là gì và xác định API tạo giao dịch cần theo dõi.
- **O1-KR2.t2**: Lấy dữ liệu độ trễ p95 trong 7 ngày qua để làm cơ sở so sánh.
- **O1-KR2.t3**: Xác định các yếu tố gây độ trễ như cơ sở dữ liệu, mạng, hoặc xử lý logic.
- **O1-KR2.t4**: Lên kế hoạch tối ưu hóa API tạo giao dịch dựa trên phân tích.
- **O1-KR2.t5**: Áp dụng các giải pháp đã thiết kế để cải thiện độ trễ trong toàn bộ API tạo giao dịch.
- **O1-KR2.t6**: Đo độ trễ p95 sau khi thực hiện tối ưu hóa.
- **O1-KR2.t7**: So sánh độ trễ trước và sau tối ưu hóa, báo cáo kết quả.
- **O1-KR3.t1**: Định nghĩa rõ MTTR và các điều kiện đo lường.
- **O1-KR3.t2**: Lấy dữ liệu lịch sử về thời gian khắc phục sự cố trong 3 tháng qua.
- **O1-KR3.t3**: Xác định các lỗi phổ biến và nguyên nhân gây ra thời gian khắc phục kéo dài.
- **O1-KR3.t4**: Xây dựng quy trình khắc phục sự cố theo từng loại lỗi với thời gian tối đa 30 phút.
- **O1-KR3.t5**: Kiểm thử quy trình với các tình huống giả lập lỗi phổ biến.
- **O1-KR3.t6**: Đánh giá hiệu quả của quy trình và điều chỉnh nếu cần thiết.
- **O1-KR3.t7**: Theo dõi MTTR mỗi tuần và ghi lại kết quả.
- **O1-KR3.t8**: Đánh giá xem MTTR có đạt mục tiêu 30 phút không.
- **O2-KR1.t1**: Định nghĩa rõ các thành phần cần test và phạm vi của test coverage.
- **O2-KR1.t2**: Lập kế hoạch chi tiết các module, chức năng cần test và phân bổ thời gian.
- **O2-KR1.t3**: Viết test case cho 5 module đầu tiên trong danh sách.
- **O2-KR1.t4**: Viết test case cho 5 module tiếp theo trong danh sách.
- **O2-KR1.t5**: Viết test case cho 5 module cuối cùng trong danh sách.
- **O2-KR1.t6**: Chạy toàn bộ test case và kiểm tra kết quả để xác định test coverage hiện tại.
- **O2-KR1.t7**: Đánh giá kết quả test và điều chỉnh test case nếu cần thiết.
- **O2-KR1.t8**: Viết test case cho 5 module tiếp theo trong danh sách.
- **O2-KR1.t9**: Viết test case cho 5 module cuối cùng trong danh sách.
- **O2-KR1.t10**: Chạy toàn bộ test case và kiểm tra kết quả để xác định test coverage hiện tại.
- **O2-KR1.t11**: Đánh giá kết quả test và điều chỉnh test case nếu cần thiết.
- **O2-KR1.t12**: Kiểm tra lại test coverage sau khi hoàn tất việc tăng lên 75%.
- **O2-KR1.t13**: Ghi nhận kết quả đạt được và báo cáo cho team.
- **O2-KR2.t1**: Phân tích dữ liệu lỗi từ hệ thống để xác định 5 lỗi phổ biến nhất.
- **O2-KR2.t2**: Viết runbook chi tiết cho lỗi 1, bao gồm nguyên nhân, cách khắc phục và hướng dẫn xử lý.
- **O2-KR2.t3**: Viết runbook chi tiết cho lỗi 2, bao gồm nguyên nhân, cách khắc phục và hướng dẫn xử lý.
- **O2-KR2.t4**: Viết runbook chi tiết cho lỗi 3, bao gồm nguyên nhân, cách khắc phục và hướng dẫn xử lý.
- **O2-KR2.t5**: Viết runbook chi tiết cho lỗi 4, bao gồm nguyên nhân, cách khắc phục và hướng dẫn xử lý.
- **O2-KR2.t6**: Viết runbook chi tiết cho lỗi 5, bao gồm nguyên nhân, cách khắc phục và hướng dẫn xử lý.
- **O2-KR2.t7**: Mời team kỹ thuật xem qua và góp ý runbook cho 5 lỗi.
