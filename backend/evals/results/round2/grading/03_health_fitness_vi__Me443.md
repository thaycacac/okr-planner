# Plan Me443 — sample 03_health_fitness_vi

- Pipeline status: `ok`

## Tasks (27 tasks, 97 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 3 | — | Xác định mục tiêu và kế hoạch chạy 5 km | Kế hoạch chạy 5 km đã được lập và xác nhận. |
| O1-KR1.t2 | O1-KR1 | 2 | O1-KR1.t1 | Chuẩn bị dữ liệu và theo dõi thời gian chạy | Thời gian chạy 5 km hiện tại đã được ghi lại và theo dõi. |
| O1-KR1.t3 | O1-KR1 | 4 | O1-KR1.t2 | Chạy thử nghiệm và điều chỉnh cường độ | Đã chạy thử nghiệm và điều chỉnh cường độ phù hợp. |
| O1-KR1.t4 | O1-KR1 | 6 | O1-KR1.t3 | Chạy 5 km theo kế hoạch: buổi 1-3 | Đã chạy 5 km theo kế hoạch trong 3 buổi đầu tiên. |
| O1-KR1.t5 | O1-KR1 | 6 | O1-KR1.t4 | Chạy 5 km theo kế hoạch: buổi 4-6 | Đã chạy 5 km theo kế hoạch trong 3 buổi tiếp theo. |
| O1-KR1.t6 | O1-KR1 | 6 | O1-KR1.t5 | Chạy 5 km theo kế hoạch: buổi 7-9 | Đã chạy 5 km theo kế hoạch trong 3 buổi cuối cùng. |
| O1-KR1.t7 | O1-KR1 | 2 | O1-KR1.t6 | Đánh giá kết quả và đo lường thời gian chạy | Thời gian chạy 5 km đã được đo lường và so sánh với mục tiêu. |
| O1-KR2.t1 | O1-KR2 | 3 | — | Lên kế hoạch tập sức mạnh 4 tuần | Kế hoạch tập sức mạnh 4 tuần đã được xác định rõ ràng và gửi cho người quản lý để phê duyệt. |
| O1-KR2.t2 | O1-KR2 | 3 | — | Chuẩn bị bữa ăn cho tập luyện | Thực đơn 4 tuần xoay vòng đã được gửi cho chuyên gia dinh dưỡng để góp ý. |
| O1-KR2.t3 | O1-KR2 | 6 | O1-KR2.t1 | Tập sức mạnh buổi sáng 2 buổi/tuần | Đã hoàn thành 2 buổi tập sức mạnh mỗi tuần trong 12 tuần. |
| O1-KR2.t4 | O1-KR2 | 6 | O1-KR2.t3 | Tập sức mạnh buổi sáng 2 buổi/tuần (tiếp theo) | Đã hoàn thành 2 buổi tập sức mạnh mỗi tuần trong 12 tuần. |
| O1-KR2.t5 | O1-KR2 | 6 | O1-KR2.t3 | Theo dõi tiến trình tập luyện | Đã theo dõi và đánh giá tiến trình tập luyện sau mỗi 4 tuần, đảm bảo duy trì 2 buổi/tuần. |
| O1-KR2.t6 | O1-KR2 | 2 | O1-KR2.t5 | Đánh giá kết quả cuối kỳ | Đã xác nhận số buổi tập sức mạnh mỗi tuần đạt 2 buổi/tuần sau 12 tuần. |
| O2-KR1.t1 | O2-KR1 | 2 | — | Xác định mục tiêu và kế hoạch ăn uống | Kế hoạch ăn uống 4 tuần được lập và gửi cho chuyên gia dinh dưỡng để góp ý. |
| O2-KR1.t2 | O2-KR1 | 3 | O2-KR1.t1 | Chuẩn bị thực đơn 4 tuần | Thực đơn 4 tuần được hoàn thành và gửi cho chuyên gia dinh dưỡng để góp ý. |
| O2-KR1.t3 | O2-KR1 | 3 | O2-KR1.t2 | Thực hiện thực đơn 4 tuần: Tuần 1 | Thực đơn được thực hiện đầy đủ trong tuần 1 và theo dõi. |
| O2-KR1.t4 | O2-KR1 | 3 | O2-KR1.t3 | Thực hiện thực đơn 4 tuần: Tuần 2 | Thực đơn được thực hiện đầy đủ trong tuần 2 và theo dõi. |
| O2-KR1.t5 | O2-KR1 | 3 | O2-KR1.t4 | Thực hiện thực đơn 4 tuần: Tuần 3 | Thực đơn được thực hiện đầy đủ trong tuần 3 và theo dõi. |
| O2-KR1.t6 | O2-KR1 | 3 | O2-KR1.t5 | Thực hiện thực đơn 4 tuần: Tuần 4 | Thực đơn được thực hiện đầy đủ trong tuần 4 và theo dõi. |
| O2-KR1.t7 | O2-KR1 | 5 | O2-KR1.t6 | Theo dõi cân nặng và điều chỉnh kế hoạch | Cân nặng được theo dõi mỗi tuần và kế hoạch ăn uống được điều chỉnh nếu cần. |
| O2-KR1.t8 | O2-KR1 | 2 | O2-KR1.t7 | Đo lường kết quả cuối kỳ | Cân nặng cuối kỳ được đo lường và so sánh với mục tiêu. |
| O2-KR2.t1 | O2-KR2 | 4 | — | Lên kế hoạch thực đơn 4 tuần xoay vòng | Kế hoạch thực đơn 4 tuần xoay vòng được lập ra và gửi cho chuyên gia dinh dưỡng để góp ý. |
| O2-KR2.t2 | O2-KR2 | 3 | O2-KR2.t1 | Chuẩn bị dữ liệu và tài liệu liên quan | Thông tin cần thiết về nhu cầu dinh dưỡng và sở thích ăn uống đã được thu thập và lưu trữ. |
| O2-KR2.t3 | O2-KR2 | 2 | O2-KR2.t1, O2-KR2.t2 | Gửi thực đơn 4 tuần xoay vòng cho chuyên gia dinh dưỡng | Thực đơn 4 tuần xoay vòng đã được gửi cho chuyên gia dinh dưỡng. |
| O2-KR2.t4 | O2-KR2 | 4 | O2-KR2.t3 | Chỉnh sửa thực đơn dựa trên góp ý của chuyên gia | Thực đơn 4 tuần xoay vòng đã được chỉnh sửa theo góp ý của chuyên gia dinh dưỡng. |
| O2-KR2.t5 | O2-KR2 | 3 | O2-KR2.t4 | Kiểm tra lại thực đơn để đảm bảo tính hợp lý | Thực đơn 4 tuần xoay vòng đã được kiểm tra và xác nhận là hợp lý. |
| O2-KR2.t6 | O2-KR2 | 2 | O2-KR2.t5 | Hoàn thiện và công bố thực đơn 4 tuần xoay vòng | Thực đơn 4 tuần xoay vòng đã được hoàn thiện và công bố. |

### Descriptions

- **O1-KR1.t1**: Lập kế hoạch chi tiết để giảm thời gian chạy 5 km từ 38 phút xuống 30 phút trong quý này, bao gồm lịch chạy, cường độ, và phương pháp cải thiện.
- **O1-KR1.t2**: Ghi lại thời gian chạy 5 km hiện tại (38 phút), và bắt đầu theo dõi thời gian chạy mỗi lần để đánh giá tiến trình.
- **O1-KR1.t3**: Chạy 5 km với cường độ tăng dần, theo dõi thời gian và điều chỉnh kế hoạch phù hợp.
- **O1-KR1.t4**: Thực hiện chạy 5 km theo kế hoạch đã lập, đảm bảo thời gian chạy giảm dần trong 3 buổi đầu tiên.
- **O1-KR1.t5**: Tiếp tục chạy 5 km theo kế hoạch đã lập, đảm bảo thời gian chạy giảm dần trong 3 buổi tiếp theo.
- **O1-KR1.t6**: Tiếp tục chạy 5 km theo kế hoạch đã lập, đảm bảo thời gian chạy giảm dần trong 3 buổi cuối cùng.
- **O1-KR1.t7**: Đo thời gian chạy 5 km sau khi hoàn thành kế hoạch, so sánh với thời gian ban đầu để xác định tiến trình.
- **O1-KR2.t1**: Xác định lịch tập, bài tập cụ thể, tần suất và thời gian cho mỗi buổi tập. Chọn bài tập phù hợp với mục tiêu tăng sức mạnh tim mạch.
- **O1-KR2.t2**: Lên thực đơn 4 tuần xoay vòng, đảm bảo đủ dinh dưỡng và phù hợp với mục tiêu tăng sức mạnh. Gửi thực đơn cho chuyên gia dinh dưỡng để góp ý.
- **O1-KR2.t3**: Thực hiện 2 buổi tập sức mạnh mỗi tuần vào buổi sáng, theo lịch đã lên. Đảm bảo mỗi buổi tập kéo dài 45-60 phút.
- **O1-KR2.t4**: Thực hiện 2 buổi tập sức mạnh mỗi tuần vào buổi sáng, theo lịch đã lên. Đảm bảo mỗi buổi tập kéo dài 45-60 phút.
- **O1-KR2.t5**: Ghi lại số buổi tập sức mạnh mỗi tuần và đánh giá tiến trình sau mỗi 4 tuần. Điều chỉnh kế hoạch nếu cần.
- **O1-KR2.t6**: Kiểm tra số buổi tập sức mạnh mỗi tuần sau 12 tuần để xác nhận đạt mục tiêu 2 buổi/tuần.
- **O2-KR1.t1**: Lập kế hoạch ăn uống cụ thể cho 4 tuần, bao gồm các bữa ăn, lượng calo, và loại thực phẩm phù hợp để giảm cân.
- **O2-KR1.t2**: Lên danh sách các bữa ăn cụ thể cho 4 tuần, bao gồm các món ăn, số lượng, và thời gian ăn.
- **O2-KR1.t3**: Áp dụng thực đơn đã được chuyên gia dinh dưỡng góp ý vào tuần 1, theo dõi và điều chỉnh nếu cần.
- **O2-KR1.t4**: Áp dụng thực đơn đã được chuyên gia dinh dưỡng góp ý vào tuần 2, theo dõi và điều chỉnh nếu cần.
- **O2-KR1.t5**: Áp dụng thực đơn đã được chuyên gia dinh dưỡng góp ý vào tuần 3, theo dõi và điều chỉnh nếu cần.
- **O2-KR1.t6**: Áp dụng thực đơn đã được chuyên gia dinh dưỡng góp ý vào tuần 4, theo dõi và điều chỉnh nếu cần.
- **O2-KR1.t7**: Theo dõi cân nặng mỗi tuần, so sánh với mục tiêu và điều chỉnh kế hoạch ăn uống nếu cần.
- **O2-KR1.t8**: Đo lường cân nặng cuối kỳ để xác định xem mục tiêu đã đạt được hay chưa.
- **O2-KR2.t1**: Xác định mục tiêu dinh dưỡng, phân bổ các bữa ăn, và lựa chọn các món ăn phù hợp với nhu cầu của người dùng.
- **O2-KR2.t2**: Thu thập thông tin về nhu cầu dinh dưỡng, sở thích ăn uống, và các hạn chế (nếu có) của người dùng.
- **O2-KR2.t3**: Gửi kế hoạch thực đơn đã lập cho chuyên gia dinh dưỡng để nhận góp ý.
- **O2-KR2.t4**: Sửa đổi thực đơn theo các góp ý nhận được từ chuyên gia dinh dưỡng.
- **O2-KR2.t5**: Đánh giá lại thực đơn để đảm bảo nó đáp ứng đủ nhu cầu dinh dưỡng và phù hợp với thói quen ăn uống của người dùng.
- **O2-KR2.t6**: Lưu trữ và công bố thực đơn 4 tuần xoay vòng đã được chỉnh sửa và kiểm tra.
