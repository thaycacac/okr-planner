# Plan Mc88b — sample 03_health_fitness_vi

- Pipeline status: `ok`

## Tasks (27 tasks, 63 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 2 | — | Xác định mục tiêu và kế hoạch chạy 5 km | Kế hoạch chạy 5 km với các mục tiêu cụ thể và lịch tập được xác định rõ ràng. |
| O1-KR1.t2 | O1-KR1 | 3 | O1-KR1.t1 | Chuẩn bị dụng cụ và địa điểm chạy, đồng thời chạy thử để đánh giá khả năng hiện tại | Địa điểm chạy và dụng cụ đã được xác định và chuẩn bị sẵn sàng, kết quả chạy thử 5 km được ghi lại và phân tích để xác định điểm cần cải thiện. |
| O1-KR1.t3 | O1-KR1 | 2 | O1-KR1.t2 | Lập lịch chạy tập trung vào tăng tốc và cải thiện sức bền | Lịch chạy 5 km với các buổi tập tăng tốc được lập và phân bổ hợp lý. |
| O1-KR1.t4 | O1-KR1 | 2 | O1-KR1.t3 | Theo dõi tiến trình và điều chỉnh kế hoạch | Thời gian chạy 5 km được theo dõi mỗi tuần và kế hoạch được điều chỉnh nếu cần. |
| O1-KR1.t5 | O1-KR1 | 2 | O1-KR1.t4 | Kiểm tra kết quả cuối kỳ và đánh giá hiệu quả | Kết quả chạy 5 km cuối kỳ được ghi lại và xác nhận đạt mục tiêu 30 phút. |
| O1-KR2.t1 | O1-KR2 | 2 | — | Lên kế hoạch tập sức mạnh | Kế hoạch tập sức mạnh được lập và gửi cho người quản lý. |
| O1-KR2.t2 | O1-KR2 | 2 | O1-KR2.t1 | Chuẩn bị dụng cụ và không gian tập | Dụng cụ và không gian tập đã được chuẩn bị sẵn sàng. |
| O1-KR2.t3 | O1-KR2 | 2 | O1-KR2.t1, O1-KR2.t2 | Tập sức mạnh buổi 1 | Ghi chú tập sức mạnh buổi 1 được cập nhật trong lịch tập. |
| O1-KR2.t4 | O1-KR2 | 2 | O1-KR2.t1, O1-KR2.t2 | Tập sức mạnh buổi 2 | Ghi chú tập sức mạnh buổi 2 được cập nhật trong lịch tập. |
| O1-KR2.t5 | O1-KR2 | 2 | O1-KR2.t3, O1-KR2.t4 | Đánh giá tiến độ sau 4 tuần | Số buổi tập sức mạnh đạt 8 buổi trong 4 tuần. |
| O1-KR2.t6 | O1-KR2 | 2 | O1-KR2.t1, O1-KR2.t2 | Tập sức mạnh buổi 3 | Ghi chú tập sức mạnh buổi 3 được cập nhật trong lịch tập. |
| O1-KR2.t7 | O1-KR2 | 2 | O1-KR2.t1, O1-KR2.t2 | Tập sức mạnh buổi 4 | Ghi chú tập sức mạnh buổi 4 được cập nhật trong lịch tập. |
| O1-KR2.t8 | O1-KR2 | 2 | O1-KR2.t6, O1-KR2.t7 | Đánh giá tiến độ sau 8 tuần | Số buổi tập sức mạnh đạt 16 buổi trong 8 tuần. |
| O1-KR2.t9 | O1-KR2 | 2 | O1-KR2.t1, O1-KR2.t2 | Tập sức mạnh buổi 5 | Ghi chú tập sức mạnh buổi 5 được cập nhật trong lịch tập. |
| O1-KR2.t10 | O1-KR2 | 2 | O1-KR2.t1, O1-KR2.t2 | Tập sức mạnh buổi 6 | Ghi chú tập sức mạnh buổi 6 được cập nhật trong lịch tập. |
| O1-KR2.t11 | O1-KR2 | 2 | O1-KR2.t9, O1-KR2.t10 | Đánh giá tiến độ sau 12 tuần | Số buổi tập sức mạnh đạt 24 buổi trong 12 tuần. |
| O2-KR1.t1 | O2-KR1 | 3 | — | Lên kế hoạch ăn uống | Thực đơn 4 tuần được lập và gửi cho chuyên gia dinh dưỡng để góp ý. |
| O2-KR1.t2 | O2-KR1 | 4 | O2-KR1.t1, O2-KR2.t6 | Chuẩn bị bữa ăn | Bữa ăn cho cả tuần được chuẩn bị và lưu trữ trong tủ lạnh. |
| O2-KR1.t3 | O2-KR1 | 2 | — | Theo dõi cân nặng | Cân nặng được ghi lại mỗi tuần trong sổ theo dõi. |
| O2-KR1.t4 | O2-KR1 | 3 | O2-KR1.t2, O2-KR2.t6 | Đánh giá thực đơn | Thực đơn được điều chỉnh dựa trên phản hồi và kết quả ăn uống. |
| O2-KR1.t5 | O2-KR1 | 2 | O2-KR1.t3, O2-KR1.t4 | Đánh giá kết quả | Kết quả sau 12 tuần được ghi lại và đánh giá xem có đạt mục tiêu hay không. |
| O2-KR2.t1 | O2-KR2 | 4 | — | Lên khung thực đơn 4 tuần | Một bảng Excel chứa 4 tuần thực đơn với các bữa ăn và loại thực phẩm được ghi rõ. |
| O2-KR2.t2 | O2-KR2 | 2 | O2-KR2.t1 | Tìm chuyên gia dinh dưỡng | Thông tin liên lạc và lịch hẹn với chuyên gia dinh dưỡng được xác nhận. |
| O2-KR2.t3 | O2-KR2 | 2 | O2-KR2.t2 | Gửi thực đơn để góp ý | Thực đơn được gửi qua email và có xác nhận nhận được. |
| O2-KR2.t4 | O2-KR2 | 4 | O2-KR2.t3 | Chỉnh sửa thực đơn theo góp ý | Thực đơn đã được chỉnh sửa và gửi lại cho chuyên gia để xác nhận. |
| O2-KR2.t5 | O2-KR2 | 2 | O2-KR2.t4 | Kiểm tra lại thực đơn | Thực đơn được kiểm tra và xác nhận đạt yêu cầu. |
| O2-KR2.t6 | O2-KR2 | 2 | O2-KR2.t5 | Lưu trữ và chia sẻ thực đơn | Thực đơn được lưu trữ trong Google Drive và chia sẻ với người dùng. |

### Descriptions

- **O1-KR1.t1**: Lập kế hoạch chi tiết để giảm thời gian chạy 5 km từ 38 phút xuống 30 phút.
- **O1-KR1.t2**: Lựa chọn địa điểm chạy phù hợp, chuẩn bị dụng cụ cần thiết và chạy thử 5 km để đánh giá thời gian hiện tại và xác định điểm yếu.
- **O1-KR1.t3**: Lập lịch chạy 3-4 lần mỗi tuần, tập trung vào tăng tốc và cải thiện sức bền.
- **O1-KR1.t4**: Theo dõi thời gian chạy 5 km mỗi tuần và điều chỉnh kế hoạch nếu cần.
- **O1-KR1.t5**: Chạy 5 km cuối kỳ để kiểm tra xem đã đạt mục tiêu 30 phút chưa và đánh giá hiệu quả của kế hoạch.
- **O1-KR2.t1**: Xác định lịch tập, bài tập và thời gian cho 2 buổi/tuần.
- **O1-KR2.t2**: Mua hoặc thuê dụng cụ cần thiết và chọn nơi tập phù hợp.
- **O1-KR2.t3**: Thực hiện buổi tập sức mạnh đầu tiên theo kế hoạch.
- **O1-KR2.t4**: Thực hiện buổi tập sức mạnh thứ hai theo kế hoạch.
- **O1-KR2.t5**: Kiểm tra số buổi tập đã hoàn thành và điều chỉnh kế hoạch nếu cần.
- **O1-KR2.t6**: Thực hiện buổi tập sức mạnh thứ ba theo kế hoạch.
- **O1-KR2.t7**: Thực hiện buổi tập sức mạnh thứ tư theo kế hoạch.
- **O1-KR2.t8**: Kiểm tra số buổi tập đã hoàn thành và điều chỉnh kế hoạch nếu cần.
- **O1-KR2.t9**: Thực hiện buổi tập sức mạnh thứ năm theo kế hoạch.
- **O1-KR2.t10**: Thực hiện buổi tập sức mạnh thứ sáu theo kế hoạch.
- **O1-KR2.t11**: Kiểm tra số buổi tập đã hoàn thành và xác nhận đạt mục tiêu.
- **O2-KR1.t1**: Xác định mục tiêu ăn uống, loại bỏ thực phẩm không lành mạnh và lên thực đơn 4 tuần.
- **O2-KR1.t2**: Chuẩn bị bữa ăn cho cả tuần theo thực đơn đã lên.
- **O2-KR1.t3**: Theo dõi cân nặng mỗi tuần và ghi lại vào sổ theo dõi.
- **O2-KR1.t4**: Đánh giá lại thực đơn sau 2 tuần và điều chỉnh nếu cần.
- **O2-KR1.t5**: Đánh giá kết quả sau 12 tuần và xác định xem có đạt mục tiêu giảm 5 kg hay không.
- **O2-KR2.t1**: Xác định các bữa ăn chính và phụ trong 4 tuần, đảm bảo cân bằng dinh dưỡng.
- **O2-KR2.t2**: Liên hệ và chọn một chuyên gia dinh dưỡng để góp ý thực đơn.
- **O2-KR2.t3**: Gửi bảng Excel thực đơn cho chuyên gia dinh dưỡng để nhận góp ý.
- **O2-KR2.t4**: Sửa đổi thực đơn dựa trên phản hồi từ chuyên gia dinh dưỡng.
- **O2-KR2.t5**: Đảm bảo thực đơn đáp ứng đủ nhu cầu dinh dưỡng và phù hợp với chế độ ăn.
- **O2-KR2.t6**: Lưu trữ thực đơn đã hoàn thiện và chia sẻ với người dùng.
