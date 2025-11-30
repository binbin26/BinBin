"""
Test script để xác minh PSO Solver gán giám thị đúng.
"""

import sys
from pathlib import Path
import copy

# Setup paths
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from src.core.solvers.pso_solver import PSOSolver
from src.models.room import Room
from src.models.course import Course
from src.models.proctor import Proctor


def test_pso_proctor_assignment():
    """Test xem PSO Solver có gán giám thị đúng không."""
    print("=" * 80)
    print("TEST: PSO SOLVER - PROCTOR ASSIGNMENT")
    print("=" * 80)
    
    # ============================================================
    # 1. Tạo dữ liệu test
    # ============================================================
    print("\n[STEP 1] Tạo dữ liệu test")
    print("-" * 80)
    
    # Phòng thi
    rooms = [
        Room(room_id="P01", capacity=30, location="Tòa A"),
        Room(room_id="P02", capacity=25, location="Tòa A"),
    ]
    print(f"✓ Tạo {len(rooms)} phòng thi")
    
    # Môn học
    courses = [
        Course(course_id="MH001", name="Toán", student_count=25, 
               location="Tòa A", exam_format="Tự luận", duration=120),
        Course(course_id="MH002", name="Lập Trình", student_count=20,
               location="Tòa A", exam_format="Tự luận", duration=120),
        Course(course_id="MH003", name="CSDL", student_count=28,
               location="Tòa A", exam_format="Tự luận", duration=120),
    ]
    print(f"✓ Tạo {len(courses)} môn học")
    
    # Giám thị
    proctors = [
        Proctor(proctor_id="GT001", name="Thầy A", location="Tòa A"),
        Proctor(proctor_id="GT002", name="Thầy B", location="Tòa A"),
        Proctor(proctor_id="GT003", name="Thầy C", location="Tòa A"),
    ]
    print(f"✓ Tạo {len(proctors)} giám thị")
    
    # ============================================================
    # 2. Tạo config cho PSO
    # ============================================================
    print("\n[STEP 2] Cấu hình PSO Solver")
    print("-" * 80)
    
    config = {
        'algorithm': 'pso',
        'swarm_size': 10,
        'max_iterations': 50,
        'w': 0.7,
        'c1': 1.5,
        'c2': 1.5,
        'schedule_config': {
            'start_date': '2025-12-01',
            'end_date': '2025-12-10',
            'max_exams_per_week': 5,
            'max_exams_per_day': 3,
        }
    }
    print(f"✓ Config: swarm_size={config['swarm_size']}, max_iter={config['max_iterations']}")
    
    # ============================================================
    # 3. Tạo PSO Solver
    # ============================================================
    print("\n[STEP 3] Khởi tạo PSO Solver")
    print("-" * 80)
    
    pso_solver = PSOSolver(
        copy.deepcopy(courses), 
        rooms, 
        config, 
        proctors
    )
    
    print(f"✓ PSO Solver khởi tạo thành công")
    print(f"  - Available dates: {len(pso_solver.available_dates)} ngày")
    print(f"  - Available times: {len(pso_solver.available_times)} ca")
    print(f"  - Proctors: {len(pso_solver.proctors)} giám thị")
    
    # ============================================================
    # 4. Tạo giải pháp ban đầu
    # ============================================================
    print("\n[STEP 4] Tạo giải pháp từ random PSO position")
    print("-" * 80)
    
    import numpy as np
    random_position = np.random.uniform(pso_solver.lb, pso_solver.ub, pso_solver.dimension)
    initial_solution = pso_solver._decode_position_to_schedule(random_position)
    
    print(f"✓ Initial solution tạo được: {len(initial_solution.courses)} ca thi")
    
    # ============================================================
    # 5. Kiểm tra giám thị trong initial solution
    # ============================================================
    print("\n[STEP 5] Kiểm tra giám thị trong initial solution")
    print("-" * 80)
    
    assigned_proctors = 0
    unassigned_proctors = 0
    
    for i, course in enumerate(initial_solution.courses):
        proctor_status = f"✓ {course.assigned_proctor_id}" if course.assigned_proctor_id else "❌ NOT ASSIGNED"
        print(f"  [{i+1}] {course.course_id}: {proctor_status}")
        
        if course.assigned_proctor_id:
            assigned_proctors += 1
        else:
            unassigned_proctors += 1
    
    print(f"\n📊 Kết quả:")
    print(f"  - Đã gán giám thị: {assigned_proctors}/{len(initial_solution.courses)}")
    print(f"  - Chưa gán giám thị: {unassigned_proctors}/{len(initial_solution.courses)}")
    
    if assigned_proctors == len(initial_solution.courses):
        print(f"✅ TẤT CẢ các môn thi đều CÓ giám thị từ decode!")
    else:
        print(f"⚠️ Sau decode, chưa có giám thị. Bây giờ gán...")
        pso_solver._assign_proctors_to_schedule(initial_solution)
        
        assigned_proctors_after = sum(1 for c in initial_solution.courses if c.assigned_proctor_id)
        print(f"   - Sau gán: {assigned_proctors_after}/{len(initial_solution.courses)} có giám thị")
        
        if assigned_proctors_after == len(initial_solution.courses):
            print(f"✅ Sau gán, TẤT CẢ các môn thi đều CÓ giám thị!")
        else:
            print(f"❌ Vẫn CÒN các môn thi KHÔNG CÓ giám thị!")
    
    # ============================================================
    # 6. Tạo một schedule random từ PSO position
    # ============================================================
    print("\n[STEP 6] Kiểm tra load balancing giám thị")
    print("-" * 80)
    
    # Đếm số lần mỗi giám thị được gán
    proctor_count = {}
    for course in initial_solution.courses:
        if course.assigned_proctor_id:
            proctor_count[course.assigned_proctor_id] = proctor_count.get(course.assigned_proctor_id, 0) + 1
    
    print(f"✓ Phân phối giám thị (load balancing):")
    for proctor_id, count in sorted(proctor_count.items()):
        print(f"    - {proctor_id}: {count} môn")
    
    # ============================================================
    # TỔNG KẾT
    # ============================================================
    print("\n" + "=" * 80)
    print("✅ TEST HOÀN THÀNH")
    print("=" * 80)
    
    # Final check
    all_assigned = all(c.assigned_proctor_id for c in initial_solution.courses)
    if all_assigned:
        print("\n✅ KẾT LUẬN: PSO Solver gán giám thị ĐÚNG!")
        print("   - Initial solution có tất cả giám thị")
        print("   - Phương thức _assign_proctors_to_schedule() hoạt động tốt")
    else:
        print("\n❌ KẾT LUẬN: PSO Solver CÒN VẤN ĐỀ với gán giám thị!")


if __name__ == "__main__":
    test_pso_proctor_assignment()
