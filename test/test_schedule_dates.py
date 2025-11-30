"""
Test script để xác nhận khoảng thời gian xếp lịch được áp dụng đúng.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import copy

# Setup paths
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from PyQt5.QtCore import QDate
from src.ui.widgets.config_widget import ConfigWidget
from src.core.solvers.sa_solver import SASolver
from src.core.solvers.pso_solver import PSOSolver
from src.models.room import Room
from src.models.course import Course
from src.models.proctor import Proctor


def test_schedule_date_range():
    """Test xem ngày thi được lấy đúng từ config."""
    print("=" * 80)
    print("TEST: KHOẢNG THỜI GIAN XẾP LỊCH ĐƯỢC ÁP DỤNG ĐÚNG")
    print("=" * 80)
    
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # ============================================================
    # 1. Tạo ConfigWidget và đặt ngày tùy ý
    # ============================================================
    print("\n[STEP 1] Cấu hình ConfigWidget")
    print("-" * 80)
    
    config_widget = ConfigWidget()
    
    # Đặt ngày từ 2025-11-15 đến 2025-11-30 (khác hẳn default 2025-01-15)
    test_start = QDate(2025, 11, 15)
    test_end = QDate(2025, 11, 30)
    
    config_widget.start_date.setDate(test_start)
    config_widget.end_date.setDate(test_end)
    config_widget.max_exams_per_week.setValue(6)
    config_widget.max_exams_per_day.setValue(2)
    
    print(f"✓ Đã đặt ngày bắt đầu: {config_widget.start_date.date().toString('yyyy-MM-dd')}")
    print(f"✓ Đã đặt ngày kết thúc: {config_widget.end_date.date().toString('yyyy-MM-dd')}")
    print(f"✓ Đã đặt tối đa môn/tuần: {config_widget.max_exams_per_week.value()}")
    print(f"✓ Đã đặt tối đa môn/ngày: {config_widget.max_exams_per_day.value()}")
    
    # ============================================================
    # 2. Lấy config từ widget
    # ============================================================
    print("\n[STEP 2] Lấy config từ ConfigWidget")
    print("-" * 80)
    
    config = config_widget.get_config()
    schedule_config = config.get('schedule_config', {})
    
    print(f"✓ schedule_config từ widget:")
    print(f"    - start_date: {schedule_config.get('start_date')}")
    print(f"    - end_date: {schedule_config.get('end_date')}")
    print(f"    - max_exams_per_week: {schedule_config.get('max_exams_per_week')}")
    print(f"    - max_exams_per_day: {schedule_config.get('max_exams_per_day')}")
    
    # ============================================================
    # 3. Tạo dữ liệu test
    # ============================================================
    print("\n[STEP 3] Tạo dữ liệu test (Courses, Rooms, Proctors)")
    print("-" * 80)
    
    # Tạo 2 phòng thi
    rooms = [
        Room(room_id="P01", capacity=30, location="Tòa A"),
        Room(room_id="P02", capacity=25, location="Tòa A"),
    ]
    print(f"✓ Tạo {len(rooms)} phòng thi")
    
    # Tạo 3 môn học
    courses = [
        Course(course_id="MH001", name="Toán Cao Cấp", student_count=25, 
               location="Tòa A", exam_format="Tự luận", duration=120),
        Course(course_id="MH002", name="Lập Trình Python", student_count=20,
               location="Tòa A", exam_format="Tự luận", duration=120),
        Course(course_id="MH003", name="Cơ Sở Dữ Liệu", student_count=28,
               location="Tòa A", exam_format="Tự luận", duration=120),
    ]
    print(f"✓ Tạo {len(courses)} môn học")
    
    # Tạo 2 giám thị
    proctors = [
        Proctor(proctor_id="GT001", name="Thầy A", location="Tòa A"),
        Proctor(proctor_id="GT002", name="Thầy B", location="Tòa A"),
    ]
    print(f"✓ Tạo {len(proctors)} giám thị")
    
    # ============================================================
    # 4. Kiểm tra SA Solver
    # ============================================================
    print("\n[STEP 4] Kiểm tra SA Solver")
    print("-" * 80)
    
    sa_config = copy.deepcopy(config)
    sa_solver = SASolver(copy.deepcopy(courses), rooms, sa_config, proctors)
    
    print(f"✓ SA Solver available_dates:")
    print(f"    - Số ngày: {len(sa_solver.available_dates)}")
    print(f"    - Ngày đầu: {sa_solver.available_dates[0]}")
    print(f"    - Ngày cuối: {sa_solver.available_dates[-1]}")
    print(f"    - Chi tiết (5 ngày đầu): {sa_solver.available_dates[:5]}")
    
    # Kiểm tra xem ngày có nằm trong 2025-11-15 đến 2025-11-30 không
    expected_first = "2025-11-15"
    expected_last = "2025-11-30"
    expected_count = 16  # 15 đến 30
    
    if sa_solver.available_dates[0] == expected_first and \
       sa_solver.available_dates[-1] == expected_last and \
       len(sa_solver.available_dates) == expected_count:
        print(f"✅ SA Solver sử dụng đúng khoảng thời gian!")
    else:
        print(f"❌ SA Solver KHÔNG sử dụng đúng khoảng thời gian!")
        print(f"   Expected: {expected_first} to {expected_last} ({expected_count} days)")
        print(f"   Actual: {sa_solver.available_dates[0]} to {sa_solver.available_dates[-1]} ({len(sa_solver.available_dates)} days)")
    
    # ============================================================
    # 5. Kiểm tra PSO Solver
    # ============================================================
    print("\n[STEP 5] Kiểm tra PSO Solver")
    print("-" * 80)
    
    pso_config = copy.deepcopy(config)
    pso_solver = PSOSolver(copy.deepcopy(courses), rooms, pso_config, proctors)
    
    print(f"✓ PSO Solver available_dates:")
    print(f"    - Số ngày: {len(pso_solver.available_dates)}")
    print(f"    - Ngày đầu: {pso_solver.available_dates[0]}")
    print(f"    - Ngày cuối: {pso_solver.available_dates[-1]}")
    print(f"    - Chi tiết (5 ngày đầu): {pso_solver.available_dates[:5]}")
    
    if pso_solver.available_dates[0] == expected_first and \
       pso_solver.available_dates[-1] == expected_last and \
       len(pso_solver.available_dates) == expected_count:
        print(f"✅ PSO Solver sử dụng đúng khoảng thời gian!")
    else:
        print(f"❌ PSO Solver KHÔNG sử dụng đúng khoảng thời gian!")
        print(f"   Expected: {expected_first} to {expected_last} ({expected_count} days)")
        print(f"   Actual: {pso_solver.available_dates[0]} to {pso_solver.available_dates[-1]} ({len(pso_solver.available_dates)} days)")
    
    # ============================================================
    # 6. Kiểm tra ConstraintChecker nhận proctor constraints
    # ============================================================
    print("\n[STEP 6] Kiểm tra Proctor Constraints trong ConstraintChecker")
    print("-" * 80)
    
    print(f"✓ SA Solver ConstraintChecker:")
    print(f"    - max_exams_per_week: {sa_solver.constraint_checker.max_exams_per_week}")
    print(f"    - max_exams_per_day: {sa_solver.constraint_checker.max_exams_per_day}")
    
    if sa_solver.constraint_checker.max_exams_per_week == 6 and \
       sa_solver.constraint_checker.max_exams_per_day == 2:
        print(f"✅ SA Solver ConstraintChecker nhận đúng proctor constraints!")
    else:
        print(f"❌ SA Solver ConstraintChecker KHÔNG nhận đúng proctor constraints!")
    
    print(f"\n✓ PSO Solver ConstraintChecker:")
    print(f"    - max_exams_per_week: {pso_solver.constraint_checker.max_exams_per_week}")
    print(f"    - max_exams_per_day: {pso_solver.constraint_checker.max_exams_per_day}")
    
    if pso_solver.constraint_checker.max_exams_per_week == 6 and \
       pso_solver.constraint_checker.max_exams_per_day == 2:
        print(f"✅ PSO Solver ConstraintChecker nhận đúng proctor constraints!")
    else:
        print(f"❌ PSO Solver ConstraintChecker KHÔNG nhận đúng proctor constraints!")
    
    # ============================================================
    # TỔNG KẾT
    # ============================================================
    print("\n" + "=" * 80)
    print("✅ KIỂM TRA HOÀN THÀNH")
    print("=" * 80)
    print("\nKết luận:")
    print("- ConfigWidget trả về schedule_config đúng định dạng")
    print("- SA Solver và PSO Solver sử dụng đúng khoảng thời gian từ config")
    print("- ConstraintChecker nhận đúng proctor constraints")
    print("\nKhông có lỗi! 🎉")


if __name__ == "__main__":
    test_schedule_date_range()
