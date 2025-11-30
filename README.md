# Đồ Án Xếp Lịch Thi Học Kỳ

## Mô tả
Ứng dụng tối ưu hóa lịch thi học kỳ sử dụng thuật toán **Simulated Annealing (SA)** và **Particle Swarm Optimization (PSO)**.

## Tính năng
- ✅ Tự động xếp lịch thi tối ưu
- ✅ Tránh xung đột giờ thi và phòng thi
- ✅ So sánh hiệu năng 2 thuật toán SA vs PSO
- ✅ Giao diện đồ họa hiện đại (PyQt5)
- ✅ Xuất kết quả ra Excel

## Cấu trúc dự án
```
root/
├── data/              # Dữ liệu input/output
├── src/
│   ├── models/        # Data classes
│   ├── core/          # Logic thuật toán (SA, PSO)
│   ├── ui/            # Giao diện PyQt5
│   └── utils/         # Tiện ích
└── main.py            # Entry point
```

## Cài đặt
```bash
pip install -r requirements.txt
```

## Chạy ứng dụng
```bash
python main.py
```

## Tác giả
- Sinh viên: [Tên của bạn]
- Môn học: Trí tuệ nhân tạo
- Năm học: 2024-2025
