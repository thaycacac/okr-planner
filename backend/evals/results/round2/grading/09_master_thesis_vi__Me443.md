# Plan Me443 — sample 09_master_thesis_vi

- Pipeline status: `ok`

## Tasks (40 tasks, 165 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 2 | — | Chuẩn bị tài liệu và yêu cầu từ giảng viên | Giảng viên gửi lại yêu cầu duyệt chương 2 và tiêu chí đánh giá. |
| O1-KR1.t2 | O1-KR1 | 4 | O1-KR1.t1 | Làm rõ yêu cầu và chuẩn bị tài liệu | Chương 2 được hoàn thiện theo yêu cầu của giảng viên. |
| O1-KR1.t3 | O1-KR1 | 2 | O1-KR1.t2 | Gửi chương 2 để giảng viên xem trước | Giảng viên gửi lại phản hồi về chương 2. |
| O1-KR1.t4 | O1-KR1 | 4 | O1-KR1.t3 | Chỉnh sửa chương 2 theo phản hồi | Chương 2 được chỉnh sửa hoàn tất theo phản hồi của giảng viên. |
| O1-KR1.t5 | O1-KR1 | 2 | O1-KR1.t4 | Nộp chương 2 để giảng viên duyệt | Chương 2 được giảng viên duyệt và xác nhận hoàn thành. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Lên kế hoạch và chuẩn bị dữ liệu | Đã có danh sách 2.000 câu hội thoại được phân loại theo bộ intent và công cụ gán nhãn đã sẵn sàng. |
| O1-KR2.t2 | O1-KR2 | 6 | O1-KR2.t1 | Gán nhãn 2.000 câu hội thoại: phần 1 | Đã gán nhãn hoàn tất 300 câu hội thoại đầu tiên theo bộ intent. |
| O1-KR2.t3 | O1-KR2 | 6 | O1-KR2.t2 | Gán nhãn 2.000 câu hội thoại: phần 2 | Đã gán nhãn hoàn tất 600 câu hội thoại theo bộ intent. |
| O1-KR2.t4 | O1-KR2 | 6 | O1-KR2.t3 | Gán nhãn 2.000 câu hội thoại: phần 3 | Đã gán nhãn hoàn tất 900 câu hội thoại theo bộ intent. |
| O1-KR2.t5 | O1-KR2 | 6 | O1-KR2.t4 | Gán nhãn 2.000 câu hội thoại: phần 4 | Đã gán nhãn hoàn tất 1.200 câu hội thoại theo bộ intent. |
| O1-KR2.t6 | O1-KR2 | 6 | O1-KR2.t5 | Gán nhãn 2.000 câu hội thoại: phần 5 | Đã gán nhãn hoàn tất 1.500 câu hội thoại theo bộ intent. |
| O1-KR2.t7 | O1-KR2 | 6 | O1-KR2.t6 | Gán nhãn 2.000 câu hội thoại: phần 6 | Đã gán nhãn hoàn tất 1.800 câu hội thoại theo bộ intent. |
| O1-KR2.t8 | O1-KR2 | 4 | O1-KR2.t7 | Gán nhãn 2.000 câu hội thoại: phần 7 | Đã gán nhãn hoàn tất 2.000 câu hội thoại theo bộ intent. |
| O1-KR2.t9 | O1-KR2 | 4 | O1-KR2.t8 | Kiểm tra và đánh giá lại kết quả gán nhãn: phần 1 | Đã kiểm tra và xác nhận 100 câu gán nhãn, đảm bảo độ chính xác đạt yêu cầu. |
| O1-KR2.t10 | O1-KR2 | 4 | O1-KR2.t9 | Kiểm tra và đánh giá lại kết quả gán nhãn: phần 2 | Đã kiểm tra và xác nhận 200 câu gán nhãn, đảm bảo độ chính xác đạt yêu cầu. |
| O1-KR2.t11 | O1-KR2 | 4 | O1-KR2.t10 | Kiểm tra và đánh giá lại kết quả gán nhãn: phần 3 | Đã kiểm tra và xác nhận 300 câu gán nhãn, đảm bảo độ chính xác đạt yêu cầu. |
| O1-KR2.t12 | O1-KR2 | 4 | O1-KR2.t11 | Kiểm tra và đánh giá lại kết quả gán nhãn: phần 4 | Đã kiểm tra và xác nhận 400 câu gán nhãn, đảm bảo độ chính xác đạt yêu cầu. |
| O1-KR2.t13 | O1-KR2 | 4 | O1-KR2.t12 | Kiểm tra và đánh giá lại kết quả gán nhãn: phần 5 | Đã kiểm tra và xác nhận 500 câu gán nhãn, đảm bảo độ chính xác đạt yêu cầu. |
| O1-KR2.t14 | O1-KR2 | 4 | O1-KR2.t13 | Tính toán và báo cáo kết quả gán nhãn | Đã hoàn thành báo cáo số lượng câu gán nhãn và gửi cho giảng viên hướng dẫn. |
| O1-KR3.t1 | O1-KR3 | 4 | O1-KR2.t8 | Chuẩn bị dữ liệu và xác định tiêu chí đánh giá | Đã xác định rõ tập test, tiêu chí macro-F1, và công cụ cần thiết. |
| O1-KR3.t2 | O1-KR3 | 4 | O1-KR3.t1 | Phân tích mô hình hiện tại và xác định điểm yếu | Đã phân tích mô hình hiện tại và xác định các điểm yếu cụ thể. |
| O1-KR3.t3 | O1-KR3 | 4 | O1-KR3.t2 | Thử nghiệm với mô hình Random Forest | Đã thử nghiệm mô hình Random Forest và ghi nhận kết quả macro-F1. |
| O1-KR3.t4 | O1-KR3 | 4 | O1-KR3.t3 | Thử nghiệm với mô hình XGBoost | Đã thử nghiệm mô hình XGBoost và ghi nhận kết quả macro-F1. |
| O1-KR3.t5 | O1-KR3 | 4 | O1-KR3.t4 | Thử nghiệm với mô hình BERT | Đã thử nghiệm mô hình BERT và ghi nhận kết quả macro-F1. |
| O1-KR3.t6 | O1-KR3 | 4 | O1-KR3.t5 | Đánh giá và chọn mô hình tối ưu | Đã chọn mô hình tối ưu và hoàn tất quá trình tối ưu hóa tham số. |
| O1-KR3.t7 | O1-KR3 | 4 | O1-KR3.t6 | Kiểm tra lại mô hình trên tập test | Mô hình đã đạt macro-F1 trên tập test là 0.75. |
| O1-KR3.t8 | O1-KR3 | 4 | O1-KR3.t7 | Ghi nhận và báo cáo kết quả | Đã ghi nhận và báo cáo đầy đủ kết quả thử nghiệm. |
| O2-KR1.t1 | O2-KR1 | 4 | O1-KR3.t7 | Lập kế hoạch và xác định phạm vi bài báo hội thảo | Cấu trúc bài báo và danh sách tài liệu tham khảo đã được xác định rõ ràng. |
| O2-KR1.t2 | O2-KR1 | 3 | O2-KR1.t1 | Viết phần tóm tắt và mục lục bài báo | Phần tóm tắt và mục lục đã hoàn thành và được kiểm tra. |
| O2-KR1.t3 | O2-KR1 | 4 | O2-KR1.t2 | Viết phần giới thiệu và mục tiêu nghiên cứu | Phần giới thiệu và mục tiêu nghiên cứu đã hoàn thành và được kiểm tra. |
| O2-KR1.t4 | O2-KR1 | 6 | O2-KR1.t3 | Viết phần phương pháp nghiên cứu | Phần phương pháp nghiên cứu đã hoàn thành và được kiểm tra. |
| O2-KR1.t5 | O2-KR1 | 6 | O2-KR1.t4 | Viết phần kết quả và thảo luận | Phần kết quả và thảo luận đã hoàn thành và được kiểm tra. |
| O2-KR1.t6 | O2-KR1 | 4 | O2-KR1.t5 | Viết phần kết luận và tài liệu tham khảo | Phần kết luận và tài liệu tham khảo đã hoàn thành và được kiểm tra. |
| O2-KR1.t7 | O2-KR1 | 4 | O2-KR1.t6 | Kiểm tra và chỉnh sửa bài báo hội thảo | Bài báo hội thảo đã được kiểm tra và chỉnh sửa hoàn tất. |
| O2-KR1.t8 | O2-KR1 | 2 | O2-KR1.t7 | Nộp bài báo hội thảo | Bài báo hội thảo đã được nộp đúng hạn. |
| O2-KR2.t1 | O2-KR2 | 4 | O2-KR1.t8 | Chuẩn bị nội dung trình bày | Có bản tóm tắt nội dung trình bày và cấu trúc bài thuyết trình được xác định rõ ràng. |
| O2-KR2.t2 | O2-KR2 | 4 | O2-KR2.t1 | Làm slide trình bày | Hoàn thành bộ slide trình bày với nội dung đầy đủ và trực quan. |
| O2-KR2.t3 | O2-KR2 | 4 | O2-KR2.t2 | Thực hiện bài trình bày tại seminar | Hoàn thành bài trình bày và nhận phản hồi từ người tham dự. |
| O2-KR2.t4 | O2-KR2 | 4 | O2-KR2.t3 | Thu thập phản hồi và cải thiện bài trình bày | Cải thiện bài trình bày dựa trên phản hồi và sẵn sàng cho phiên trình bày cuối cùng. |
| O2-KR2.t5 | O2-KR2 | 2 | O2-KR2.t4 | Đo lường hiệu quả của bài trình bày | Có báo cáo đánh giá hiệu quả bài trình bày và phản hồi từ người tham dự. |

### Descriptions

- **O1-KR1.t1**: Liên hệ giảng viên hướng dẫn để xác định tiêu chí duyệt chương 2, yêu cầu cụ thể về nội dung, định dạng và thời hạn.
- **O1-KR1.t2**: Đọc lại chương 2, so sánh với yêu cầu từ giảng viên, bổ sung tài liệu tham khảo, chỉnh sửa phần tổng quan tài liệu theo hướng dẫn.
- **O1-KR1.t3**: Gửi chương 2 cho giảng viên để xem trước và nhận phản hồi.
- **O1-KR1.t4**: Sửa chương 2 dựa trên phản hồi từ giảng viên, đảm bảo đáp ứng đầy đủ yêu cầu.
- **O1-KR1.t5**: Nộp chương 2 cho giảng viên để hoàn tất quá trình duyệt.
- **O1-KR2.t1**: Xác định bộ intent đã thống nhất, phân loại các câu hội thoại, và chuẩn bị công cụ gán nhãn như Excel hoặc phần mềm hỗ trợ.
- **O1-KR2.t2**: Gán nhãn 300 câu hội thoại đầu tiên theo bộ intent đã thống nhất.
- **O1-KR2.t3**: Gán nhãn 300 câu hội thoại tiếp theo theo bộ intent đã thống nhất.
- **O1-KR2.t4**: Gán nhãn 300 câu hội thoại tiếp theo theo bộ intent đã thống nhất.
- **O1-KR2.t5**: Gán nhãn 300 câu hội thoại tiếp theo theo bộ intent đã thống nhất.
- **O1-KR2.t6**: Gán nhãn 300 câu hội thoại cuối cùng theo bộ intent đã thống nhất.
- **O1-KR2.t7**: Gán nhãn 300 câu hội thoại cuối cùng theo bộ intent đã thống nhất.
- **O1-KR2.t8**: Gán nhãn 200 câu hội thoại cuối cùng theo bộ intent đã thống nhất.
- **O1-KR2.t9**: Kiểm tra ngẫu nhiên 100 câu hội thoại đã gán nhãn để đảm bảo độ chính xác, và điều chỉnh nếu cần.
- **O1-KR2.t10**: Kiểm tra ngẫu nhiên 100 câu hội thoại đã gán nhãn để đảm bảo độ chính xác, và điều chỉnh nếu cần.
- **O1-KR2.t11**: Kiểm tra ngẫu nhiên 100 câu hội thoại đã gán nhãn để đảm bảo độ chính xác, và điều chỉnh nếu cần.
- **O1-KR2.t12**: Kiểm tra ngẫu nhiên 100 câu hội thoại đã gán nhãn để đảm bảo độ chính xác, và điều chỉnh nếu cần.
- **O1-KR2.t13**: Kiểm tra ngẫu nhiên 100 câu hội thoại đã gán nhãn để đảm bảo độ chính xác, và điều chỉnh nếu cần.
- **O1-KR2.t14**: Tính toán số lượng câu đã gán nhãn, và báo cáo kết quả cho giảng viên hướng dẫn.
- **O1-KR3.t1**: Xác định tập test, tiêu chí tính macro-F1, và cách đánh giá mô hình. Chuẩn bị công cụ như Python, scikit-learn, và dữ liệu cần thiết.
- **O1-KR3.t2**: Đánh giá mô hình TF-IDF + SVM hiện tại trên tập test, xác định các điểm yếu như độ chính xác, recall, và F1-score.
- **O1-KR3.t3**: Thử nghiệm mô hình Random Forest trên tập test, đánh giá macro-F1 và ghi nhận kết quả.
- **O1-KR3.t4**: Thử nghiệm mô hình XGBoost trên tập test, đánh giá macro-F1 và ghi nhận kết quả.
- **O1-KR3.t5**: Thử nghiệm mô hình BERT trên tập test, đánh giá macro-F1 và ghi nhận kết quả.
- **O1-KR3.t6**: So sánh kết quả từ các mô hình thử nghiệm, chọn mô hình có macro-F1 cao nhất và tối ưu hóa tham số.
- **O1-KR3.t7**: Kiểm tra lại mô hình đã chọn trên tập test để đảm bảo macro-F1 đạt mục tiêu 0.75.
- **O1-KR3.t8**: Ghi lại toàn bộ quá trình thử nghiệm, kết quả đạt được, và phân tích nguyên nhân cải thiện macro-F1.
- **O2-KR1.t1**: Xác định cấu trúc bài báo, tiêu chí chọn nội dung, và các phần cần trình bày. Chuẩn bị tài liệu tham khảo và công cụ hỗ trợ.
- **O2-KR1.t2**: Viết phần tóm tắt (abstract) và mục lục (table of contents) cho bài báo hội thảo.
- **O2-KR1.t3**: Viết phần giới thiệu và mục tiêu nghiên cứu của bài báo hội thảo.
- **O2-KR1.t4**: Viết phần phương pháp nghiên cứu, bao gồm mô tả dữ liệu, mô hình, và cách phân tích.
- **O2-KR1.t5**: Viết phần kết quả và thảo luận, bao gồm phân tích dữ liệu và ý nghĩa của nghiên cứu.
- **O2-KR1.t6**: Viết phần kết luận và tài liệu tham khảo cho bài báo hội thảo.
- **O2-KR1.t7**: Kiểm tra lỗi chính tả, ngữ pháp, và tính nhất quán của bài báo hội thảo.
- **O2-KR1.t8**: Nộp bài báo hội thảo theo yêu cầu của hội đồng.
- **O2-KR2.t1**: Làm rõ mục tiêu, cấu trúc và nội dung chính của bài trình bày tại seminar, bao gồm tóm tắt kết quả nghiên cứu, phương pháp, dữ liệu và kết quả đạt được.
- **O2-KR2.t2**: Tạo slide trình bày với nội dung chính, hình ảnh minh họa, biểu đồ và bảng số liệu để hỗ trợ bài thuyết trình.
- **O2-KR2.t3**: Trình bày kết quả nghiên cứu trước nhóm nghiên cứu và các chuyên gia trong seminar, đảm bảo thời gian và nội dung phù hợp.
- **O2-KR2.t4**: Tổng hợp phản hồi từ seminar, điều chỉnh nội dung và slide trình bày để cải thiện chất lượng bài thuyết trình.
- **O2-KR2.t5**: Đánh giá mức độ phản hồi, sự tham gia và hiệu quả truyền đạt của bài trình bày tại seminar.
