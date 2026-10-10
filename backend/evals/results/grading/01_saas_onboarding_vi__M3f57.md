# Plan M3f57 — sample 01_saas_onboarding_vi

- Pipeline status: `ok`

## Tasks (38 tasks, 158 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 4 | — | Phân tích dữ liệu activation hiện tại | Báo cáo phân tích dữ liệu activation hiện tại được hoàn thành. |
| O1-KR1.t2 | O1-KR1 | 4 | O1-KR1.t1 | Xác định các điểm cần cải thiện trong onboarding | Danh sách các điểm cần cải thiện trong onboarding được hoàn thành. |
| O1-KR1.t3 | O1-KR1 | 6 | O1-KR1.t2, O1-KR2.t3, O1-KR3.t1 | Thiết kế lại quy trình onboarding | Phiên bản mới của quy trình onboarding được hoàn thành. |
| O1-KR1.t4 | O1-KR1 | 6 | O1-KR1.t3, O1-KR3.t1 | Tạo nội dung hướng dẫn người dùng mới | Tài liệu hướng dẫn người dùng mới được hoàn thành. |
| O1-KR1.t5 | O1-KR1 | 4 | O1-KR1.t4, O1-KR1.t3 | Thử nghiệm A/B với quy trình onboarding mới | Thiết lập A/B test cho quy trình onboarding mới được hoàn thành. |
| O1-KR1.t6 | O1-KR1 | 4 | O1-KR1.t5 | Thu thập phản hồi từ người dùng thử nghiệm | Báo cáo phản hồi từ người dùng thử nghiệm được hoàn thành. |
| O1-KR1.t7 | O1-KR1 | 6 | O1-KR1.t6, O1-KR2.t6 | Tối ưu quy trình onboarding dựa trên phản hồi | Phiên bản tối ưu của quy trình onboarding được hoàn thành. |
| O1-KR1.t8 | O1-KR1 | 4 | O1-KR1.t7 | Triển khai quy trình onboarding mới cho toàn bộ người dùng | Quy trình onboarding mới được triển khai cho toàn bộ người dùng mới. |
| O1-KR1.t9 | O1-KR1 | 4 | O1-KR1.t8 | Theo dõi tỉ lệ activation trong 7 ngày | Báo cáo tỉ lệ activation trong 7 ngày được hoàn thành. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Phân tích dữ liệu hiện tại về time-to-first-value | Báo cáo phân tích dữ liệu hiện tại được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O1-KR2.t2 | O1-KR2 | 4 | O1-KR2.t1 | Xác định các điểm nghẽn trong quy trình onboarding | Danh sách các điểm nghẽn được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O1-KR2.t3 | O1-KR2 | 4 | O1-KR2.t2, O1-KR3.t1 | Thiết kế bản đồ trải nghiệm người dùng mới | Bản đồ trải nghiệm người dùng mới được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O1-KR2.t6 | O1-KR2 | 4 | O1-KR1.t5 | Thu thập phản hồi từ nhóm thử nghiệm | Báo cáo phản hồi từ nhóm thử nghiệm được lưu trữ trong hệ thống chia sẻ nội bộ và có ít nhất 10 phản hồi từ người dùng. |
| O1-KR2.t9 | O1-KR2 | 4 | O1-KR1.t8 | Theo dõi và đo lường time-to-first-value trung vị | Báo cáo đo lường time-to-first-value trung vị được lưu trữ trong hệ thống chia sẻ nội bộ và có số liệu trung vị sau triển khai là 1.5 ngày. |
| O1-KR3.t1 | O1-KR3 | 4 | — | Xác định 3 luồng chính và nội dung hướng dẫn in-app cho từng luồng | 3 luồng chính được xác định và nội dung hướng dẫn in-app cho từng luồng được ghi lại trong tài liệu. |
| O1-KR3.t3 | O1-KR3 | 4 | O1-KR1.t4 | Xây dựng prototype hướng dẫn in-app cho luồng nhập hàng | Prototype hướng dẫn in-app cho luồng nhập hàng được hoàn thành và có thể chạy thử. |
| O1-KR3.t4 | O1-KR3 | 4 | O1-KR1.t4 | Xây dựng prototype hướng dẫn in-app cho luồng xuất hàng | Prototype hướng dẫn in-app cho luồng xuất hàng được hoàn thành và có thể chạy thử. |
| O1-KR3.t5 | O1-KR3 | 4 | O1-KR1.t4 | Xây dựng prototype hướng dẫn in-app cho luồng kiểm kê | Prototype hướng dẫn in-app cho luồng kiểm kê được hoàn thành và có thể chạy thử. |
| O1-KR3.t6 | O1-KR3 | 4 | O1-KR3.t3, O1-KR3.t4, O1-KR3.t5 | Kiểm thử prototype hướng dẫn in-app với nhóm người dùng thử nghiệm | Phản hồi từ nhóm người dùng thử nghiệm được thu thập và lưu trữ trong tài liệu. |
| O1-KR3.t7 | O1-KR3 | 4 | O1-KR3.t6 | Tổng hợp phản hồi và điều chỉnh prototype hướng dẫn in-app | Prototype hướng dẫn in-app được điều chỉnh dựa trên phản hồi từ người dùng thử nghiệm. |
| O1-KR3.t8 | O1-KR3 | 4 | O1-KR3.t7 | Hoàn thiện và tích hợp hướng dẫn in-app vào sản phẩm | Hướng dẫn in-app được tích hợp vào sản phẩm và có thể chạy được. |
| O1-KR3.t9 | O1-KR3 | 4 | O1-KR3.t8 | Ra mắt hướng dẫn in-app cho người dùng mới | Hướng dẫn in-app được kích hoạt và hiển thị cho người dùng mới khi họ truy cập sản phẩm. |
| O1-KR3.t10 | O1-KR3 | 4 | O1-KR3.t9 | Theo dõi và đo lường hiệu quả của hướng dẫn in-app | Dữ liệu về hiệu quả của hướng dẫn in-app được thu thập và lưu trữ trong báo cáo. |
| O2-KR1.t1 | O2-KR1 | 4 | — | Phân tích dữ liệu churn hiện tại | Báo cáo phân tích dữ liệu hiện tại được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O2-KR1.t2 | O2-KR1 | 4 | O2-KR1.t1, O2-KR2.t6 | Xác định các điểm đau chính của người dùng mới | Danh sách các điểm đau chính được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O2-KR1.t3 | O2-KR1 | 4 | O2-KR1.t2, O2-KR2.t6 | Thiết kế các giải pháp cải thiện trải nghiệm người dùng mới | Tài liệu đề xuất cải thiện trải nghiệm người dùng mới được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O2-KR1.t4 | O2-KR1 | 4 | O2-KR1.t3 | Triển khai các cải tiến nhỏ để thử nghiệm | Các cải tiến nhỏ đã được triển khai và ghi nhận trong hệ thống theo dõi. |
| O2-KR1.t5 | O2-KR1 | 4 | O2-KR1.t4 | Theo dõi và đánh giá hiệu quả của các cải tiến | Báo cáo hiệu quả của các cải tiến được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O2-KR1.t6 | O2-KR1 | 4 | O2-KR1.t5 | Tối ưu hóa các giải pháp dựa trên dữ liệu thử nghiệm | Tài liệu tối ưu hóa các giải pháp được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O2-KR1.t7 | O2-KR1 | 4 | O2-KR1.t6 | Triển khai các giải pháp tối ưu hóa | Các giải pháp tối ưu hóa đã được triển khai và ghi nhận trong hệ thống theo dõi. |
| O2-KR1.t8 | O2-KR1 | 4 | O2-KR1.t7 | Theo dõi tỉ lệ churn tháng đầu sau khi triển khai | Báo cáo tỉ lệ churn tháng đầu sau triển khai được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O2-KR1.t9 | O2-KR1 | 4 | O2-KR1.t8 | Đánh giá hiệu quả cuối kỳ và điều chỉnh nếu cần | Báo cáo đánh giá hiệu quả cuối kỳ được lưu trữ trong hệ thống chia sẻ nội bộ. |
| O2-KR2.t1 | O2-KR2 | 4 | — | Xác định danh sách khách hàng rời bỏ và chuẩn bị công cụ phỏng vấn | Danh sách 15 khách hàng rời bỏ được xác định và công cụ phỏng vấn được chuẩn bị sẵn sàng |
| O2-KR2.t2 | O2-KR2 | 4 | O2-KR2.t1 | Phỏng vấn 3 khách hàng đầu tiên và ghi lại insight | 3 cuộc phỏng vấn được thực hiện và các insight được ghi lại trong tài liệu |
| O2-KR2.t3 | O2-KR2 | 4 | O2-KR2.t2 | Phỏng vấn 3 khách hàng tiếp theo và tổng hợp insight | 3 cuộc phỏng vấn được thực hiện và insight được tổng hợp trong tài liệu |
| O2-KR2.t4 | O2-KR2 | 4 | O2-KR2.t3 | Phỏng vấn 3 khách hàng tiếp theo và ghi lại insight | 3 cuộc phỏng vấn được thực hiện và các insight được ghi lại trong tài liệu |
| O2-KR2.t5 | O2-KR2 | 4 | O2-KR2.t4 | Phỏng vấn 3 khách hàng cuối cùng và tổng hợp insight | 3 cuộc phỏng vấn được thực hiện và insight được tổng hợp trong tài liệu |
| O2-KR2.t6 | O2-KR2 | 4 | O2-KR2.t5 | Tổng hợp và phân tích insight từ 15 cuộc phỏng vấn | Tài liệu tổng hợp insight từ 15 cuộc phỏng vấn được hoàn thành và đưa ra các đề xuất cải thiện |

### Descriptions

- **O1-KR1.t1**: Xem xét dữ liệu activation hiện tại để xác định các điểm nghẽn.
- **O1-KR1.t2**: Dựa trên phân tích dữ liệu, xác định các điểm cần cải thiện trong quy trình onboarding.
- **O1-KR1.t3**: Thiết kế lại quy trình onboarding dựa trên các điểm cần cải thiện.
- **O1-KR1.t4**: Tạo nội dung hướng dẫn người dùng mới cho từng bước trong quy trình onboarding.
- **O1-KR1.t5**: Triển khai quy trình onboarding mới cho một nhóm người dùng và so sánh với nhóm đối chứng.
- **O1-KR1.t6**: Thu thập phản hồi từ người dùng thử nghiệm quy trình onboarding mới.
- **O1-KR1.t7**: Tối ưu quy trình onboarding dựa trên phản hồi từ người dùng thử nghiệm.
- **O1-KR1.t8**: Triển khai quy trình onboarding mới cho toàn bộ người dùng mới.
- **O1-KR1.t9**: Theo dõi tỉ lệ activation trong 7 ngày sau khi triển khai quy trình onboarding mới.
- **O1-KR2.t1**: Thu thập và phân tích dữ liệu hiện tại để xác định nguyên nhân làm chậm time-to-first-value.
- **O1-KR2.t2**: Dựa trên phân tích dữ liệu, xác định các bước gây khó khăn cho người dùng mới.
- **O1-KR2.t3**: Tạo bản đồ trải nghiệm người dùng mới dựa trên các điểm nghẽn đã xác định.
- **O1-KR2.t6**: Thu thập phản hồi từ người dùng thử nghiệm về quy trình onboarding mới.
- **O1-KR2.t9**: Theo dõi và đo lường time-to-first-value trung vị trước và sau khi triển khai quy trình mới.
- **O1-KR3.t1**: Xác định 3 luồng chính (nhập hàng, xuất hàng, kiểm kê) và nội dung hướng dẫn in-app cần thiết cho từng luồng.
- **O1-KR3.t3**: Xây dựng prototype hướng dẫn in-app cho luồng nhập hàng.
- **O1-KR3.t4**: Xây dựng prototype hướng dẫn in-app cho luồng xuất hàng.
- **O1-KR3.t5**: Xây dựng prototype hướng dẫn in-app cho luồng kiểm kê.
- **O1-KR3.t6**: Kiểm thử prototype hướng dẫn in-app với nhóm người dùng thử nghiệm để thu thập phản hồi.
- **O1-KR3.t7**: Tổng hợp phản hồi từ người dùng thử nghiệm và điều chỉnh prototype hướng dẫn in-app.
- **O1-KR3.t8**: Hoàn thiện hướng dẫn in-app và tích hợp vào sản phẩm.
- **O1-KR3.t9**: Ra mắt hướng dẫn in-app cho người dùng mới trên toàn bộ sản phẩm.
- **O1-KR3.t10**: Theo dõi và đo lường hiệu quả của hướng dẫn in-app trong quá trình sử dụng của người dùng mới.
- **O2-KR1.t1**: Xem xét dữ liệu người dùng rời bỏ trong tháng đầu sử dụng để xác định các mô hình và nguyên nhân tiềm năng.
- **O2-KR1.t2**: Tổng hợp các phản hồi từ người dùng mới và các điểm đau trong quá trình sử dụng sản phẩm.
- **O2-KR1.t3**: Tạo các đề xuất cải thiện trải nghiệm người dùng mới dựa trên phân tích và điểm đau đã xác định.
- **O2-KR1.t4**: Triển khai các cải tiến nhỏ để thử nghiệm tác động đến tỉ lệ churn.
- **O2-KR1.t5**: Theo dõi tỉ lệ churn trong tháng đầu sau khi triển khai các cải tiến và đánh giá hiệu quả.
- **O2-KR1.t6**: Tối ưu hóa các giải pháp dựa trên dữ liệu và phản hồi từ thử nghiệm.
- **O2-KR1.t7**: Triển khai các giải pháp tối ưu hóa để cải thiện tỉ lệ churn tháng đầu.
- **O2-KR1.t8**: Theo dõi tỉ lệ churn tháng đầu sau khi triển khai các giải pháp tối ưu hóa.
- **O2-KR1.t9**: Đánh giá hiệu quả của các giải pháp trong suốt quý và điều chỉnh nếu cần thiết.
- **O2-KR2.t1**: Xác định danh sách 15 khách hàng rời bỏ và chuẩn bị công cụ phỏng vấn (phỏng vấn qua Zoom, Google Forms, hoặc email)
- **O2-KR2.t2**: Tiến hành phỏng vấn 3 khách hàng rời bỏ và ghi lại các insight từ cuộc phỏng vấn
- **O2-KR2.t3**: Tiến hành phỏng vấn 3 khách hàng rời bỏ tiếp theo và tổng hợp insight từ các cuộc phỏng vấn
- **O2-KR2.t4**: Tiến hành phỏng vấn 3 khách hàng rời bỏ tiếp theo và ghi lại các insight từ cuộc phỏng vấn
- **O2-KR2.t5**: Tiến hành phỏng vấn 3 khách hàng rời bỏ cuối cùng và tổng hợp insight từ các cuộc phỏng vấn
- **O2-KR2.t6**: Tổng hợp và phân tích các insight từ 15 cuộc phỏng vấn để đưa ra các đề xuất cải thiện
