# Plan Mbec4 — sample 01_saas_onboarding_vi

- Pipeline status: `ok`

## Tasks (24 tasks, 94 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 4 | — | Phân tích dữ liệu activation hiện tại | Có báo cáo phân tích chi tiết về các điểm nghẽn trong quá trình activation. |
| O1-KR1.t2 | O1-KR1 | 4 | O1-KR1.t1 | Thiết kế lại quy trình onboarding cho người dùng mới | Có bản thiết kế quy trình onboarding mới được phê duyệt. |
| O1-KR1.t3 | O1-KR1 | 4 | O1-KR1.t2 | Triển khai A/B test cho quy trình onboarding mới | A/B test đã được triển khai và đang thu thập dữ liệu. |
| O1-KR1.t4 | O1-KR1 | 4 | O1-KR1.t3 | Phân tích kết quả A/B test và điều chỉnh quy trình onboarding | Có báo cáo phân tích kết quả A/B test và quy trình onboarding đã được điều chỉnh (nếu cần). |
| O1-KR1.t5 | O1-KR1 | 4 | O1-KR1.t4 | Triển khai quy trình onboarding mới cho toàn bộ người dùng | Quy trình onboarding mới đã được triển khai cho toàn bộ người dùng mới. |
| O1-KR1.t6 | O1-KR1 | 4 | O1-KR1.t5 | Theo dõi và đánh giá tỉ lệ activation sau triển khai | Tỉ lệ activation trong 7 ngày đã được đo lường và đạt mục tiêu 35%. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Phân tích dữ liệu hiện tại về time-to-first-value | Báo cáo phân tích với các điểm nghẽn chính đã được xác định và lưu trữ trong hệ thống quản lý dự án. |
| O1-KR2.t2 | O1-KR2 | 4 | O1-KR2.t1 | Thiết kế lại quy trình onboarding dựa trên phân tích | Bản thiết kế quy trình onboarding mới đã được hoàn thành và lưu trữ trong hệ thống quản lý dự án. |
| O1-KR2.t3 | O1-KR2 | 4 | O1-KR2.t2 | Triển khai quy trình onboarding mới cho người dùng mới | Quy trình onboarding mới đã được triển khai và đang được áp dụng cho người dùng mới. |
| O1-KR2.t4 | O1-KR2 | 4 | O1-KR2.t3 | Theo dõi và đánh giá hiệu quả của quy trình onboarding mới | Báo cáo đánh giá hiệu quả quy trình onboarding mới đã được hoàn thành và lưu trữ trong hệ thống quản lý dự án. |
| O1-KR3.t1 | O1-KR3 | 4 | — | Phân tích 3 luồng chính: nhập hàng, xuất hàng, kiểm kê | Đã có danh sách các bước và điểm cần giải thích cho từng luồng. |
| O1-KR3.t2 | O1-KR3 | 4 | O1-KR3.t1 | Thiết kế nội dung hướng dẫn in-app cho từng luồng | Đã hoàn thành nội dung hướng dẫn cho cả 3 luồng. |
| O1-KR3.t3 | O1-KR3 | 4 | O1-KR3.t2 | Thiết kế giao diện hướng dẫn in-app | Đã có bản thiết kế giao diện hướng dẫn in-app cho từng luồng. |
| O1-KR3.t4 | O1-KR3 | 4 | O1-KR3.t3 | Triển khai hướng dẫn in-app vào sản phẩm | Hướng dẫn in-app đã được triển khai và chạy thử thành công trong ứng dụng. |
| O1-KR3.t5 | O1-KR3 | 4 | O1-KR3.t4 | Kiểm thử và hiệu chỉnh hướng dẫn in-app | Hướng dẫn in-app đã được kiểm thử và hiệu chỉnh hoàn tất. |
| O1-KR3.t6 | O1-KR3 | 2 | O1-KR3.t5 | Ra mắt hướng dẫn in-app cho người dùng mới | Hướng dẫn in-app đã được kích hoạt và hiển thị cho người dùng mới. |
| O2-KR1.t1 | O2-KR1 | 4 | — | Phân tích dữ liệu churn tháng đầu để xác định nguyên nhân chính | Có báo cáo phân tích sơ bộ về các nguyên nhân chính gây churn tháng đầu. |
| O2-KR1.t2 | O2-KR1 | 6 | O2-KR1.t1 | Thiết kế và triển khai tính năng cải thiện trải nghiệm người dùng trong tháng đầu | Tính năng đã được triển khai và sẵn sàng cho người dùng mới. |
| O2-KR1.t3 | O2-KR1 | 4 | O2-KR1.t2 | Tối ưu quy trình onboarding cho người dùng mới | Quy trình onboarding đã được cập nhật và triển khai. |
| O2-KR1.t4 | O2-KR1 | 4 | O2-KR1.t3 | Thiết kế và gửi email chăm sóc người dùng trong tháng đầu | Email chăm sóc người dùng đã được gửi đến toàn bộ người dùng mới trong tháng đầu. |
| O2-KR1.t5 | O2-KR1 | 2 | O2-KR1.t4 | Theo dõi và đánh giá hiệu quả các hành động giảm churn | Có báo cáo sơ bộ về hiệu quả của các hành động đã thực hiện trong việc giảm tỉ lệ churn. |
| O2-KR2.t1 | O2-KR2 | 2 | — | Xác định danh sách 15 khách hàng đã rời bỏ trong tháng đầu sử dụng | Danh sách 15 khách hàng đã rời bỏ được xác định và lưu trữ trong hệ thống hoặc tài liệu chia sẻ. |
| O2-KR2.t2 | O2-KR2 | 6 | O2-KR2.t1 | Liên hệ và phỏng vấn 15 khách hàng đã rời bỏ | 15 cuộc phỏng vấn được hoàn thành và ghi lại nội dung phỏng vấn. |
| O2-KR2.t3 | O2-KR2 | 4 | O2-KR2.t2 | Tổng hợp insight từ các cuộc phỏng vấn | Báo cáo tổng hợp insight từ 15 cuộc phỏng vấn được hoàn thành và lưu trữ. |

### Descriptions

- **O1-KR1.t1**: Xem xét dữ liệu activation hiện tại để xác định các điểm nghẽn và nguyên nhân khiến tỉ lệ activation thấp. Tập trung vào hành vi người dùng trong 7 ngày đầu tiên.
- **O1-KR1.t2**: Dựa trên phân tích từ t1, thiết kế lại quy trình onboarding để giúp người dùng tạo sản phẩm đầu tiên dễ dàng hơn trong 7 ngày đầu tiên.
- **O1-KR1.t3**: Triển khai A/B test để so sánh tỉ lệ activation giữa quy trình onboarding cũ và mới. Đảm bảo thu thập dữ liệu đầy đủ để đánh giá hiệu quả.
- **O1-KR1.t4**: Phân tích kết quả A/B test để xác định liệu quy trình onboarding mới có cải thiện tỉ lệ activation hay không. Điều chỉnh quy trình nếu cần thiết.
- **O1-KR1.t5**: Triển khai quy trình onboarding mới cho toàn bộ người dùng mới, đảm bảo không có lỗi và hệ thống hoạt động trơn tru.
- **O1-KR1.t6**: Theo dõi tỉ lệ activation trong 7 ngày sau khi triển khai quy trình onboarding mới. Đảm bảo đạt mục tiêu 35%.
- **O1-KR2.t1**: Thu thập và phân tích dữ liệu hiện tại về hành vi người dùng mới để xác định các điểm nghẽn trong quá trình onboarding. Tập trung vào các bước mà người dùng mất nhiều thời gian nhất để hoàn thành.
- **O1-KR2.t2**: Dựa trên kết quả phân tích, thiết kế lại quy trình onboarding để rút ngắn thời gian đạt giá trị đầu tiên. Tập trung vào việc đơn giản hóa các bước phức tạp và tăng tính hướng dẫn.
- **O1-KR2.t3**: Triển khai quy trình onboarding mới cho người dùng mới, đảm bảo rằng các thay đổi được áp dụng một cách mượt mà và không làm gián đoạn trải nghiệm hiện tại.
- **O1-KR2.t4**: Theo dõi và đánh giá hiệu quả của quy trình onboarding mới bằng cách thu thập dữ liệu về time-to-first-value trong một khoảng thời gian nhất định.
- **O1-KR3.t1**: Xác định các bước quan trọng và điểm dễ gây nhầm lẫn trong từng luồng để xây dựng nội dung hướng dẫn in-app phù hợp.
- **O1-KR3.t2**: Viết nội dung hướng dẫn ngắn gọn, dễ hiểu và phù hợp với từng luồng chính: nhập hàng, xuất hàng, kiểm kê.
- **O1-KR3.t3**: Tạo giao diện hướng dẫn in-app với các hình ảnh minh họa, biểu tượng và các bước tương tác phù hợp.
- **O1-KR3.t4**: Lắp đặt hướng dẫn in-app vào ứng dụng, đảm bảo tính tương tác và hiển thị đúng theo luồng người dùng.
- **O1-KR3.t5**: Kiểm tra hướng dẫn in-app trên các thiết bị và trình duyệt khác nhau, hiệu chỉnh nếu có lỗi hoặc điểm cần cải thiện.
- **O1-KR3.t6**: Kích hoạt hướng dẫn in-app cho người dùng mới và theo dõi phản hồi ban đầu để đánh giá hiệu quả.
- **O2-KR1.t1**: Xem xét dữ liệu sử dụng, phản hồi và hành vi của người dùng trong tháng đầu tiên để xác định các yếu tố chính dẫn đến churn.
- **O2-KR1.t2**: Dựa trên insight từ phân tích dữ liệu, thiết kế và triển khai một tính năng mới hoặc cải tiến hiện tại nhằm tăng sự gắn kết của người dùng trong tháng đầu.
- **O2-KR1.t3**: Cải thiện quy trình hướng dẫn người dùng mới để giúp họ hiểu và sử dụng sản phẩm hiệu quả hơn trong những ngày đầu tiên.
- **O2-KR1.t4**: Tạo và gửi các email hướng dẫn, hỗ trợ và khuyến khích người dùng tiếp tục sử dụng sản phẩm trong tháng đầu tiên.
- **O2-KR1.t5**: Theo dõi tỉ lệ churn sau khi triển khai các cải tiến và phân tích hiệu quả của từng hành động.
- **O2-KR2.t1**: Tìm kiếm và xác định danh sách 15 khách hàng đã rời bỏ trong tháng đầu sử dụng từ hệ thống, đảm bảo rằng họ đã đăng ký và rời bỏ trong khoảng thời gian phù hợp.
- **O2-KR2.t2**: Tiến hành phỏng vấn 15 khách hàng đã rời bỏ thông qua email, điện thoại hoặc các kênh liên lạc phù hợp, đảm bảo thu thập được thông tin cần thiết về lý do rời bỏ.
- **O2-KR2.t3**: Phân tích nội dung từ 15 cuộc phỏng vấn, tóm tắt các insight chính về lý do khách hàng rời bỏ, và lưu trữ dưới dạng báo cáo hoặc tài liệu tổng hợp.
