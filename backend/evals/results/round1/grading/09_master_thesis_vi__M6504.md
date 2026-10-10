# Plan M6504 — sample 09_master_thesis_vi

- Pipeline status: `ok`

## Tasks (31 tasks, 113 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 4 | — | Nghiên cứu và tổng hợp tài liệu liên quan đến tổng quan lý thuyết | Có một bản nháp tài liệu tổng quan lý thuyết, bao gồm các ý chính và các nguồn tài liệu tham khảo đã được xác định. |
| O1-KR1.t2 | O1-KR1 | 6 | O1-KR1.t1 | Soạn thảo bản nháp Chương 2 (Tổng quan tài liệu) | Hoàn thành bản nháp Chương 2, bao gồm các phần mở đầu, nội dung chính, và kết luận sơ bộ. |
| O1-KR1.t3 | O1-KR1 | 4 | O1-KR1.t2 | Rà soát và chỉnh sửa bản nháp Chương 2 | Bản nháp Chương 2 đã được rà soát, chỉnh sửa và hoàn thiện về mặt nội dung và hình thức. |
| O1-KR1.t4 | O1-KR1 | 2 | O1-KR1.t3 | Gửi Chương 2 cho giảng viên hướng dẫn duyệt | Đã gửi bản nháp Chương 2 cho giảng viên hướng dẫn và nhận được xác nhận đã nhận. |
| O1-KR1.t5 | O1-KR1 | 4 | O1-KR1.t4 | Chỉnh sửa Chương 2 theo góp ý của giảng viên hướng dẫn | Chương 2 đã được chỉnh sửa theo các góp ý của giảng viên hướng dẫn và sẵn sàng để trình duyệt lại. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Làm quen với bộ intent và hướng dẫn gán nhãn | Viết báo cáo ngắn gọn (dưới 1 trang) tóm tắt bộ intent và cách gán nhãn, được giảng viên hướng dẫn phê duyệt. |
| O1-KR2.t2 | O1-KR2 | 4 | O1-KR2.t1 | Gán nhãn 500 câu hội thoại đầu tiên | Hoàn thành gán nhãn 500 câu hội thoại và có báo cáo về các trường hợp gán nhãn khó hoặc không rõ ràng. |
| O1-KR2.t3 | O1-KR2 | 4 | O1-KR2.t2 | Gán nhãn 500 câu hội thoại tiếp theo | Hoàn thành gán nhãn 500 câu hội thoại và có báo cáo về các trường hợp gán nhãn khó hoặc không rõ ràng. |
| O1-KR2.t4 | O1-KR2 | 4 | O1-KR2.t3 | Gán nhãn 500 câu hội thoại tiếp theo | Hoàn thành gán nhãn 500 câu hội thoại và có báo cáo về các trường hợp gán nhãn khó hoặc không rõ ràng. |
| O1-KR2.t5 | O1-KR2 | 4 | O1-KR2.t4 | Gán nhãn 500 câu hội thoại tiếp theo | Hoàn thành gán nhãn 500 câu hội thoại và có báo cáo về các trường hợp gán nhãn khó hoặc không rõ ràng. |
| O1-KR2.t6 | O1-KR2 | 4 | O1-KR2.t5 | Kiểm tra và sửa lỗi gán nhãn cho 1000 câu hội thoại đầu tiên | Hoàn thành kiểm tra và sửa lỗi cho 1000 câu hội thoại đầu tiên, có báo cáo chi tiết về các lỗi đã phát hiện và cách sửa. |
| O1-KR2.t7 | O1-KR2 | 4 | O1-KR2.t6 | Gán nhãn 500 câu hội thoại cuối cùng | Hoàn thành gán nhãn 500 câu hội thoại và có báo cáo về các trường hợp gán nhãn khó hoặc không rõ ràng. |
| O1-KR3.t1 | O1-KR3 | 4 | — | Nghiên cứu và thử nghiệm các thuật toán/kiến trúc cải tiến | Đã thử nghiệm ít nhất 3 kiến trúc/thuật toán khác nhau và có báo cáo chi tiết về kết quả thử nghiệm, bao gồm các chỉ số đánh giá (precision, recall, F1-score) và phân tích ưu nhược điểm. |
| O1-KR3.t2 | O1-KR3 | 3 | — | Tinh chỉnh mô hình hiện tại (TF-IDF + SVM) | Đã thử nghiệm ít nhất 5 bộ tham số khác nhau cho mô hình TF-IDF + SVM và có báo cáo chi tiết về kết quả thử nghiệm, bao gồm các chỉ số đánh giá (precision, recall, F1-score). |
| O1-KR3.t3 | O1-KR3 | 4 | O1-KR3.t1, O1-KR3.t2 | Thử nghiệm kết hợp các mô hình (Ensemble) | Đã thử nghiệm ít nhất 2 phương pháp ensemble khác nhau và có báo cáo chi tiết về kết quả thử nghiệm, bao gồm các chỉ số đánh giá (precision, recall, F1-score). |
| O1-KR3.t4 | O1-KR3 | 2 | O1-KR3.t1, O1-KR3.t2, O1-KR3.t3 | Đánh giá và lựa chọn mô hình tốt nhất | Đã chọn ra mô hình tốt nhất dựa trên macro-F1 score trên tập test và có báo cáo chi tiết về lý do lựa chọn, bao gồm phân tích các trường hợp hoạt động kém. |
| O1-KR3.t5 | O1-KR3 | 3 | O1-KR3.t4 | Tối ưu hóa và tinh chỉnh mô hình tốt nhất | Mô hình đã được tối ưu hóa và tinh chỉnh để đạt được macro-F1 score trên tập test đạt hoặc vượt quá 0.75. |
| O1-KR3.t6 | O1-KR3 | 3 | O1-KR3.t5 | Viết báo cáo kết quả thực nghiệm | Báo cáo kết quả thực nghiệm đã được hoàn thành và sẵn sàng để trình bày cho giảng viên hướng dẫn. |
| O2-KR1.t1 | O2-KR1 | 4 | — | Xác định phạm vi và cấu trúc bài báo hội thảo | Dàn ý chi tiết bài báo được phê duyệt bởi người hướng dẫn. |
| O2-KR1.t2 | O2-KR1 | 4 | O2-KR1.t1 | Viết phần giới thiệu và tổng quan liên quan đến bài báo | Phần giới thiệu hoàn chỉnh và được người hướng dẫn duyệt. |
| O2-KR1.t3 | O2-KR1 | 6 | O2-KR1.t1 | Viết phần phương pháp nghiên cứu | Phần phương pháp hoàn chỉnh, rõ ràng và được người hướng dẫn duyệt. |
| O2-KR1.t4 | O2-KR1 | 6 | O2-KR1.t3 | Viết phần kết quả và phân tích | Phần kết quả và phân tích hoàn chỉnh, có bảng biểu và đồ thị minh họa, được người hướng dẫn duyệt. |
| O2-KR1.t5 | O2-KR1 | 4 | O2-KR1.t4 | Viết phần thảo luận và kết luận | Phần thảo luận và kết luận hoàn chỉnh, được người hướng dẫn duyệt. |
| O2-KR1.t6 | O2-KR1 | 4 | O2-KR1.t5 | Kiểm tra và chỉnh sửa bài báo | Bài báo đã được kiểm tra, chỉnh sửa và đạt yêu cầu về nội dung và định dạng. |
| O2-KR1.t7 | O2-KR1 | 2 | O2-KR1.t6 | Chuẩn bị tài liệu tham khảo | Danh mục tài liệu tham khảo hoàn chỉnh và chính xác. |
| O2-KR1.t8 | O2-KR1 | 2 | O2-KR1.t6, O2-KR1.t7 | Nộp bài báo hội thảo | Bài báo đã được nộp thành công qua hệ thống của hội thảo và nhận được xác nhận. |
| O2-KR2.t1 | O2-KR2 | 4 | — | Chuẩn bị nội dung trình bày seminar | Tài liệu trình bày hoàn chỉnh, bao gồm slide và ghi chú, đã được duyệt bởi người hướng dẫn. |
| O2-KR2.t2 | O2-KR2 | 3 | O2-KR2.t1 | Thiết kế slide trình bày | Bộ slide trình bày hoàn chỉnh, được thiết kế chuyên nghiệp và phù hợp với nội dung trình bày. |
| O2-KR2.t3 | O2-KR2 | 2 | O2-KR2.t2 | Luyện tập trình bày | Trình bày đã được luyện tập ít nhất 2 lần và nhận được phản hồi tích cực từ người hướng dẫn hoặc đồng nghiệp. |
| O2-KR2.t4 | O2-KR2 | 3 | O2-KR2.t1 | Chuẩn bị câu hỏi và trả lời | Danh sách các câu hỏi dự kiến và câu trả lời tương ứng đã được chuẩn bị và duyệt bởi người hướng dẫn. |
| O2-KR2.t5 | O2-KR2 | 2 | O2-KR2.t3, O2-KR2.t4 | Tham gia seminar và trình bày | Đã trình bày thành công tại seminar và trả lời các câu hỏi của người nghe. |

### Descriptions

- **O1-KR1.t1**: Tìm kiếm, đọc và tổng hợp các tài liệu khoa học, bài báo, sách, và các nguồn tài liệu khác liên quan đến phân loại ý định (intent classification) và chatbot tiếng Việt. Tập trung vào các phương pháp, mô hình, và nghiên cứu trước đây trong lĩnh vực này. Ghi chép lại các ý chính, kết quả, và các điểm cần thiết để xây dựng phần tổng quan tài liệu.
- **O1-KR1.t2**: Dựa trên bản nháp tài liệu đã thu thập, soạn thảo bản nháp Chương 2 của luận văn, trình bày một cách có hệ thống và mạch lạc các kiến thức nền tảng, các nghiên cứu trước đây, và các xu hướng phát triển trong lĩnh vực phân loại ý định và chatbot tiếng Việt. Đảm bảo tính chính xác, đầy đủ, và rõ ràng của nội dung.
- **O1-KR1.t3**: Rà soát kỹ lưỡng bản nháp Chương 2 để đảm bảo tính logic, mạch lạc, và chính xác của nội dung. Chỉnh sửa các lỗi chính tả, ngữ pháp, và định dạng. Đảm bảo các trích dẫn và tài liệu tham khảo được thực hiện đúng theo quy định.
- **O1-KR1.t4**: Gửi bản nháp Chương 2 đã chỉnh sửa cho giảng viên hướng dẫn để nhận xét và góp ý. Theo dõi phản hồi từ giảng viên hướng dẫn và chuẩn bị sẵn sàng để thảo luận và giải đáp các thắc mắc.
- **O1-KR1.t5**: Tiếp nhận và phân tích các góp ý của giảng viên hướng dẫn về Chương 2. Thực hiện các chỉnh sửa cần thiết để đáp ứng các yêu cầu và góp ý của giảng viên hướng dẫn. Đảm bảo Chương 2 được hoàn thiện và đáp ứng các tiêu chuẩn của luận văn thạc sĩ.
- **O1-KR2.t1**: Nghiên cứu kỹ bộ intent đã được thống nhất và hướng dẫn gán nhãn chi tiết. Đảm bảo hiểu rõ tiêu chí và cách áp dụng để gán nhãn nhất quán.
- **O1-KR2.t2**: Gán nhãn 500 câu hội thoại đầu tiên từ tập dữ liệu 3000 câu. Tập trung vào việc áp dụng đúng hướng dẫn và đảm bảo chất lượng gán nhãn.
- **O1-KR2.t3**: Gán nhãn 500 câu hội thoại tiếp theo từ tập dữ liệu 3000 câu. Điều chỉnh cách gán nhãn dựa trên kinh nghiệm từ 500 câu hội thoại đầu tiên.
- **O1-KR2.t4**: Gán nhãn 500 câu hội thoại tiếp theo từ tập dữ liệu 3000 câu. Tiếp tục điều chỉnh cách gán nhãn dựa trên kinh nghiệm.
- **O1-KR2.t5**: Gán nhãn 500 câu hội thoại tiếp theo từ tập dữ liệu 3000 câu. Đảm bảo tính nhất quán và chất lượng của dữ liệu đã gán nhãn.
- **O1-KR2.t6**: Kiểm tra kỹ lưỡng 1000 câu hội thoại đầu tiên đã gán nhãn để phát hiện và sửa các lỗi gán nhãn. Đảm bảo tính chính xác và nhất quán của dữ liệu.
- **O1-KR2.t7**: Gán nhãn 500 câu hội thoại cuối cùng từ tập dữ liệu 3000 câu. Đảm bảo chất lượng và tính nhất quán của dữ liệu.
- **O1-KR3.t1**: Nghiên cứu các thuật toán hoặc kiến trúc học sâu khác nhau (ví dụ: Transformer, BERT, RoBERTa) có thể cải thiện hiệu suất phân loại ý định. Thử nghiệm các mô hình này trên tập dữ liệu hiện có và đánh giá kết quả. Tập trung vào các phương pháp có thể được tích hợp vào pipeline hiện tại.
- **O1-KR3.t2**: Thử nghiệm các tham số khác nhau cho mô hình TF-IDF + SVM hiện tại. Điều chỉnh các tham số như C, kernel, gamma để tối ưu hóa hiệu suất trên tập test.  Tìm hiểu các kỹ thuật feature engineering có thể cải thiện chất lượng dữ liệu đầu vào.
- **O1-KR3.t3**: Thử nghiệm kết hợp các mô hình khác nhau (ví dụ: TF-IDF + SVM với một mô hình học sâu) để cải thiện hiệu suất tổng thể.  Nghiên cứu các phương pháp ensemble khác nhau (ví dụ: voting, stacking, blending).
- **O1-KR3.t4**: Đánh giá hiệu suất của tất cả các mô hình đã thử nghiệm trên tập test. Lựa chọn mô hình có hiệu suất tốt nhất dựa trên macro-F1 score.  Phân tích chi tiết các trường hợp mà mô hình hoạt động kém.
- **O1-KR3.t5**: Tối ưu hóa và tinh chỉnh mô hình đã chọn để đạt được hiệu suất cao nhất có thể. Điều chỉnh các tham số, thử nghiệm các kỹ thuật regularization, và đảm bảo mô hình hoạt động ổn định trên tập test.
- **O1-KR3.t6**: Viết báo cáo chi tiết về quá trình thực nghiệm, bao gồm các mô hình đã thử nghiệm, kết quả thử nghiệm, phân tích ưu nhược điểm, và kết luận.  Đảm bảo báo cáo tuân thủ các yêu cầu của luận văn thạc sĩ.
- **O2-KR1.t1**: Nghiên cứu các bài báo hội thảo tương tự, xác định các tiêu chí và cấu trúc phù hợp cho bài báo của mình. Lên dàn ý chi tiết cho bài báo, bao gồm các phần chính như giới thiệu, phương pháp, kết quả, thảo luận và kết luận.
- **O2-KR1.t2**: Viết phần giới thiệu, nêu bật tầm quan trọng của nghiên cứu, đặt vấn đề và giới thiệu tổng quan về các công trình liên quan. Đảm bảo phần giới thiệu rõ ràng, hấp dẫn và phù hợp với tiêu chí của hội thảo.
- **O2-KR1.t3**: Mô tả chi tiết phương pháp nghiên cứu được sử dụng, bao gồm tiền xử lý dữ liệu, lựa chọn mô hình (TF-IDF + SVM và các cải tiến khác), các tham số và các bước thực hiện. Đảm bảo phần này đủ chi tiết để người khác có thể tái hiện lại nghiên cứu.
- **O2-KR1.t4**: Trình bày kết quả đạt được một cách rõ ràng và khách quan. Sử dụng các bảng biểu, đồ thị để minh họa kết quả. Phân tích kết quả và so sánh với baseline (TF-IDF + SVM).
- **O2-KR1.t5**: Thảo luận về ý nghĩa của kết quả, so sánh với các nghiên cứu khác, chỉ ra những hạn chế của nghiên cứu và đề xuất hướng nghiên cứu tiếp theo. Viết kết luận tóm tắt những điểm chính của nghiên cứu.
- **O2-KR1.t6**: Đọc lại toàn bộ bài báo, kiểm tra lỗi chính tả, ngữ pháp và định dạng. Đảm bảo bài báo tuân thủ các yêu cầu của hội thảo. Chỉnh sửa và hoàn thiện bài báo dựa trên phản hồi từ người hướng dẫn.
- **O2-KR1.t7**: Liệt kê đầy đủ các tài liệu tham khảo theo đúng định dạng của hội thảo. Kiểm tra tính chính xác của các thông tin tham khảo.
- **O2-KR1.t8**: Nộp bài báo hội thảo qua hệ thống của hội thảo trước hạn chót.
- **O2-KR2.t1**: Tổng hợp và tóm tắt các kết quả nghiên cứu chính, bao gồm phương pháp, kết quả đạt được so với baseline (TF-IDF + SVM), và các hướng cải tiến tiềm năng.  Tập trung vào những điểm mới và đóng góp của nghiên cứu.  Đảm bảo nội dung trình bày dễ hiểu cho người nghe không chuyên.
- **O2-KR2.t2**: Thiết kế slide trình bày trực quan, hấp dẫn, và dễ theo dõi. Sử dụng hình ảnh, biểu đồ, và đồ thị để minh họa các kết quả nghiên cứu. Đảm bảo slide có cấu trúc rõ ràng và nhất quán.
- **O2-KR2.t3**: Luyện tập trình bày nội dung trước người hướng dẫn hoặc đồng nghiệp để nhận phản hồi và cải thiện kỹ năng trình bày. Chú trọng vào tốc độ, ngữ điệu, và sự tự tin.
- **O2-KR2.t4**: Dự đoán các câu hỏi có thể được đặt ra trong seminar và chuẩn bị sẵn các câu trả lời rõ ràng, chính xác, và đầy đủ.  Nghiên cứu kỹ các điểm có thể gây tranh cãi hoặc hiểu lầm.
- **O2-KR2.t5**: Tham gia seminar của nhóm nghiên cứu và trình bày kết quả nghiên cứu theo kế hoạch. Trả lời các câu hỏi của người nghe một cách tự tin và chuyên nghiệp.
