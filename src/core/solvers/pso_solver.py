"""
Thuật toán Particle Swarm Optimization (PSO) - Bầy đàn
Pure Python implementation với hỗ trợ Numpy.

Cách tiếp cận cho bài toán xếp lịch (Discrete Problem):
- Encoding: Biến đổi lịch thi thành Vector số thực (Continuous Position).
  Vector X = [t_1, r_1, t_2, r_2, ..., t_n, r_n]
  Trong đó:
    t_i: Giá trị float map sang index của (Ngày + Giờ)
    r_i: Giá trị float map sang index của Phòng
- Decoding: Làm tròn số thực -> Index nguyên -> Lấy giá trị thực tế.
"""

import numpy as np
import time
import random
from typing import List, Dict, Any, Tuple, Optional
import sys
from pathlib import Path

# Setup path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.solvers.base_solver import BaseSolver
from src.models.solution import Schedule
from src.models.course import Course
from src.models.room import Room
from src.core.constraints import ConstraintChecker
from src.core.optimization_fast import FastConstraintChecker

class Particle:
    """
    Đại diện cho một cá thể trong bầy đàn.
    """
    def __init__(self, dimension: int, bounds: Tuple[np.ndarray, np.ndarray]):
        # Vị trí hiện tại (Random trong bounds)
        self.position = np.random.uniform(bounds[0], bounds[1], dimension)
        
        # Vận tốc (Khởi tạo nhỏ)
        self.velocity = np.random.uniform(-1, 1, dimension)
        
        # PBest (Vị trí tốt nhất của cá nhân)
        self.pbest_position = self.position.copy()
        self.pbest_value = float('inf')
        
        # Cost hiện tại
        self.current_value = float('inf')

class PSOSolver(BaseSolver):
    """
    Particle Swarm Optimization Solver.
    
    Nguyên lý:
        - Mỗi hạt (particle) đại diện cho một solution
        - Hạt di chuyển trong không gian tìm kiếm dựa trên:
            + Vận tốc hiện tại (quán tính)
            + Vị trí tốt nhất của chính nó (PBest - cognitive)
            + Vị trí tốt nhất của cả bầy (GBest - social)
    
    Parameters (trong config):
        - swarm_size (int): Số lượng hạt trong bầy (mặc định: 50)
        - max_iterations (int): Số vòng lặp tối đa (mặc định: 1000)
        - w (float): Hệ số quán tính (inertia weight, mặc định: 0.7)
        - c1 (float): Hệ số nhận thức (cognitive coefficient, mặc định: 1.5)
        - c2 (float): Hệ số xã hội (social coefficient, mặc định: 1.5)
    """
    def __init__(self, 
                 courses: List[Course], 
                 rooms: List[Room],
                 config: Optional[Dict[str, Any]] = None,
                 proctors: Optional[List] = None,
                 parent=None):
        """
        Khởi tạo PSO Solver.
        
        ENHANCED: Tự động chia môn học có số lượng sinh viên lớn thành nhiều Course objects.
        
        Args:
            courses: Danh sách môn học cần xếp lịch.
            rooms: Danh sách phòng thi có sẵn.
            config: Dictionary chứa tham số PSO.
            proctors: Danh sách giám thị có sẵn (optional).
            parent: Parent QObject.
        """
        super().__init__(courses, rooms, config, proctors, parent)
        
        # --- PSO Parameters ---
        self.swarm_size = int(self.config.get('swarm_size', 50))
        self.max_iterations = int(self.config.get('max_iterations', 1000))
        
        # Hệ số quán tính (Inertia weight)
        self.w = float(self.config.get('w', 0.7)) 
        # Hệ số nhận thức (Cognitive - PBest)
        self.c1 = float(self.config.get('c1', 1.5))
        # Hệ số xã hội (Social - GBest)
        self.c2 = float(self.config.get('c2', 1.5))
        
        # Constraint Checker với proctor constraints
        schedule_config = self.config.get('schedule_config', {})
        max_exams_per_week = schedule_config.get('max_exams_per_week', 5)
        max_exams_per_day = schedule_config.get('max_exams_per_day', 3)
        self.constraint_checker = ConstraintChecker(
            rooms,
            max_exams_per_week=max_exams_per_week,
            max_exams_per_day=max_exams_per_day
        )
        
        # OPTIMIZATION: Use FastConstraintChecker for iterations
        self.fast_constraint_checker = FastConstraintChecker(rooms)
        
        # Performance optimization: max runtime in seconds (prevent hangs)
        self.max_runtime = float(self.config.get('max_runtime', 300.0))  # 5 minutes default
        
        # Statistics
        self.gbest_updates = 0
        self.pbest_updates = 0
        
        # --- ENHANCED: Chuẩn bị courses (chia thành nhiều Course objects nếu cần) ---
        self.processed_courses = self._prepare_courses_with_sessions(self.courses, auto_split=True)
        
        # Log thống kê
        original_count = len(self.courses)
        processed_count = len(self.processed_courses)
        if processed_count > original_count:
            self._log(f"📋 Đã chia {original_count} môn học thành {processed_count} ca thi riêng biệt")
        
        # --- Search Space Setup ---
        # Flatten Time Slots: Tạo danh sách tất cả các cặp (Ngày, Giờ) khả dụng
        # Ví dụ: 14 ngày * 4 ca = 56 slots thời gian
        self.time_slots_flat = []
        for d in self.available_dates:
            for t in self.available_times:
                self.time_slots_flat.append((d, t))
        
        self.num_time_slots = len(self.time_slots_flat)
        self.num_rooms = len(self.rooms)
        self.num_courses = len(self.processed_courses)
        
        # Dimension: Mỗi course cần 2 giá trị (TimeSlot_Index, Room_Index)
        self.dimension = self.num_courses * 2
        
        # Bounds (Giới hạn không gian tìm kiếm)
        # Lower bound: [0, 0, 0, 0...]
        self.lb = np.zeros(self.dimension)
        # Upper bound: [max_time, max_room, max_time, max_room...]
        self.ub = np.zeros(self.dimension)
        for i in range(self.num_courses):
            self.ub[2*i] = self.num_time_slots - 1e-6     # Time index
            self.ub[2*i+1] = self.num_rooms - 1e-6        # Room index
        
        # Log initialization
        self._log(f"🚀 PSO Solver initialized: swarm_size={self.swarm_size}, "
                  f"max_iter={self.max_iterations}, w={self.w}, c1={self.c1}, c2={self.c2}")
        self._log(f"📊 Courses: {self.num_courses}, Dimension: {self.dimension}")

    def _assign_proctors_to_schedule(self, schedule: Schedule) -> None:
        """
        Gán giám thị cho tất cả các môn thi chưa được gán.
        
        Sử dụng chiến lược phân công giám thị ngẫu nhiên để cân bằng tải.
        
        Args:
            schedule (Schedule): Schedule object cần gán giám thị
        """
        if not self.proctors or not schedule or not schedule.courses:
            return
        
        proctor_assignments = {}  # Map to track assignments per proctor
        
        for course in schedule.courses:
            # Nếu đã có giám thị, skip
            if course.assigned_proctor_id:
                continue
            
            # Tìm giám thị có ít công việc nhất (load balancing)
            min_assignments = float('inf')
            best_proctor = None
            
            for proctor in self.proctors:
                if proctor.proctor_id not in proctor_assignments:
                    proctor_assignments[proctor.proctor_id] = 0
                
                assignments_count = proctor_assignments[proctor.proctor_id]
                
                if assignments_count < min_assignments:
                    min_assignments = assignments_count
                    best_proctor = proctor
            
            # Gán giám thị tốt nhất (có ít công việc nhất)
            if best_proctor:
                course.assigned_proctor_id = best_proctor.proctor_id
                proctor_assignments[best_proctor.proctor_id] += 1

    def _decode_position_to_schedule(self, position: np.ndarray) -> Schedule:
        """
        Chuyển đổi Vector vị trí (Float) thành đối tượng Schedule (Discrete).
        
        ENHANCED: Hỗ trợ khóa cứng lịch thi (is_locked).
        Khi decode, nếu course gốc có is_locked=True, bỏ qua giá trị từ vector 
        và dùng giá trị cố định ban đầu của course đó.
        
        Position structure: [c1_time, c1_room, c2_time, c2_room, ...]
        Mỗi course đã được chia thành Course objects riêng biệt.
        """
        decoded_courses = []
        
        # Position là mảng [c1_time, c1_room, c2_time, c2_room, ...]
        for i in range(self.num_courses):
            course_template = self.processed_courses[i]
            
            # Tạo object Course mới đã được gán lịch
            new_course = Course(
                course_id=course_template.course_id,
                name=course_template.name,
                location=course_template.location,
                exam_format=course_template.exam_format,
                note=course_template.note,
                student_count=course_template.student_count,
                is_locked=course_template.is_locked,
                duration=course_template.duration
            )
            
            # ENHANCED: Kiểm tra is_locked
            # Nếu is_locked=True và đã có lịch: Sử dụng giá trị cố định cho ngày/giờ/phòng
            # Nhưng KHÔNG assign proctor từ template - proctor sẽ được tối ưu độc lập
            if course_template.is_locked and course_template.is_scheduled():
                new_course.assigned_date = course_template.assigned_date
                new_course.assigned_time = course_template.assigned_time
                new_course.assigned_room = course_template.assigned_room
                # Không assign proctor - để vector tối ưu
            else:
                # Lấy giá trị float từ vector và ép kiểu int để ra index
                time_idx = int(position[2*i])
                room_idx = int(position[2*i+1])
                
                # Clip index để tránh lỗi out of bound (phòng ngừa)
                time_idx = np.clip(time_idx, 0, self.num_time_slots - 1)
                room_idx = np.clip(room_idx, 0, self.num_rooms - 1)
                
                # Map ngược lại dữ liệu thực
                date_val, time_val = self.time_slots_flat[time_idx]
                room_val = self.rooms[room_idx].room_id
                
                new_course.assigned_date = date_val
                new_course.assigned_time = time_val
                new_course.assigned_room = room_val
            
            decoded_courses.append(new_course)
            
        schedule = Schedule(courses=decoded_courses)
        return schedule

    def run(self) -> None:
        """
        Chạy thuật toán Particle Swarm Optimization.
        
        Main Loop:
            1. Khởi tạo quần thể (swarm) với vị trí và vận tốc ngẫu nhiên
            2. Đánh giá ban đầu và tìm GBest
            3. While iteration < max_iterations:
                a. Cập nhật vận tốc cho mỗi hạt
                b. Cập nhật vị trí cho mỗi hạt
                c. Đánh giá và cập nhật PBest/GBest
                d. Emit signals để cập nhật GUI
            4. Kiểm tra feasibility và trả về kết quả
        """
        try:
            # Setup
            self.is_running = True
            self.should_stop = False
            self.start_time = time.time()
            self.convergence_history = []
            self.gbest_updates = 0
            self.pbest_updates = 0
            
            self._log("=" * 60)
            self._log("🚀 BẮT ĐẦU PARTICLE SWARM OPTIMIZATION")
            self._log("=" * 60)
            self._log(f"📊 Tham số: swarm_size={self.swarm_size}, max_iter={self.max_iterations}")
            self._log(f"⚙️ Hệ số: w={self.w}, c1={self.c1}, c2={self.c2}")
            self._log(f"🔍 Không gian tìm kiếm: {self.dimension} chiều")
            self._log(f"   - Số môn học/ca thi: {self.num_courses} (bao gồm courses đã chia)")
            self._log(f"   - Số time slots: {self.num_time_slots}")
            self._log(f"   - Số phòng thi: {self.num_rooms}")
            self._log("-" * 60)
            
            # 1. Khởi tạo quần thể (Swarm Initialization)
            self._log("📊 Đang khởi tạo quần thể...")
            swarm = [Particle(self.dimension, (self.lb, self.ub)) for _ in range(self.swarm_size)]
            
            gbest_position = np.zeros(self.dimension)
            gbest_value = float('inf')
            initial_gbest_value = None
            
            # Đánh giá ban đầu
            self._log("🔍 Đang đánh giá các hạt ban đầu...")
            for particle in swarm:
                sched = self._decode_position_to_schedule(particle.position)
                # Gán giám thị cho schedule này
                self._assign_proctors_to_schedule(sched)
                # Use fast checker for initial evaluation
                cost = self.fast_constraint_checker.calculate_fast(sched)
                
                particle.current_value = cost
                particle.pbest_value = cost
                particle.pbest_position = particle.position.copy()
                
                if cost < gbest_value:
                    gbest_value = cost
                    gbest_position = particle.position.copy()
                    self.best_solution = sched
                    self.best_solution.fitness_score = gbest_value
            
            initial_gbest_value = gbest_value
            self._log(f"✓ Đánh giá ban đầu hoàn tất: Initial Best Cost = {gbest_value:.2f}")
            self.convergence_history.append(gbest_value)
            
            # 2. Main Loop
            self._log("-" * 60)
            self._log("🔄 Bắt đầu vòng lặp chính...")
            iteration = 0
            
            while iteration < self.max_iterations and self.is_running:
                if self.should_stop:
                    self._log("⚠️ Thuật toán đã bị dừng bởi người dùng")
                    break
                
                # Check runtime limit
                elapsed_time = time.time() - self.start_time
                if elapsed_time > self.max_runtime:
                    self._log(f"⏱️ Đạt giới hạn thời gian ({self.max_runtime}s). Dừng.")
                    break
                
                iteration += 1
                self.total_iterations = iteration
                
                for particle in swarm:
                    # --- UPDATE VELOCITY ---
                    # v = w*v + c1*r1*(pbest - x) + c2*r2*(gbest - x)
                    r1 = np.random.rand(self.dimension)
                    r2 = np.random.rand(self.dimension)
                    
                    particle.velocity = (self.w * particle.velocity) + \
                                        (self.c1 * r1 * (particle.pbest_position - particle.position)) + \
                                        (self.c2 * r2 * (gbest_position - particle.position))
                    
                    # --- UPDATE POSITION ---
                    # x = x + v
                    particle.position = particle.position + particle.velocity
                    
                    # Clip position to bounds (giữ hạt trong không gian tìm kiếm)
                    particle.position = np.clip(particle.position, self.lb, self.ub)
                    
                    # --- EVALUATION (OPTIMIZED: Use fast checker) ---
                    current_sched = self._decode_position_to_schedule(particle.position)
                    # Gán giám thị cho schedule này
                    self._assign_proctors_to_schedule(current_sched)
                    
                    # Use fast constraint checker for iterations (hard constraints only)
                    current_cost = self.fast_constraint_checker.calculate_fast(current_sched)
                    particle.current_value = current_cost
                    
                    # Update PBest
                    if current_cost < particle.pbest_value:
                        particle.pbest_value = current_cost
                        particle.pbest_position = particle.position.copy()
                        self.pbest_updates += 1
                        
                        # Update GBest
                        if current_cost < gbest_value:
                            gbest_value = current_cost
                            gbest_position = particle.position.copy()
                            self.best_solution = current_sched
                            self.best_solution.fitness_score = gbest_value
                            self.gbest_updates += 1
                            
                            self._log(f"🌟 Iteration {iteration}: NEW GBEST FOUND! Cost = {gbest_value:.2f}")

                # Store history
                self.convergence_history.append(gbest_value)
                
                # Emit updates (mỗi 10 vòng để đỡ lag GUI)
                if iteration % 10 == 0:
                    # Phát tín hiệu với 6 tham số đầy đủ
                    # Định dạng: (iteration, cost, temperature, inertia, acceptance_rate, updates)
                    pbest_rate = (self.pbest_updates / (iteration * self.swarm_size) * 100) if iteration > 0 else 0
                    self.step_signal.emit(iteration, gbest_value, 0.0, self.w, pbest_rate, self.gbest_updates)
                    self._emit_progress(iteration, self.max_iterations)
                
                # Log định kỳ (mỗi 100 vòng)
                if iteration % 100 == 0:
                    pbest_rate = (self.pbest_updates / (iteration * self.swarm_size) * 100) if iteration > 0 else 0
                    self._log(
                        f"Iter {iteration}: Current Best = {gbest_value:.2f}, "
                        f"GBest Updates = {self.gbest_updates}, "
                        f"PBest Updates = {self.pbest_updates} ({pbest_rate:.1f}%)"
                    )
            
            # 3. Finish
            self.end_time = time.time()
            execution_time = self.get_execution_time()
            
            # Calculate statistics
            improvement = 0.0
            if initial_gbest_value is not None and initial_gbest_value > 0:
                improvement = ((initial_gbest_value - gbest_value) / initial_gbest_value * 100)
            
            # OPTIMIZATION: Final evaluation with full constraint checker for accurate score
            if self.best_solution:
                self._assign_proctors_to_schedule(self.best_solution)
                final_cost = self.constraint_checker.calculate_total_violation(self.best_solution)
                self.best_solution.fitness_score = final_cost
            else:
                final_cost = gbest_value
            
            # Final log
            self._log("=" * 60)
            self._log("✅ HOÀN THÀNH PARTICLE SWARM OPTIMIZATION (OPTIMIZED)")
            self._log("=" * 60)
            self._log(f"⏱️ Thời gian thực thi: {execution_time:.2f}s")
            self._log(f"🔁 Tổng số vòng lặp: {iteration}")
            self._log(f"📊 Cost ban đầu: {initial_gbest_value:.2f}")
            self._log(f"🎯 Cost tốt nhất (fast): {gbest_value:.2f}")
            self._log(f"🎯 Cost tốt nhất (chính xác): {final_cost:.2f}")
            self._log(f"📈 Cải thiện: {improvement:.2f}%")
            self._log(f"🌟 Số lần cập nhật GBest: {self.gbest_updates}")
            self._log(f"⭐ Tổng số lần cập nhật PBest: {self.pbest_updates}")
            if iteration > 0:
                pbest_rate = (self.pbest_updates / (iteration * self.swarm_size) * 100)
                self._log(f"📊 Tỷ lệ cập nhật PBest: {pbest_rate:.1f}%")
            
            # Check feasibility
            if self.best_solution:
                if self.constraint_checker.is_feasible(self.best_solution):
                    self._log("✅ Lịch thi KHẢ THI (không vi phạm hard constraints)")
                else:
                    self._log("⚠️ Lịch thi CÒN VI PHẠM một số ràng buộc cứng")
            
            # Emit điểm cuối cùng nếu chưa được emit (đảm bảo chart có dữ liệu đầy đủ)
            if iteration % 10 != 0:
                pbest_rate = (self.pbest_updates / (iteration * self.swarm_size) * 100) if iteration > 0 else 0
                self.step_signal.emit(iteration, final_cost, 0.0, self.w, pbest_rate, self.gbest_updates)
                self._emit_progress(100, 100)
            
            # Emit finished signal
            self.finished_signal.emit(self.best_solution)
            
        except Exception as e:
            self._log_error(f"Lỗi trong quá trình chạy PSO: {str(e)}")
            import traceback
            self._log_error(traceback.format_exc())
        
        finally:
            self.is_running = False
            self._emit_progress(100, 100)