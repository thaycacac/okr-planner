# Plan Mc88b — sample 01_saas_onboarding_vi

- Pipeline status: `ok`

## Tasks (34 tasks, 131 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 2 | — | Xác định tiêu chí và phạm vi cho activation | Định nghĩa tiêu chí activation và phạm vi người dùng được ghi lại trong tài liệu. |
| O1-KR1.t2 | O1-KR1 | 3 | O1-KR1.t1 | Lên kế hoạch nội dung onboarding | Kế hoạch nội dung onboarding được ghi lại trong tài liệu. |
| O1-KR1.t7 | O1-KR1 | 3 | O1-KR3.t4 | Cải tiến hướng dẫn in-app dựa trên phản hồi | Hướng dẫn in-app được cải tiến và lưu trữ trong hệ thống. |
| O1-KR1.t10 | O1-KR1 | 3 | O1-KR3.t7 | Đánh giá kết quả và điều chỉnh | Kết quả được đánh giá và điều chỉnh nếu cần thiết trong báo cáo. |
| O1-KR2.t1 | O1-KR2 | 2 | — | Xác định tiêu chí và phạm vi cho time-to-first-value | Danh sách các bước onboarding và thời điểm đo time-to-first-value được xác định rõ ràng. |
| O1-KR2.t2 | O1-KR2 | 3 | O1-KR2.t1 | Thu thập dữ liệu baseline về time-to-first-value | Dữ liệu baseline trung vị của time-to-first-value được phân tích và ghi lại. |
| O1-KR2.t4 | O1-KR2 | 6 | O1-KR3.t2, O1-KR1.t2 | Thực hiện cải thiện bước 1-3 của onboarding | 3 bước đầu tiên trong onboarding đã được tối ưu và kiểm tra. |
| O1-KR2.t5 | O1-KR2 | 3 | O1-KR2.t4 | Kiểm tra hiệu quả bước 1-3 sau cải thiện | Time-to-first-value trung vị sau cải thiện được đo và ghi lại. |
| O1-KR2.t6 | O1-KR2 | 6 | O1-KR2.t5 | Thực hiện cải thiện bước 4-6 của onboarding | 3 bước tiếp theo trong onboarding đã được tối ưu và kiểm tra. |
| O1-KR2.t7 | O1-KR2 | 3 | O1-KR2.t6 | Kiểm tra hiệu quả bước 4-6 sau cải thiện | Time-to-first-value trung vị sau cải thiện được đo và ghi lại. |
| O1-KR2.t8 | O1-KR2 | 3 | O1-KR2.t7 | Tổng hợp kết quả và đánh giá tiến độ | Kết quả đo lường và đánh giá đạt mục tiêu được tổng hợp và ghi lại. |
| O1-KR3.t1 | O1-KR3 | 2 | — | Xác định 3 luồng chính cần hướng dẫn | Danh sách 3 luồng chính được xác định và ghi lại trong tài liệu. |
| O1-KR3.t2 | O1-KR3 | 4 | O1-KR3.t1, O1-KR2.t2 | Lên kế hoạch nội dung cho từng luồng | Nội dung hướng dẫn cho 3 luồng được viết và lưu trữ trong tài liệu. |
| O1-KR3.t3 | O1-KR3 | 4 | O1-KR3.t2, O1-KR1.t2, O1-KR3.t1 | Thiết kế giao diện hướng dẫn in-app | Giao diện hướng dẫn in-app được thiết kế và lưu trữ trong tài liệu. |
| O1-KR3.t4 | O1-KR3 | 4 | O1-KR3.t3 | Thử nghiệm với người dùng thực tế | Phản hồi từ 5 người dùng được ghi lại và phân tích. |
| O1-KR3.t5 | O1-KR3 | 4 | O1-KR3.t4 | Chỉnh sửa dựa trên phản hồi | Hướng dẫn in-app được chỉnh sửa và lưu trữ trong tài liệu. |
| O1-KR3.t6 | O1-KR3 | 2 | O1-KR3.t5, O1-KR1.t7 | Ra mắt hướng dẫn in-app | Hướng dẫn in-app được triển khai và sẵn sàng sử dụng. |
| O1-KR3.t7 | O1-KR3 | 4 | O1-KR3.t6 | Đo lường hiệu quả hướng dẫn | Dữ liệu đo lường được thu thập và phân tích. |
| O2-KR1.t1 | O2-KR1 | 2 | — | Xác định tiêu chí và phạm vi cho việc giảm churn | Danh sách tiêu chí và phạm vi được xác định rõ ràng trong tài liệu. |
| O2-KR1.t2 | O2-KR1 | 3 | O2-KR1.t1 | Thu thập dữ liệu churn tháng đầu | Tệp dữ liệu chứa thông tin về các tài khoản rời bỏ trong tháng đầu được tạo ra. |
| O2-KR1.t3 | O2-KR1 | 4 | O2-KR1.t2 | Phân tích nguyên nhân churn | Báo cáo phân tích nguyên nhân churn tháng đầu được hoàn thành. |
| O2-KR1.t4 | O2-KR1 | 4 | O2-KR1.t3 | Thiết kế chiến lược giảm churn | Chiến lược giảm churn được trình bày trong tài liệu và được phê duyệt. |
| O2-KR1.t5 | O2-KR1 | 3 | O2-KR1.t4 | Triển khai chiến lược giảm churn trong tuần đầu | Các biện pháp đầu tiên trong chiến lược giảm churn được triển khai. |
| O2-KR1.t6 | O2-KR1 | 3 | O2-KR1.t5 | Triển khai chiến lược giảm churn trong tuần thứ hai | Các biện pháp tiếp theo trong chiến lược giảm churn được triển khai. |
| O2-KR1.t7 | O2-KR1 | 3 | O2-KR1.t6 | Triển khai chiến lược giảm churn trong tuần thứ ba | Các biện pháp cuối cùng trong chiến lược giảm churn được triển khai. |
| O2-KR1.t8 | O2-KR1 | 3 | O2-KR1.t7 | Đánh giá kết quả sau 1 tháng | Tỉ lệ churn tháng đầu được đo lường và so sánh với mục tiêu. |
| O2-KR2.t1 | O2-KR2 | 3 | — | Lên kế hoạch phỏng vấn và xác định tiêu chí chọn khách hàng | Danh sách 15 khách hàng rời bỏ và tiêu chí chọn người phỏng vấn được xác định rõ ràng. |
| O2-KR2.t2 | O2-KR2 | 6 | O2-KR2.t1 | Phỏng vấn nhóm 1-3 khách hàng rời bỏ | Hoàn thành 5 nhóm phỏng vấn, mỗi nhóm 3 khách hàng, ghi chú lại kết quả. |
| O2-KR2.t3 | O2-KR2 | 6 | O2-KR2.t2 | Phỏng vấn nhóm 4-6 khách hàng rời bỏ | Hoàn thành 5 nhóm phỏng vấn, mỗi nhóm 3 khách hàng, ghi chú lại kết quả. |
| O2-KR2.t4 | O2-KR2 | 6 | O2-KR2.t3 | Phỏng vấn nhóm 7-9 khách hàng rời bỏ | Hoàn thành 5 nhóm phỏng vấn, mỗi nhóm 3 khách hàng, ghi chú lại kết quả. |
| O2-KR2.t5 | O2-KR2 | 6 | O2-KR2.t4 | Phỏng vấn nhóm 10-12 khách hàng rời bỏ | Hoàn thành 5 nhóm phỏng vấn, mỗi nhóm 3 khách hàng, ghi chú lại kết quả. |
| O2-KR2.t6 | O2-KR2 | 6 | O2-KR2.t5 | Tổng hợp insight từ 15 cuộc phỏng vấn | Báo cáo tổng hợp insight từ 15 cuộc phỏng vấn được hoàn thành. |
| O2-KR2.t7 | O2-KR2 | 6 | O2-KR2.t6 | Kiểm tra và đánh giá báo cáo | Báo cáo được kiểm tra và đánh giá đạt yêu cầu. |
| O2-KR2.t8 | O2-KR2 | 6 | O2-KR2.t7 | Phân tích kết quả và đưa ra đề xuất cải thiện | Đề xuất cải thiện để giảm churn được trình bày rõ ràng trong báo cáo. |

### Descriptions

- **O1-KR1.t1**: Định nghĩa rõ tiêu chí activation và xác định phạm vi người dùng cần theo dõi.
- **O1-KR1.t2**: Lên kế hoạch nội dung onboarding cho 3 luồng chính: nhập hàng, xuất hàng, kiểm kê.
- **O1-KR1.t7**: Cải tiến hướng dẫn in-app dựa trên phản hồi từ 5 người dùng.
- **O1-KR1.t10**: Đánh giá kết quả sau triển khai và điều chỉnh nếu cần thiết.
- **O1-KR2.t1**: Lập danh sách các bước chính trong onboarding và xác định thời điểm đo time-to-first-value.
- **O1-KR2.t2**: Phân tích dữ liệu hiện tại để xác định baseline trung vị của time-to-first-value.
- **O1-KR2.t4**: Tối ưu 3 bước đầu tiên trong quy trình onboarding để giúp người dùng đạt được giá trị nhanh hơn.
- **O1-KR2.t5**: Đo thời gian trung vị của time-to-first-value sau khi tối ưu 3 bước đầu tiên.
- **O1-KR2.t6**: Tối ưu 3 bước tiếp theo trong quy trình onboarding để giúp người dùng đạt được giá trị nhanh hơn.
- **O1-KR2.t7**: Đo thời gian trung vị của time-to-first-value sau khi tối ưu 3 bước tiếp theo.
- **O1-KR2.t8**: Tổng hợp dữ liệu đo lường và đánh giá xem time-to-first-value có đạt mục tiêu 1 ngày hay không.
- **O1-KR3.t1**: Lập danh sách 3 luồng chính: nhập hàng, xuất hàng, kiểm kê dựa trên dữ liệu người dùng.
- **O1-KR3.t2**: Viết nội dung hướng dẫn cho từng luồng, đảm bảo rõ ràng và dễ hiểu.
- **O1-KR3.t3**: Tạo giao diện và bố trí các bước hướng dẫn cho từng luồng.
- **O1-KR3.t4**: Thử nghiệm hướng dẫn với 5 người dùng mới để đánh giá hiệu quả.
- **O1-KR3.t5**: Cập nhật nội dung và giao diện dựa trên phản hồi từ người dùng thử nghiệm.
- **O1-KR3.t6**: Đưa hướng dẫn in-app ra mắt cho người dùng mới.
- **O1-KR3.t7**: Theo dõi tỉ lệ activation và time-to-first-value sau khi triển khai hướng dẫn.
- **O2-KR1.t1**: Định nghĩa rõ các yếu tố ảnh hưởng đến churn tháng đầu và xác định nhóm khách hàng mục tiêu.
- **O2-KR1.t2**: Tổng hợp dữ liệu về các tài khoản rời bỏ trong tháng đầu sử dụng.
- **O2-KR1.t3**: Phân tích dữ liệu để xác định các nguyên nhân chính gây ra churn tháng đầu.
- **O2-KR1.t4**: Lên kế hoạch các biện pháp cụ thể để giảm tỉ lệ churn từ 9% xuống 6%.
- **O2-KR1.t5**: Thực hiện các biện pháp đã lên kế hoạch để giảm churn trong tuần đầu tiên.
- **O2-KR1.t6**: Tiếp tục triển khai các biện pháp đã lên kế hoạch để giảm churn trong tuần thứ hai.
- **O2-KR1.t7**: Tiếp tục triển khai các biện pháp đã lên kế hoạch để giảm churn trong tuần thứ ba.
- **O2-KR1.t8**: Kiểm tra lại tỉ lệ churn sau khi triển khai chiến lược.
- **O2-KR2.t1**: Xác định danh sách 15 khách hàng rời bỏ và tiêu chí chọn người phỏng vấn.
- **O2-KR2.t2**: Thực hiện 5 nhóm phỏng vấn, mỗi nhóm 3 khách hàng rời bỏ.
- **O2-KR2.t3**: Thực hiện 5 nhóm phỏng vấn, mỗi nhóm 3 khách hàng rời bỏ.
- **O2-KR2.t4**: Thực hiện 5 nhóm phỏng vấn, mỗi nhóm 3 khách hàng rời bỏ.
- **O2-KR2.t5**: Thực hiện 5 nhóm phỏng vấn, mỗi nhóm 3 khách hàng rời bỏ.
- **O2-KR2.t6**: Tổng hợp các insight từ 15 cuộc phỏng vấn thành báo cáo.
- **O2-KR2.t7**: Kiểm tra lại báo cáo để đảm bảo tính chính xác và đầy đủ.
- **O2-KR2.t8**: Phân tích insight và đưa ra đề xuất cải thiện để giảm churn.
