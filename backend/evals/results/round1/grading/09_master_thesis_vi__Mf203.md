# Plan Mf203 — sample 09_master_thesis_vi

- Pipeline status: `ok`

## Tasks (23 tasks, 90 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 4 | — | Tổng hợp tài liệu và phân tích nghiên cứu liên quan | Tài liệu tổng hợp đã được phân loại và lưu trữ, kèm theo báo cáo phân tích phương pháp hiện có và điểm khác biệt của đề tài. |
| O1-KR1.t2 | O1-KR1 | 4 | O1-KR1.t1 | Viết phần tổng quan tài liệu cho chương 2 | Chương 2 đã được hoàn thành và gửi cho giảng viên hướng dẫn để duyệt. |
| O1-KR1.t3 | O1-KR1 | 2 | O1-KR1.t2 | Chuẩn bị dữ liệu và phân công công việc gán nhãn | Dữ liệu 2.000 câu hội thoại đã được chuẩn bị và phân công công việc gán nhãn. |
| O1-KR1.t4 | O1-KR1 | 4 | O1-KR1.t3 | Gán nhãn 2.000 câu hội thoại theo bộ intent | Tất cả 2.000 câu hội thoại đã được gán nhãn theo bộ intent và kiểm tra lại để đảm bảo tính nhất quán. |
| O1-KR1.t5 | O1-KR1 | 4 | O1-KR1.t4 | Xây dựng và huấn luyện mô hình phân loại intent | Mô hình phân loại intent đã được huấn luyện và đánh giá hiệu suất ban đầu. |
| O1-KR1.t6 | O1-KR1 | 4 | O1-KR1.t5 | Tối ưu mô hình và nâng macro-F1 lên 0,75 | Macro-F1 trên tập test đã đạt mức 0,75 và mô hình đã được kiểm tra kỹ lưỡng. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Lên kế hoạch và phân loại bộ intent | Các intent đã được xác định rõ và 2.000 câu hội thoại được phân chia thành các nhóm nhỏ theo intent. |
| O1-KR2.t2 | O1-KR2 | 4 | O1-KR2.t1 | Gán nhãn cho 500 câu hội thoại đầu tiên | 500 câu hội thoại đã được gán nhãn và kiểm tra lại để đảm bảo tính nhất quán. |
| O1-KR2.t3 | O1-KR2 | 4 | O1-KR2.t2 | Gán nhãn cho 500 câu hội thoại tiếp theo | 500 câu hội thoại tiếp theo đã được gán nhãn và kiểm tra lại để đảm bảo tính nhất quán. |
| O1-KR2.t4 | O1-KR2 | 4 | O1-KR2.t3 | Gán nhãn cho 500 câu hội thoại tiếp theo | 500 câu hội thoại tiếp theo đã được gán nhãn và kiểm tra lại để đảm bảo tính nhất quán. |
| O1-KR2.t5 | O1-KR2 | 4 | O1-KR2.t4 | Gán nhãn cho 500 câu hội thoại cuối cùng | 500 câu hội thoại cuối cùng đã được gán nhãn và kiểm tra lại để đảm bảo tính nhất quán. |
| O1-KR3.t1 | O1-KR3 | 4 | — | Phân tích hiện trạng và xác định điểm yếu của mô hình hiện tại | Đã hoàn thành báo cáo phân tích hiện trạng và đề xuất cải tiến mô hình, được giảng viên phê duyệt. |
| O1-KR3.t2 | O1-KR3 | 6 | O1-KR3.t1 | Thiết kế và triển khai các cải tiến mô hình | Đã hoàn thành việc triển khai và thử nghiệm các cải tiến mô hình, đạt macro-F1 trên tập test tối thiểu là 0.70. |
| O1-KR3.t3 | O1-KR3 | 4 | O1-KR3.t2 | Gán nhãn dữ liệu và đánh giá hiệu suất | Đã hoàn thành việc gán nhãn dữ liệu và đánh giá hiệu suất, đạt macro-F1 trên tập test tối thiểu là 0.75. |
| O1-KR3.t4 | O1-KR3 | 4 | O1-KR3.t3 | Viết báo cáo và chuẩn bị kết quả | Đã hoàn thành báo cáo chi tiết và tài liệu trình bày kết quả, đạt macro-F1 trên tập test là 0.75. |
| O2-KR1.t1 | O2-KR1 | 4 | — | Xử lý dữ liệu và chuẩn bị tập dữ liệu | Tập dữ liệu đã được làm sạch và gán nhãn hoàn toàn, với ít nhất 3.000 câu được xử lý và phân loại thành các lớp ý định tương ứng. |
| O2-KR1.t2 | O2-KR1 | 4 | O2-KR1.t1 | Tối ưu mô hình TF-IDF + SVM | Mô hình TF-IDF + SVM đã được tối ưu và đạt được độ chính xác tối thiểu 80% trên tập dữ liệu kiểm thử. |
| O2-KR1.t3 | O2-KR1 | 4 | O2-KR1.t2 | Viết bài báo hội thảo | Bài báo hội thảo đã được hoàn thành, có đủ 6 trang và được kiểm tra về tính chính xác và tính logic. |
| O2-KR1.t4 | O2-KR1 | 4 | O2-KR1.t3 | Chỉnh sửa và hoàn thiện bài báo | Bài báo hội thảo đã được chỉnh sửa hoàn toàn và sẵn sàng nộp trước hạn 15/12/2026. |
| O2-KR2.t1 | O2-KR2 | 4 | — | Chuẩn bị nội dung trình bày cho seminar | Đã có tài liệu trình bày đầy đủ và sẵn sàng cho buổi seminar nhóm nghiên cứu. |
| O2-KR2.t2 | O2-KR2 | 4 | O2-KR2.t1 | Thiết kế slide trình bày | Đã hoàn thành slide trình bày và được kiểm tra bởi người hướng dẫn. |
| O2-KR2.t3 | O2-KR2 | 4 | O2-KR2.t2 | Thực hiện buổi trình bày tại seminar | Đã hoàn thành buổi trình bày và nhận được phản hồi từ nhóm nghiên cứu. |
| O2-KR2.t4 | O2-KR2 | 2 | O2-KR2.t3 | Lập kế hoạch cải thiện dựa trên phản hồi | Đã có kế hoạch cải thiện rõ ràng dựa trên phản hồi từ buổi seminar. |

### Descriptions

- **O1-KR1.t1**: Thu thập và tổng hợp tài liệu liên quan đến phân loại ý định trong chatbot tiếng Việt, bao gồm các bài báo, luận văn, và tài liệu hướng dẫn. Phân tích các phương pháp hiện có và xác định điểm khác biệt của đề tài.
- **O1-KR1.t2**: Viết phần tổng quan tài liệu cho chương 2 của luận văn, bao gồm mục lục, tóm tắt nội dung, và đánh giá các nghiên cứu liên quan. Đảm bảo nội dung phù hợp với yêu cầu của giảng viên hướng dẫn.
- **O1-KR1.t3**: Chuẩn bị dữ liệu 2.000 câu hội thoại chưa gán nhãn, phân loại theo bộ intent đã thống nhất, và phân công công việc cho người hỗ trợ nếu cần.
- **O1-KR1.t4**: Gán nhãn cho 2.000 câu hội thoại theo bộ intent đã thống nhất, đảm bảo tính nhất quán và chính xác trong quá trình gán nhãn.
- **O1-KR1.t5**: Xây dựng mô hình phân loại intent dựa trên dữ liệu đã gán nhãn, huấn luyện mô hình và đánh giá hiệu suất ban đầu.
- **O1-KR1.t6**: Tối ưu mô hình bằng các phương pháp như điều chỉnh siêu tham số, tăng cường dữ liệu, hoặc sử dụng các kỹ thuật khác để nâng macro-F1 trên tập test từ 0,62 lên 0,75.
- **O1-KR2.t1**: Xác định rõ các intent đã thống nhất và phân chia 2.000 câu hội thoại thành các nhóm nhỏ theo intent để đảm bảo tính nhất quán trong gán nhãn.
- **O1-KR2.t2**: Gán nhãn cho 500 câu hội thoại đầu tiên theo bộ intent đã thống nhất, đảm bảo tính nhất quán và chính xác.
- **O1-KR2.t3**: Tiếp tục gán nhãn cho 500 câu hội thoại tiếp theo theo bộ intent đã thống nhất, đảm bảo tính nhất quán và chính xác.
- **O1-KR2.t4**: Tiếp tục gán nhãn cho 500 câu hội thoại tiếp theo theo bộ intent đã thống nhất, đảm bảo tính nhất quán và chính xác.
- **O1-KR2.t5**: Gán nhãn cho 500 câu hội thoại cuối cùng theo bộ intent đã thống nhất, đảm bảo tính nhất quán và chính xác.
- **O1-KR3.t1**: Đánh giá mô hình TF-IDF + SVM hiện tại, phân tích các chỉ số hiện tại, xác định các yếu tố làm giảm macro-F1 và đề xuất các cải tiến có thể thực hiện.
- **O1-KR3.t2**: Triển khai các cải tiến như sử dụng mô hình học sâu (BERT, DistilBERT, hoặc các mô hình ngôn ngữ tiếng Việt), điều chỉnh hyperparameters, và thử nghiệm trên tập dữ liệu chưa gán nhãn.
- **O1-KR3.t3**: Sử dụng dữ liệu đã gán nhãn (2.000 câu) để đánh giá hiệu suất của mô hình, điều chỉnh mô hình dựa trên kết quả và tiến hành thử nghiệm trên tập test.
- **O1-KR3.t4**: Viết báo cáo chi tiết về các bước thực hiện, kết quả đạt được, và phân tích các yếu tố ảnh hưởng đến macro-F1. Chuẩn bị tài liệu để trình bày kết quả.
- **O2-KR1.t1**: Làm sạch dữ liệu, phân loại các câu hội thoại, và gán nhãn cho các câu chưa gán nhãn. Sử dụng các công cụ như Python, Pandas, và các thư viện xử lý ngôn ngữ tự nhiên.
- **O2-KR1.t2**: Đánh giá hiệu suất của mô hình hiện tại, thực hiện các bước tối ưu như chọn lựa đặc trưng, điều chỉnh tham số, và kiểm tra độ chính xác trên tập dữ liệu.
- **O2-KR1.t3**: Viết nội dung bài báo hội thảo gồm phần giới thiệu, phương pháp, kết quả, và thảo luận, đảm bảo đủ 6 trang và tuân thủ định dạng yêu cầu.
- **O2-KR1.t4**: Chỉnh sửa lại bài báo hội thảo để đảm bảo tính mạch lạc, rõ ràng, và tuân thủ các yêu cầu của hội nghị. Kiểm tra lỗi chính tả và định dạng.
- **O2-KR2.t1**: Tổng hợp kết quả nghiên cứu, bao gồm mô tả dữ liệu, phương pháp, kết quả và phân tích, để trình bày tại seminar của nhóm nghiên cứu.
- **O2-KR2.t2**: Tạo slide trình bày với nội dung đã chuẩn bị, đảm bảo tính trực quan và dễ hiểu cho khán giả.
- **O2-KR2.t3**: Trình bày kết quả nghiên cứu trước nhóm nghiên cứu, trả lời các câu hỏi và nhận phản hồi.
- **O2-KR2.t4**: Phân tích phản hồi từ buổi seminar và lên kế hoạch cải thiện kết quả nghiên cứu nếu cần.
