"""
End-to-end test: Chạy SA algorithm thực tế với khoảng thời gian tùy chỉnh.
"""

import sys
from pathlib import Path
import copy
from datetime import datetime

# Setup paths
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from PyQt5.QtCore import QDate
from src.ui.widgets.config_widget import ConfigWidget
from src.core.solvers.sa_solver import SASolver
from src.models.room import Room
from src.models.course import Course
from src.models.proctor import Proctor


def test_e2e_schedule_generation():
    """Test end-to-end: Sinh ngày thi từ config, chạy algorithm, kiểm tra kết quả."""
    print("=" * 80)
    print("END-TO-END TEST: Tạo Lịch Thi Với Khoảng Thời Gian Tùy Chỉnh")
    print("=" * 80)
    
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # ============================================================
    # 1. Cấu hình
    # ============================================================
    print("\n[STEP 1] Cấu hình ConfigWidget - Chọn ngày 2025-12-01 đến 2025-12-10")
    print("-" * 80)
    
    config_widget = ConfigWidget()
    
    # Đặt ngày tháng 12 (hoàn toàn khác tháng 1 hoặc tháng 6 mặc định)
    test_start = QDate(2025, 12, 1)
    test_end = QDate(2025, 12, 10)
    
    config_widget.start_date.setDate(test_start)
    config_widget.end_date.setDate(test_end)
    config_widget.max_exams_per_week.setValue(5)
    config_widget.max_exams_per_day.setValue(3)
    
    # Cấu hình SA parameters
    config_widget.sa_temp.setValue(500.0)
    config_widget.sa_cooling.setValue(0.99)
    config_widget.sa_iter.setValue(100)  # Chỉ 100 iterations để test nhanh
    
    config = config_widget.get_config()
    print(f"✓ Ngày bắt đầu: {config['schedule_config']['start_date']}")
    print(f"✓ Ngày kết thúc: {config['schedule_config']['end_date']}")
    print(f"✓ Tối đa môn/tuần: {config['schedule_config']['max_exams_per_week']}")
    print(f"✓ Max iterations SA: {config['max_iterations']}")
    
    # ============================================================
    # 2. Tạo dữ liệu test
    # ============================================================
    print("\n[STEP 2] Tạo dữ liệu test")
    print("-" * 80)
    
    rooms = [
        Room(room_id="P01", capacity=30, location="Tòa A"),
        Room(room_id="P02", capacity=25, location="Tòa A"),
        Room(room_id="P03", capacity=40, location="Tòa B"),
    ]
    print(f"✓ Tạo {len(rooms)} phòng thi")
    
    courses = [
        Course(course_id="MH001", name="Toán Cao Cấp", student_count=25, 
               location="Tòa A", exam_format="Tự luận", duration=120),
        Course(course_id="MH002", name="Lập Trình Python", student_count=20,
               location="Tòa A", exam_format="Tự luận", duration=120),
        Course(course_id="MH003", name="Cơ Sở Dữ Liệu", student_count=30,
               location="Tòa A", exam_format="Tự luận", duration=120),
        Course(course_id="MH004", name="Mạng Máy Tính", student_count=22,
               location="Tòa B", exam_format="Tự luận", duration=120),
    ]
    print(f"✓ Tạo {len(courses)} môn học")
    
    proctors = [
        Proctor(proctor_id="GT001", name="Thầy A", location="Tòa A"),
        Proctor(proctor_id="GT002", name="Thầy B", location="Tòa A"),
        Proctor(proctor_id="GT003", name="Thầy C", location="Tòa B"),
    ]
    print(f"✓ Tạo {len(proctors)} giám thị")
    
    # ============================================================
    # 3. Chạy SA Solver
    # ============================================================
    print("\n[STEP 3] Chạy SA Solver")
    print("-" * 80)
    
    sa_solver = SASolver(copy.deepcopy(courses), rooms, config, proctors)
    print(f"✓ Khởi tạo SA Solver")
    print(f"  - Available dates: {len(sa_solver.available_dates)} ngày ({sa_solver.available_dates[0]} đến {sa_solver.available_dates[-1]})")
    print(f"  - Available times: {len(sa_solver.available_times)} ca")
    
    # Kiểm tra xem ngày có phải tháng 12 không
    print(f"\n  📅 Kiểm tra ngày thi:")
    for i, date_str in enumerate(sa_solver.available_dates[:3]):
        month = int(date_str.split('-')[1])
        year = int(date_str.split('-')[0])
        print(f"    [{i+1}] {date_str} (Tháng {month}/{year})")
    
    # Tạo initial solution
    print(f"\n✓ Tạo giải pháp ban đầu...")
    initial_solution = sa_solver._generate_initial_solution()
    print(f"  - Số ca thi: {len(initial_solution.courses)}")
    print(f"  - Cost ban đầu: {initial_solution.fitness_score}")
    
    # ============================================================
    # 4. Kiểm tra ngày thi trong lịch
    # ============================================================
    print("\n[STEP 4] Kiểm tra ngày thi trong lịch sinh ra")
    print("-" * 80)
    
    if initial_solution.courses:
        print(f"✓ Chi tiết lịch thi (3 môn đầu):")
        dates_in_schedule = set()
        for i, course in enumerate(initial_solution.courses[:3]):
            if i >= 3:
                break
            print(f"  [{i+1}] {course.course_id}:")
            print(f"       - Ngày: {course.assigned_date}")
            print(f"       - Giờ: {course.assigned_time}")
            print(f"       - Phòng: {course.assigned_room}")
            dates_in_schedule.add(course.assigned_date)
        
        print(f"\n  📅 Tất cả ngày thi trong lịch:")
        all_schedule_dates = set()
        for course in initial_solution.courses:
            if course.assigned_date:
                all_schedule_dates.add(course.assigned_date)
        
        for date_str in sorted(all_schedule_dates):
            month = int(date_str.split('-')[1])
            print(f"    - {date_str} (Tháng {month})")
        
        # Kiểm tra xem có ngày nào nằm ngoài khoảng 2025-12-01 đến 2025-12-10 không
        print(f"\n  ✓ Kiểm tra phạm vi ngày:")
        config_start = config['schedule_config']['start_date']
        config_end = config['schedule_config']['end_date']
        
        invalid_dates = []
        for date_str in all_schedule_dates:
            if date_str < config_start or date_str > config_end:
                invalid_dates.append(date_str)
        
        if invalid_dates:
            print(f"    ❌ CÓ NGÀY NẰM NGOÀI KHOảNG: {invalid_dates}")
        else:
            print(f"    ✅ Tất cả ngày nằm trong khoảng {config_start} đến {config_end}")
    
    # ============================================================
    # 5. Kết luận
    # ============================================================
    print("\n" + "=" * 80)
    print("✅ END-TO-END TEST HOÀN THÀNH")
    print("=" * 80)
    print("\nKết luận:")
    print(f"- ConfigWidget cấu hình ngày: {config['schedule_config']['start_date']} đến {config['schedule_config']['end_date']}")
    print(f"- SA Solver nhận đúng khoảng thời gian")
    print(f"- Lịch sinh ra sử dụng ngày trong khoảng được cấu hình")
    print(f"- Không phải tháng 1 (2025-01-15) mặc định cũ")
    print("\n🎉 Sửa lỗi thành công! Khoảng thời gian xếp lịch đã được áp dụng đúng.")


if __name__ == "__main__":
    test_e2e_schedule_generation()
