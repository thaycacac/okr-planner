# Plan Mf203 — sample 05_payment_reliability_vi

- Pipeline status: `ok`

## Tasks (24 tasks, 92 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 4 | — | Phân tích nguyên nhân gây downtime trong 3 tháng qua | Đã hoàn thành báo cáo phân tích nguyên nhân downtime với các vấn đề chính được xác định và dữ liệu hỗ trợ cụ thể. |
| O1-KR1.t2 | O1-KR1 | 4 | O1-KR1.t1 | Cập nhật và tối ưu hóa cấu hình hệ thống | Các thay đổi cấu hình đã được triển khai và kiểm tra, đảm bảo không gây ảnh hưởng đến dịch vụ hiện tại. |
| O1-KR1.t3 | O1-KR1 | 4 | O1-KR1.t2 | Thiết lập và giám sát hệ thống cảnh báo tự động | Hệ thống giám sát đã được triển khai và đang hoạt động, gửi cảnh báo đúng lúc khi có sự cố. |
| O1-KR1.t4 | O1-KR1 | 4 | O1-KR1.t3 | Kiểm tra và tối ưu hóa cơ sở dữ liệu PostgreSQL | Cơ sở dữ liệu đã được tối ưu hóa, hiệu suất truy vấn cải thiện và không có sự cố liên quan trong thời gian kiểm tra. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Phân tích hiện trạng độ trễ API tạo giao dịch | Đã có báo cáo phân tích chi tiết về các yếu tố gây độ trễ và dữ liệu độ trễ p95 hiện tại được ghi nhận rõ ràng. |
| O1-KR2.t2 | O1-KR2 | 4 | O1-KR2.t1 | Tối ưu hóa truy vấn cơ sở dữ liệu | Các truy vấn liên quan đến giao dịch đã được tối ưu và thời gian phản hồi cơ sở dữ liệu giảm đáng kể. |
| O1-KR2.t3 | O1-KR2 | 4 | O1-KR2.t2 | Tối ưu hóa xử lý logic backend | Logic xử lý giao dịch đã được tối ưu và thời gian xử lý giảm đáng kể. |
| O1-KR2.t4 | O1-KR2 | 4 | O1-KR2.t3 | Kiểm tra và tối ưu hóa mạng | Độ trễ mạng đã được kiểm tra và tối ưu hóa nếu cần thiết, đảm bảo không gây ảnh hưởng đến độ trễ p95. |
| O1-KR2.t5 | O1-KR2 | 4 | O1-KR2.t4 | Kiểm tra và triển khai các cải tiến | Độ trễ p95 của API tạo giao dịch đã giảm xuống dưới 300 ms và được xác nhận qua dữ liệu giám sát. |
| O1-KR3.t1 | O1-KR3 | 4 | — | Phân tích nguyên nhân gây ra thời gian khắc phục sự cố cao | Đã hoàn thành báo cáo phân tích nguyên nhân và đưa ra danh sách các vấn đề chính gây ra MTTR cao trong 3 tháng qua. |
| O1-KR3.t2 | O1-KR3 | 4 | O1-KR3.t1 | Tối ưu hóa quy trình khắc phục sự cố | Quy trình khắc phục sự cố mới đã được triển khai và được kiểm thử trong môi trường staging. |
| O1-KR3.t3 | O1-KR3 | 4 | O1-KR3.t2 | Tự động hóa các tác vụ khắc phục sự cố thường xuyên | Các tác vụ tự động hóa đã được triển khai và đang chạy trong môi trường staging. |
| O1-KR3.t4 | O1-KR3 | 4 | O1-KR3.t3 | Thiết lập cảnh báo và giám sát thời gian thực | Hệ thống giám sát và cảnh báo đã được triển khai và đang hoạt động trong môi trường staging. |
| O2-KR1.t1 | O2-KR1 | 2 | — | Phân tích hiện trạng test coverage hiện tại | Đã tạo báo cáo phân tích test coverage hiện tại và xác định các module chưa được test. |
| O2-KR1.t2 | O2-KR1 | 4 | O2-KR1.t1 | Viết test case cho các module chưa được test | Đã viết test case cho ít nhất 30% các module chưa được test và chạy thành công. |
| O2-KR1.t3 | O2-KR1 | 2 | O2-KR1.t2 | Tích hợp test case vào CI/CD pipeline | Test case mới đã được tích hợp vào CI/CD và báo cáo test coverage được cập nhật tự động. |
| O2-KR1.t4 | O2-KR1 | 4 | O2-KR1.t3 | Tăng test coverage cho các module quan trọng | Test coverage đạt mức 75% hoặc cao hơn, theo báo cáo từ CI/CD. |
| O2-KR2.t1 | O2-KR2 | 4 | — | Xác định 5 lỗi vận hành phổ biến nhất trong hệ thống | Đã có danh sách 5 lỗi vận hành phổ biến nhất với số lần xảy ra và tác động cụ thể được ghi lại trong tài liệu runbook dự kiến. |
| O2-KR2.t2 | O2-KR2 | 4 | O2-KR2.t1 | Viết runbook cho lỗi 1 | Runbook cho lỗi 1 đã được hoàn thành và lưu trữ trong hệ thống tài liệu chung của team. |
| O2-KR2.t3 | O2-KR2 | 4 | O2-KR2.t1 | Viết runbook cho lỗi 2 | Runbook cho lỗi 2 đã được hoàn thành và lưu trữ trong hệ thống tài liệu chung của team. |
| O2-KR2.t4 | O2-KR2 | 4 | O2-KR2.t1 | Viết runbook cho lỗi 3 | Runbook cho lỗi 3 đã được hoàn thành và lưu trữ trong hệ thống tài liệu chung của team. |
| O2-KR2.t5 | O2-KR2 | 4 | O2-KR2.t1 | Viết runbook cho lỗi 4 | Runbook cho lỗi 4 đã được hoàn thành và lưu trữ trong hệ thống tài liệu chung của team. |
| O2-KR2.t6 | O2-KR2 | 4 | O2-KR2.t1 | Viết runbook cho lỗi 5 | Runbook cho lỗi 5 đã được hoàn thành và lưu trữ trong hệ thống tài liệu chung của team. |
| O2-KR2.t7 | O2-KR2 | 4 | O2-KR2.t2, O2-KR2.t3, O2-KR2.t4, O2-KR2.t5, O2-KR2.t6 | Review runbook bởi team | Runbook cho 5 lỗi đã được team review và xác nhận đạt yêu cầu. |

### Descriptions

- **O1-KR1.t1**: Xem xét nhật ký hệ thống, báo cáo sự cố và dữ liệu uptime để xác định các vấn đề phổ biến gây gián đoạn dịch vụ.
- **O1-KR1.t2**: Điều chỉnh cấu hình máy chủ, cơ sở dữ liệu và mạng để giảm thiểu rủi ro gây downtime và cải thiện độ ổn định.
- **O1-KR1.t3**: Tích hợp công cụ giám sát (như Prometheus, Grafana, hoặc Sentry) để theo dõi trạng thái hệ thống và gửi cảnh báo khi có sự cố.
- **O1-KR1.t4**: Phân tích hiệu suất cơ sở dữ liệu, tối ưu hóa truy vấn, và đảm bảo cơ sở dữ liệu hoạt động ổn định trong điều kiện cao điểm.
- **O1-KR2.t1**: Xác định các điểm gây độ trễ trong quá trình xử lý giao dịch, bao gồm cơ sở dữ liệu, mạng, và xử lý logic. Sử dụng công cụ giám sát để thu thập dữ liệu độ trễ p95 hiện tại.
- **O1-KR2.t2**: Cải thiện hiệu suất truy vấn PostgreSQL bằng cách tối ưu hóa câu lệnh SQL, sử dụng chỉ mục hợp lý, và giảm thời gian phản hồi từ cơ sở dữ liệu.
- **O1-KR2.t3**: Kiểm tra và tối ưu hóa logic xử lý giao dịch trong Python, bao gồm việc giảm thời gian xử lý, sử dụng cache hợp lý, và tối ưu hóa các vòng lặp.
- **O1-KR2.t4**: Phân tích độ trễ mạng giữa các thành phần trong hệ thống, bao gồm API, cơ sở dữ liệu, và các dịch vụ phụ trợ. Tối ưu hóa nếu cần thiết.
- **O1-KR2.t5**: Kiểm tra toàn bộ hệ thống sau khi thực hiện các cải tiến, đảm bảo rằng độ trễ p95 của API tạo giao dịch đã giảm xuống dưới 300 ms.
- **O1-KR3.t1**: Xem xét các báo cáo sự cố trong 3 tháng qua để xác định các nguyên nhân phổ biến gây ra MTTR cao, như lỗi phần mềm, lỗi cơ sở dữ liệu, hoặc vấn đề mạng.
- **O1-KR3.t2**: Xây dựng và triển khai quy trình khắc phục sự cố mới, bao gồm các bước tự động hóa, phân quyền rõ ràng, và quy trình báo cáo sự cố nhanh hơn.
- **O1-KR3.t3**: Tự động hóa các tác vụ khắc phục sự cố phổ biến như kiểm tra trạng thái cơ sở dữ liệu, giám sát hiệu suất, và tự động khởi động lại các dịch vụ nếu cần thiết.
- **O1-KR3.t4**: Cài đặt hệ thống giám sát thời gian thực để theo dõi các chỉ số như MTTR, uptime, và độ trễ API, đồng thời thiết lập cảnh báo tự động khi vượt ngưỡng.
- **O2-KR1.t1**: Xác định các module, lớp, hoặc hàm hiện tại chưa được test, và đánh giá mức độ phức tạp của chúng để xác định nơi cần ưu tiên.
- **O2-KR1.t2**: Viết test case cho các module, lớp, hoặc hàm chưa được test, tập trung vào các logic quan trọng và các trường hợp edge case.
- **O2-KR1.t3**: Cập nhật pipeline CI/CD để tự động chạy test case mới và báo cáo kết quả test coverage.
- **O2-KR1.t4**: Tiếp tục viết test case cho các module quan trọng, đặc biệt là các logic liên quan đến xử lý giao dịch và bảo mật.
- **O2-KR2.t1**: Phân tích log, báo cáo sự cố và phản hồi từ team vận hành để xác định 5 lỗi phổ biến nhất ảnh hưởng đến hệ thống.
- **O2-KR2.t2**: Tạo tài liệu runbook chi tiết cho lỗi đầu tiên, bao gồm nguyên nhân, cách phát hiện, các bước khắc phục và người chịu trách nhiệm.
- **O2-KR2.t3**: Tạo tài liệu runbook chi tiết cho lỗi thứ hai, bao gồm nguyên nhân, cách phát hiện, các bước khắc phục và người chịu trách nhiệm.
- **O2-KR2.t4**: Tạo tài liệu runbook chi tiết cho lỗi thứ ba, bao gồm nguyên nhân, cách phát hiện, các bước khắc phục và người chịu trách nhiệm.
- **O2-KR2.t5**: Tạo tài liệu runbook chi tiết cho lỗi thứ tư, bao gồm nguyên nhân, cách phát hiện, các bước khắc phục và người chịu trách nhiệm.
- **O2-KR2.t6**: Tạo tài liệu runbook chi tiết cho lỗi thứ năm, bao gồm nguyên nhân, cách phát hiện, các bước khắc phục và người chịu trách nhiệm.
- **O2-KR2.t7**: Gửi runbook cho 5 lỗi vận hành phổ biến nhất để team review và đưa ra phản hồi, đảm bảo tính chính xác và khả thi.
