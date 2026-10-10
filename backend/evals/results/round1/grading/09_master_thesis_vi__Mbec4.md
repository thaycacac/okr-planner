# Plan Mbec4 — sample 09_master_thesis_vi

- Pipeline status: `ok`

## Tasks (26 tasks, 102 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 4 | — | Tìm hiểu và thu thập tài liệu liên quan đến phân loại ý định cho chatbot | Đã thu thập được ít nhất 15 tài liệu liên quan và lưu trữ trong thư viện tài liệu của luận văn. |
| O1-KR1.t2 | O1-KR1 | 4 | O1-KR1.t1 | Phân tích và tổng hợp nội dung tài liệu đã thu thập | Đã hoàn thành báo cáo tổng quan với nội dung đầy đủ và có cấu trúc rõ ràng. |
| O1-KR1.t3 | O1-KR1 | 4 | O1-KR1.t2 | Viết nội dung chương 2 (tổng quan tài liệu) dựa trên báo cáo tổng hợp | Đã hoàn thành bản thảo chương 2 với nội dung đầy đủ và trình bày rõ ràng. |
| O1-KR1.t4 | O1-KR1 | 4 | O1-KR1.t3 | Chỉnh sửa và hoàn thiện chương 2 theo góp ý của giảng viên hướng dẫn | Đã chỉnh sửa và hoàn thiện chương 2 theo góp ý của giảng viên hướng dẫn. |
| O1-KR1.t5 | O1-KR1 | 2 | O1-KR1.t4 | Gửi chương 2 cho giảng viên hướng dẫn duyệt | Đã gửi chương 2 cho giảng viên hướng dẫn duyệt và nhận được phản hồi xác nhận duyệt. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Chuẩn bị dữ liệu và bộ intent | Dữ liệu đã được tải về và bộ intent đã được xác nhận bởi giảng viên hướng dẫn. |
| O1-KR2.t2 | O1-KR2 | 4 | O1-KR2.t1 | Gán nhãn 500 câu hội thoại đầu tiên | 500 câu hội thoại đã được gán nhãn và lưu trữ đúng định dạng. |
| O1-KR2.t3 | O1-KR2 | 4 | O1-KR2.t2 | Gán nhãn 500 câu hội thoại tiếp theo | 500 câu hội thoại tiếp theo đã được gán nhãn và lưu trữ đúng định dạng. |
| O1-KR2.t4 | O1-KR2 | 4 | O1-KR2.t3 | Gán nhãn 500 câu hội thoại tiếp theo | 500 câu hội thoại tiếp theo đã được gán nhãn và lưu trữ đúng định dạng. |
| O1-KR2.t5 | O1-KR2 | 4 | O1-KR2.t4 | Gán nhãn 500 câu hội thoại cuối cùng | 500 câu hội thoại cuối cùng đã được gán nhãn và lưu trữ đúng định dạng. |
| O1-KR3.t1 | O1-KR3 | 4 | — | Tìm hiểu và lựa chọn mô hình phân loại ý định phù hợp | Đã xác định được mô hình phân loại ý định phù hợp để triển khai và có tài liệu ghi chú về lý do lựa chọn. |
| O1-KR3.t2 | O1-KR3 | 4 | O1-KR3.t1 | Chuẩn bị dữ liệu và tiền xử lý | Dữ liệu đã được tiền xử lý và sẵn sàng để huấn luyện mô hình. |
| O1-KR3.t3 | O1-KR3 | 6 | O1-KR3.t2 | Huấn luyện mô hình phân loại ý định | Mô hình đã được huấn luyện xong và có kết quả đánh giá trên tập validation. |
| O1-KR3.t4 | O1-KR3 | 6 | O1-KR3.t3 | Đánh giá và điều chỉnh mô hình | Mô hình đã đạt được macro-F1 trên tập test từ 0,62 lên 0,75 hoặc gần giá trị mục tiêu nhất có thể. |
| O1-KR3.t5 | O1-KR3 | 4 | O1-KR3.t4 | Ghi lại kết quả và phân tích | Đã có báo cáo chi tiết về quá trình huấn luyện, đánh giá và điều chỉnh mô hình. |
| O2-KR1.t1 | O2-KR1 | 4 | — | Thu thập và làm sạch dữ liệu | Dữ liệu đã được làm sạch và sẵn sàng để gán nhãn. |
| O2-KR1.t2 | O2-KR1 | 4 | O2-KR1.t1 | Gán nhãn dữ liệu | 3.000 câu hội thoại đã được gán nhãn đầy đủ và kiểm tra chất lượng. |
| O2-KR1.t3 | O2-KR1 | 4 | O2-KR1.t2 | Xây dựng và đánh giá mô hình phân loại ý định | Mô hình phân loại ý định đã được xây dựng và đánh giá với các chỉ số như độ chính xác, độ hồi gọi và F1-score. |
| O2-KR1.t4 | O2-KR1 | 4 | O2-KR1.t3 | Viết phần giới thiệu và phương pháp luận cho bài báo | Phần giới thiệu và phương pháp luận của bài báo đã được hoàn thành và kiểm tra nội dung. |
| O2-KR1.t5 | O2-KR1 | 4 | O2-KR1.t4 | Viết phần kết quả và thảo luận cho bài báo | Phần kết quả và thảo luận của bài báo đã được hoàn thành và kiểm tra nội dung. |
| O2-KR1.t6 | O2-KR1 | 4 | O2-KR1.t5 | Viết phần kết luận và chỉnh sửa bài báo | Bài báo đã được hoàn chỉnh, bao gồm tất cả các phần cần thiết và đã được chỉnh sửa kỹ lưỡng. |
| O2-KR1.t7 | O2-KR1 | 2 | O2-KR1.t6 | Nộp bài báo trước hạn | Bài báo đã được nộp đúng hạn và không có lỗi. |
| O2-KR2.t1 | O2-KR2 | 4 | — | Chuẩn bị nội dung trình bày cho seminar | Nội dung trình bày đã được viết xong và được kiểm tra tính đầy đủ và mạch lạc. |
| O2-KR2.t2 | O2-KR2 | 4 | O2-KR2.t1 | Thiết kế slide trình bày | Slide trình bày đã được hoàn thành và được kiểm tra tính nhất quán và tính thẩm mỹ. |
| O2-KR2.t3 | O2-KR2 | 2 | O2-KR2.t2 | Thực hành trình bày trước nhóm | Đã thực hành trình bày ít nhất một lần và có phản hồi từ người nghe. |
| O2-KR2.t4 | O2-KR2 | 4 | O2-KR2.t3 | Chỉnh sửa và hoàn thiện nội dung trình bày | Nội dung và slide trình bày đã được hoàn thiện và sẵn sàng cho buổi seminar. |

### Descriptions

- **O1-KR1.t1**: Tìm kiếm và tổng hợp các tài liệu học thuật, bài báo khoa học, và tài liệu kỹ thuật liên quan đến chủ đề phân loại ý định trong chatbot, đặc biệt là các nghiên cứu về chatbot tiếng Việt.
- **O1-KR1.t2**: Đọc và phân tích các tài liệu đã thu thập, sau đó tổng hợp thành một báo cáo tổng quan về các phương pháp, kỹ thuật và xu hướng nghiên cứu trong lĩnh vực phân loại ý định cho chatbot.
- **O1-KR1.t3**: Viết nội dung chương 2 của luận văn dựa trên báo cáo tổng quan đã hoàn thành, đảm bảo nội dung phù hợp với yêu cầu của luận văn thạc sĩ và trình bày khoa học.
- **O1-KR1.t4**: Nhận góp ý từ giảng viên hướng dẫn về chương 2, sau đó chỉnh sửa và hoàn thiện nội dung theo các góp ý đó.
- **O1-KR1.t5**: Gửi bản cuối cùng của chương 2 cho giảng viên hướng dẫn để duyệt và nhận phản hồi.
- **O1-KR2.t1**: Tải về và kiểm tra dữ liệu 3.000 câu hội thoại chưa gán nhãn. Đảm bảo bộ intent đã được thống nhất với giảng viên hướng dẫn và sẵn sàng để sử dụng cho việc gán nhãn.
- **O1-KR2.t2**: Gán nhãn cho 500 câu hội thoại đầu tiên trong tập dữ liệu theo bộ intent đã thống nhất.
- **O1-KR2.t3**: Gán nhãn cho 500 câu hội thoại tiếp theo trong tập dữ liệu theo bộ intent đã thống nhất.
- **O1-KR2.t4**: Gán nhãn cho 500 câu hội thoại tiếp theo trong tập dữ liệu theo bộ intent đã thống nhất.
- **O1-KR2.t5**: Gán nhãn cho 500 câu hội thoại cuối cùng trong tập dữ liệu theo bộ intent đã thống nhất.
- **O1-KR3.t1**: Nghiên cứu các mô hình phân loại ý định hiện đại như BERT, RoBERTa, hoặc các mô hình dựa trên học sâu khác, đánh giá khả năng cải thiện macro-F1 so với mô hình hiện tại (TF-IDF + SVM), và lựa chọn mô hình phù hợp để triển khai.
- **O1-KR3.t2**: Tiến hành tiền xử lý dữ liệu hội thoại, bao gồm làm sạch văn bản, chia từ, loại bỏ từ dừng, và mã hóa nhãn. Đảm bảo dữ liệu được chuẩn bị đúng định dạng để sử dụng cho mô hình đã chọn.
- **O1-KR3.t3**: Triển khai huấn luyện mô hình đã chọn trên tập dữ liệu đã được tiền xử lý. Điều chỉnh các siêu tham số như tốc độ học, kích thước batch, số lượng epoch để tối ưu hiệu suất.
- **O1-KR3.t4**: Đánh giá hiệu suất của mô hình trên tập test, kiểm tra chỉ số macro-F1. Nếu chưa đạt mục tiêu, điều chỉnh mô hình, thử nghiệm các phương pháp tăng cường như oversampling, augmentation, hoặc thay đổi kiến trúc mô hình.
- **O1-KR3.t5**: Ghi lại các kết quả huấn luyện, đánh giá, và điều chỉnh mô hình. Phân tích các yếu tố ảnh hưởng đến hiệu suất, như dữ liệu, siêu tham số, và kiến trúc mô hình.
- **O2-KR1.t1**: Thu thập 3.000 câu hội thoại chưa gán nhãn từ chatbot chăm sóc khách hàng và thực hiện các bước làm sạch dữ liệu như loại bỏ ký tự đặc biệt, chuẩn hóa chữ cái, tách từ, và xóa các mẫu không liên quan.
- **O2-KR1.t2**: Gán nhãn cho 3.000 câu hội thoại theo các lớp ý định (intent) phù hợp với mục tiêu của bài báo. Sử dụng các tiêu chí rõ ràng và nhất quán để đảm bảo chất lượng dữ liệu.
- **O2-KR1.t3**: Xây dựng mô hình phân loại ý định sử dụng dữ liệu đã gán nhãn, thử nghiệm các thuật toán khác nhau (bao gồm TF-IDF + SVM và các mô hình hiện đại hơn nếu có thể), và đánh giá hiệu suất của chúng.
- **O2-KR1.t4**: Viết phần giới thiệu, phương pháp luận và mô tả dữ liệu cho bài báo hội thảo, đảm bảo trình bày rõ ràng và phù hợp với tiêu chuẩn học thuật.
- **O2-KR1.t5**: Viết phần kết quả và thảo luận cho bài báo, trình bày các số liệu, so sánh các mô hình và phân tích ý nghĩa của các kết quả đạt được.
- **O2-KR1.t6**: Viết phần kết luận, kiểm tra toàn bộ bài báo để đảm bảo tính nhất quán, chính xác và trình bày đúng theo yêu cầu của hội thảo.
- **O2-KR1.t7**: Kiểm tra lại bài báo một lần cuối, đảm bảo không có lỗi và nộp bài báo hội thảo trước hạn 15/12/2026.
- **O2-KR2.t1**: Viết nội dung trình bày về kết quả nghiên cứu, bao gồm giới thiệu, phương pháp, kết quả và thảo luận. Nội dung cần ngắn gọn, rõ ràng và phù hợp với thời lượng trình bày dự kiến.
- **O2-KR2.t2**: Tạo slide trình bày dựa trên nội dung đã chuẩn bị, đảm bảo hình ảnh, biểu đồ và bố cục phù hợp để hỗ trợ việc trình bày.
- **O2-KR2.t3**: Thực hành trình bày trước một nhóm nhỏ để kiểm tra thời gian, nội dung và khả năng truyền đạt. Nhận phản hồi và điều chỉnh nếu cần.
- **O2-KR2.t4**: Dựa trên phản hồi từ buổi thực hành, chỉnh sửa nội dung và slide trình bày để đảm bảo tính chuyên nghiệp và hiệu quả.
