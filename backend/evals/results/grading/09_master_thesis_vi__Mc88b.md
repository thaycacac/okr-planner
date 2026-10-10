# Plan Mc88b — sample 09_master_thesis_vi

- Pipeline status: `ok`

## Tasks (38 tasks, 137 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 3 | — | Lên kế hoạch và xác định phạm vi cho chương 2 | Có tài liệu tham khảo, tiêu chí đánh giá và cấu trúc chương 2 được xác định rõ ràng. |
| O1-KR1.t2 | O1-KR1 | 4 | O1-KR1.t1 | Chuẩn bị tài liệu tham khảo cho chương 2 | Tài liệu tham khảo được tổng hợp và lưu trữ trong một tài liệu riêng. |
| O1-KR1.t3 | O1-KR1 | 6 | O1-KR1.t2 | Viết chương 2 theo cấu trúc đã xác định | Chương 2 được viết hoàn chỉnh và lưu trữ dưới dạng tài liệu Word. |
| O1-KR1.t4 | O1-KR1 | 4 | O1-KR1.t3 | Chỉnh sửa chương 2 theo phản hồi ban đầu | Chương 2 được chỉnh sửa theo phản hồi ban đầu và đạt yêu cầu về nội dung. |
| O1-KR1.t5 | O1-KR1 | 4 | O1-KR1.t4 | Kiểm tra lại chương 2 trước khi nộp | Chương 2 được kiểm tra lại và đạt yêu cầu về định dạng, ngữ pháp và chính tả. |
| O1-KR1.t6 | O1-KR1 | 2 | O1-KR1.t5 | Nộp chương 2 để giảng viên hướng dẫn duyệt | Chương 2 đã được gửi cho giảng viên hướng dẫn và nhận được phản hồi. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Lên kế hoạch gán nhãn | Bộ intent đã được xác định và công cụ gán nhãn đã sẵn sàng. |
| O1-KR2.t2 | O1-KR2 | 6 | O1-KR2.t1 | Gán nhãn 1-500 câu hội thoại | 500 câu hội thoại đã được gán nhãn và lưu trữ. |
| O1-KR2.t3 | O1-KR2 | 4 | O1-KR2.t2 | Kiểm tra và đánh giá 1-500 câu | 500 câu đã được kiểm tra và xác nhận chính xác. |
| O1-KR2.t4 | O1-KR2 | 6 | O1-KR2.t3 | Gán nhãn 501-1000 câu hội thoại | 500 câu hội thoại từ 501-1000 đã được gán nhãn và lưu trữ. |
| O1-KR2.t5 | O1-KR2 | 4 | O1-KR2.t4 | Kiểm tra và đánh giá 501-1000 câu | 500 câu từ 501-1000 đã được kiểm tra và xác nhận chính xác. |
| O1-KR2.t6 | O1-KR2 | 6 | O1-KR2.t5 | Gán nhãn 1001-1500 câu hội thoại | 500 câu hội thoại từ 1001-1500 đã được gán nhãn và lưu trữ. |
| O1-KR2.t7 | O1-KR2 | 4 | O1-KR2.t6 | Kiểm tra và đánh giá 1001-1500 câu | 500 câu từ 1001-1500 đã được kiểm tra và xác nhận chính xác. |
| O1-KR2.t8 | O1-KR2 | 6 | O1-KR2.t7 | Gán nhãn 1501-2000 câu hội thoại | 500 câu hội thoại từ 1501-2000 đã được gán nhãn và lưu trữ. |
| O1-KR2.t9 | O1-KR2 | 4 | O1-KR2.t8 | Kiểm tra và đánh giá 1501-2000 câu | 500 câu từ 1501-2000 đã được kiểm tra và xác nhận chính xác. |
| O1-KR2.t10 | O1-KR2 | 4 | O1-KR2.t9 | Đánh giá tổng thể và báo cáo kết quả | Báo cáo tổng kết 2.000 câu đã gán nhãn và được giảng viên xác nhận. |
| O1-KR3.t1 | O1-KR3 | 3 | — | Xác định tiêu chí và phạm vi cải tiến mô hình | Tài liệu xác định rõ các lớp intent và tiêu chí tính macro-F1 được lưu trữ. |
| O1-KR3.t2 | O1-KR3 | 2 | O1-KR3.t1, O1-KR2.t10 | Chuẩn bị dữ liệu và công cụ phân tích | Dữ liệu và công cụ đã được tải và thiết lập sẵn sàng. |
| O1-KR3.t3 | O1-KR3 | 3 | O1-KR3.t2 | Thử nghiệm mô hình ban đầu | Kết quả macro-F1 ban đầu được ghi lại và xác nhận là 0.62. |
| O1-KR3.t4 | O1-KR3 | 2 | O1-KR3.t3 | Thử nghiệm mô hình Naive Bayes | Kết quả macro-F1 của mô hình Naive Bayes được ghi lại. |
| O1-KR3.t5 | O1-KR3 | 2 | O1-KR3.t4 | Thử nghiệm mô hình Random Forest | Kết quả macro-F1 của mô hình Random Forest được ghi lại. |
| O1-KR3.t6 | O1-KR3 | 2 | O1-KR3.t5 | Thử nghiệm mô hình BERT | Kết quả macro-F1 của mô hình BERT được ghi lại. |
| O1-KR3.t7 | O1-KR3 | 4 | O1-KR3.t6 | Đánh giá và chọn mô hình tối ưu | Mô hình tối ưu được chọn và ghi chú rõ ràng. |
| O1-KR3.t8 | O1-KR3 | 2 | O1-KR3.t7 | Tối ưu tham số và thử nghiệm lại | Kết quả macro-F1 đạt 0.75 hoặc cao hơn được ghi lại. |
| O1-KR3.t9 | O1-KR3 | 3 | O1-KR3.t8 | Kiểm tra lại kết quả và ghi chú | Tài liệu ghi chú các bước thực hiện và kết quả đạt được được lưu trữ. |
| O1-KR3.t10 | O1-KR3 | 2 | O1-KR3.t9 | Đo lường kết quả cuối cùng | Kết quả macro-F1 cuối cùng được ghi lại và xác nhận đạt 0.75. |
| O2-KR1.t1 | O2-KR1 | 3 | — | Xác định yêu cầu và phạm vi bài báo | Cấu trúc bài báo được xác định rõ ràng với các phần chính như tóm tắt, giới thiệu, phương pháp, kết quả, thảo luận và kết luận. |
| O2-KR1.t2 | O2-KR1 | 3 | O2-KR1.t1 | Làm rõ mục tiêu và nội dung bài báo | Tóm tắt và phần giới thiệu bài báo được hoàn thành, nêu rõ mục tiêu và ý nghĩa nghiên cứu. |
| O2-KR1.t3 | O2-KR1 | 4 | O2-KR1.t2 | Viết phần phương pháp nghiên cứu | Phần phương pháp nghiên cứu được hoàn thành, bao gồm mô tả dữ liệu, xử lý dữ liệu và mô hình được sử dụng. |
| O2-KR1.t4 | O2-KR1 | 5 | O2-KR1.t3, O1-KR3.t10 | Viết phần kết quả nghiên cứu | Phần kết quả được hoàn thành, bao gồm các chỉ số hiệu suất và so sánh với baseline hiện tại. |
| O2-KR1.t5 | O2-KR1 | 4 | O2-KR1.t4 | Viết phần thảo luận và kết luận | Phần thảo luận và kết luận được hoàn thành, nêu rõ ý nghĩa, đóng góp và hướng phát triển của nghiên cứu. |
| O2-KR1.t6 | O2-KR1 | 3 | O2-KR1.t5 | Kiểm tra và chỉnh sửa bài báo | Bài báo được kiểm tra và chỉnh sửa, đảm bảo tính logic, ngôn ngữ và định dạng đúng. |
| O2-KR1.t7 | O2-KR1 | 2 | O2-KR1.t6 | Nộp bài báo hội thảo | Bài báo được nộp đúng hạn theo yêu cầu của hội thảo. |
| O2-KR2.t1 | O2-KR2 | 3 | O2-KR1.t7 | Lên kế hoạch trình bày | File slide trình bày được gửi cho nhóm và được phê duyệt |
| O2-KR2.t2 | O2-KR2 | 5 | O2-KR2.t1 | Chuẩn bị nội dung seminar | Tài liệu trình bày hoàn chỉnh được lưu trữ trong thư mục chung |
| O2-KR2.t3 | O2-KR2 | 4 | O2-KR2.t2 | Thực hiện seminar | Video ghi hình seminar được lưu trữ và chia sẻ |
| O2-KR2.t4 | O2-KR2 | 2 | O2-KR2.t3 | Thu thập phản hồi | Khảo sát được gửi và có ít nhất 10 phản hồi |
| O2-KR2.t5 | O2-KR2 | 3 | O2-KR2.t4 | Phân tích phản hồi | Báo cáo phân tích phản hồi được gửi cho nhóm |

### Descriptions

- **O1-KR1.t1**: Xác định các tài liệu tham khảo, tiêu chí đánh giá và cấu trúc chương 2.
- **O1-KR1.t2**: Tổng hợp tài liệu liên quan đến phân loại ý định trong chatbot tiếng Việt.
- **O1-KR1.t3**: Viết nội dung chương 2 dựa trên tài liệu tham khảo và tiêu chí đã xác định.
- **O1-KR1.t4**: Đọc lại và chỉnh sửa nội dung chương 2 để đảm bảo tính logic và đầy đủ.
- **O1-KR1.t5**: Đọc lại chương 2 để đảm bảo không có lỗi chính tả, lỗi ngữ pháp và đạt yêu cầu về định dạng.
- **O1-KR1.t6**: Gửi chương 2 cho giảng viên hướng dẫn để được duyệt.
- **O1-KR2.t1**: Xác định bộ intent, phân loại câu hội thoại và chuẩn bị công cụ.
- **O1-KR2.t2**: Thực hiện gán nhãn cho 500 câu đầu tiên theo bộ intent.
- **O1-KR2.t3**: Kiểm tra lại 500 câu đã gán nhãn để đảm bảo tính nhất quán.
- **O1-KR2.t4**: Tiếp tục gán nhãn cho 500 câu tiếp theo theo bộ intent.
- **O1-KR2.t5**: Kiểm tra lại 500 câu đã gán nhãn để đảm bảo tính nhất quán.
- **O1-KR2.t6**: Tiếp tục gán nhãn cho 500 câu tiếp theo theo bộ intent.
- **O1-KR2.t7**: Kiểm tra lại 500 câu đã gán nhãn để đảm bảo tính nhất quán.
- **O1-KR2.t8**: Tiếp tục gán nhãn cho 500 câu cuối cùng theo bộ intent.
- **O1-KR2.t9**: Kiểm tra lại 500 câu đã gán nhãn để đảm bảo tính nhất quán.
- **O1-KR2.t10**: Tổng hợp số lượng câu đã gán nhãn và báo cáo kết quả cho giảng viên.
- **O1-KR3.t1**: Định nghĩa rõ ràng các lớp intent, tiêu chí đánh giá và cách tính macro-F1.
- **O1-KR3.t2**: Tải dữ liệu, cài đặt công cụ, và chuẩn bị môi trường chạy mô hình.
- **O1-KR3.t3**: Chạy mô hình TF-IDF + SVM và ghi lại kết quả macro-F1 hiện tại.
- **O1-KR3.t4**: Chạy mô hình Naive Bayes và ghi lại kết quả macro-F1.
- **O1-KR3.t5**: Chạy mô hình Random Forest và ghi lại kết quả macro-F1.
- **O1-KR3.t6**: Chạy mô hình BERT và ghi lại kết quả macro-F1.
- **O1-KR3.t7**: Phân tích kết quả và chọn mô hình có macro-F1 cao nhất.
- **O1-KR3.t8**: Tối ưu tham số và thử nghiệm lại để đạt macro-F1 tối thiểu 0.75.
- **O1-KR3.t9**: Kiểm tra lại kết quả và ghi chú các bước thực hiện.
- **O1-KR3.t10**: Đo lường macro-F1 trên tập test sau khi tối ưu.
- **O2-KR1.t1**: Lên kế hoạch cấu trúc bài báo, xác định mục tiêu, phạm vi và các phần cần có.
- **O2-KR1.t2**: Viết phần tóm tắt và giới thiệu bài báo, nêu rõ mục tiêu nghiên cứu và ý nghĩa của bài báo.
- **O2-KR1.t3**: Mô tả chi tiết phương pháp thu thập dữ liệu, xử lý dữ liệu và mô hình phân loại ý định được sử dụng.
- **O2-KR1.t4**: Trình bày kết quả phân loại ý định, so sánh với baseline hiện tại và đánh giá hiệu suất mô hình.
- **O2-KR1.t5**: Phân tích ý nghĩa của kết quả, nêu rõ đóng góp của nghiên cứu và đề xuất hướng phát triển.
- **O2-KR1.t6**: Đọc lại toàn bộ bài báo, kiểm tra tính logic, ngôn ngữ và đảm bảo tuân thủ định dạng hội thảo.
- **O2-KR1.t7**: Gửi bài báo theo đúng quy trình và thời hạn quy định.
- **O2-KR2.t1**: Xác định nội dung, cấu trúc và công cụ trình bày cho seminar
- **O2-KR2.t2**: Tổng hợp kết quả nghiên cứu thành tài liệu trình bày
- **O2-KR2.t3**: Trình bày kết quả nghiên cứu trước nhóm nghiên cứu
- **O2-KR2.t4**: Gửi khảo sát để thu thập ý kiến từ người tham dự seminar
- **O2-KR2.t5**: Xử lý và phân tích dữ liệu từ khảo sát để cải thiện nội dung
