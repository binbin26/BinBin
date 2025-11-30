"""
Simulated Annealing Solver cho bài toán xếp lịch thi.
Thuật toán luyện kim mô phỏng - Pure Python implementation from scratch.

OPTIMIZED VERSION: Loại bỏ deepcopy trong vòng lặp, sử dụng in-place modification với backup/rollback.
"""

import random
import math
import time
from typing import List, Dict, Any, Optional, Tuple
import sys
from pathlib import Path
import copy

# Fix import paths
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import với đường dẫn tương đối đúng
from src.core.solvers.base_solver import BaseSolver, SolverConfig
from src.models.solution import Schedule
from src.models.course import Course
from src.models.room import Room
from src.core.constraints import ConstraintChecker


class SASolver(BaseSolver):
    """
    Simulated Annealing Solver - Thuật toán Luyện Kim (OPTIMIZED).
    
    Performance Optimization:
        - Loại bỏ deepcopy trong vòng lặp chính
        - Sử dụng in-place modification với backup/rollback mechanism
        - Độ phức tạp mỗi bước: O(1) hoặc O(k) nhỏ thay vì O(N)
    
    Nguyên lý:
        - Bắt đầu với nhiệt độ cao → chấp nhận cả bad moves (thoát local optima)
        - Giảm dần nhiệt độ → chỉ chấp nhận good moves (hội tụ về global optima)
    
    Parameters (trong config):
        - initial_temperature (float): Nhiệt độ ban đầu (mặc định: 1000.0)
        - min_temperature (float): Nhiệt độ tối thiểu để dừng (mặc định: 0.1)
        - cooling_rate (float): Tốc độ làm lạnh (0.9 - 0.999, mặc định: 0.995)
        - max_iterations (int): Số vòng lặp tối đa (mặc định: 10000)
        - neighbor_type (str): Loại neighbor generation ('swap', 'random', 'smart')
    
    Acceptance Criterion:
        - ΔE = new_cost - current_cost
        - If ΔE < 0: Accept (better solution)
        - If ΔE > 0: Accept with probability P = exp(-ΔE/T)
    """
    
    def __init__(self, 
                 courses: List[Course], 
                 rooms: List[Room],
                 config: Optional[Dict[str, Any]] = None,
                 proctors: Optional[List] = None,
                 parent=None):
        """
        Khởi tạo SA Solver.
        
        Args:
            courses: Danh sách môn học cần xếp lịch.
            rooms: Danh sách phòng thi có sẵn.
            config: Dictionary chứa tham số SA.
            proctors: Danh sách giám thị có sẵn (optional).
            parent: Parent QObject.
        """
        super().__init__(courses, rooms, config, proctors, parent)
        
        # SA-specific parameters
        self.initial_temperature = self.config.get('initial_temperature', 1000.0)
        self.min_temperature = self.config.get('min_temperature', 0.1)
        self.cooling_rate = self.config.get('cooling_rate', 0.995)
        self.max_iterations = self.config.get('max_iterations', 10000)
        self.neighbor_type = self.config.get('neighbor_type', 'random')
        
        # Constraint checker với proctor constraints
        schedule_config = self.config.get('schedule_config', {})
        max_exams_per_week = schedule_config.get('max_exams_per_week', 5)
        max_exams_per_day = schedule_config.get('max_exams_per_day', 3)
        self.constraint_checker = ConstraintChecker(
            rooms, 
            max_exams_per_week=max_exams_per_week,
            max_exams_per_day=max_exams_per_day
        )
        
        # Time slots và schedule parameters
        self.available_dates = self._generate_exam_dates()
        self.available_times = self._generate_time_slots()
        
        # Statistics
        self.accepted_moves = 0
        self.rejected_moves = 0
        self.total_neighbors = 0
        
        self._log(f"🔥 SA Solver initialized (OPTIMIZED): T0={self.initial_temperature}, "
                  f"cooling={self.cooling_rate}, max_iter={self.max_iterations}")
    
    def _generate_initial_solution(self) -> Schedule:
        """
        Tạo lịch thi ngẫu nhiên ban đầu.
        
        ENHANCED: Hỗ trợ chia môn học thành nhiều ca và tối ưu lựa chọn phòng.
        ENHANCED: Hỗ trợ khóa cứng lịch thi (is_locked) - giữ nguyên nếu đã được xếp.
        
        Strategy:
            - Tự động chia môn học thành nhiều ca nếu số lượng sinh viên quá lớn
            - Với mỗi môn học/ca, nếu is_locked=True và đã có lịch: Giữ nguyên
            - Nếu is_locked=False hoặc chưa có lịch: Random ngày/giờ/phòng
            - Ưu tiên phòng cùng địa điểm và có utilization tốt
            - Đảm bảo phòng đủ sức chứa
        
        Returns:
            Schedule: Lịch thi ngẫu nhiên.
        """
        # Chuẩn bị courses (tự động chia thành nhiều Course objects nếu cần)
        processed_courses = self._prepare_courses_with_sessions(self.courses, auto_split=True)
        
        # Log thống kê
        original_count = len(self.courses)
        processed_count = len(processed_courses)
        if processed_count > original_count:
            self._log(f"📋 Đã chia {original_count} môn học thành {processed_count} ca thi riêng biệt")
        
        initial_courses = []
        
        for course in processed_courses:
            # Copy course để không ảnh hưởng dữ liệu gốc
            new_course = Course(
                course_id=course.course_id,
                name=course.name,
                location=course.location,
                exam_format=course.exam_format,
                note=course.note,
                student_count=course.student_count,
                is_locked=course.is_locked,
                duration=course.duration
            )
            
            # ENHANCED: Kiểm tra is_locked
            # Nếu is_locked=True và đã có lịch: Giữ nguyên ngày/giờ/phòng, nhưng vẫn phân công giám thị
            if course.is_locked and course.is_scheduled():
                new_course.assigned_date = course.assigned_date
                new_course.assigned_time = course.assigned_time
                new_course.assigned_room = course.assigned_room
                self._log(f"🔒 Giữ nguyên lịch của môn {course.course_id} (locked)")
            else:
                # Random assign schedule
                new_course.assigned_date = random.choice(self.available_dates)
                new_course.assigned_time = random.choice(self.available_times)
                
                # Tìm phòng tối ưu
                optimal_room = self._find_optimal_room(
                    new_course.student_count,
                    new_course.location,
                    prefer_smaller=False
                )
                
                if optimal_room:
                    new_course.assigned_room = optimal_room.room_id
                else:
                    # Fallback: Chọn random phòng cùng địa điểm
                    suitable_rooms = [
                        room for room in self.rooms
                        if room.location == course.location and 
                           room.capacity >= course.student_count
                    ]
                    if suitable_rooms:
                        new_course.assigned_room = random.choice(suitable_rooms).room_id
                    else:
                        new_course.assigned_room = random.choice(self.rooms).room_id
            
            # Phân công giám thị ngẫu nhiên cho TẤT CẢ MÔN (kể cả môn bị khóa)
            # vì giám thị cần được tối ưu độc lập
            if self.proctors:
                random_proctor = random.choice(self.proctors)
                new_course.assigned_proctor_id = random_proctor.proctor_id
            
            initial_courses.append(new_course)
        
        schedule = Schedule(courses=initial_courses)
        schedule.fitness_score = self.constraint_checker.calculate_total_violation(schedule)
        
        return schedule
    
    def _perturb_move(self, schedule: Schedule) -> Dict[str, Any]:
        """
        Thực hiện thay đổi nhỏ (Move) trên schedule hiện tại (in-place).
        Trả về backup data để có thể rollback nếu cần.
        
        Performance: O(1) hoặc O(k) nhỏ - chỉ thay đổi 1-2 courses.
        
        Args:
            schedule: Lịch thi cần thay đổi (sẽ bị modify trực tiếp).
        
        Returns:
            Dict chứa backup data: {
                'course_indices': List[int],
                'old_values': List[Dict]  # [{date, time, room}, ...]
            }
        """
        if not schedule.courses:
            return {'course_indices': [], 'old_values': []}
        
        backup_data = {
            'course_indices': [],
            'old_values': []
        }
        
        if self.neighbor_type == 'swap':
            # Swap 2 courses
            if len(schedule.courses) < 2:
                return self._perturb_move_random(schedule, backup_data)
            
            # Chọn 2 môn ngẫu nhiên
            idx1, idx2 = random.sample(range(len(schedule.courses)), 2)
            course1 = schedule.courses[idx1]
            course2 = schedule.courses[idx2]
            
            # Backup
            backup_data['course_indices'] = [idx1, idx2]
            backup_data['old_values'] = [
                {
                    'date': course1.assigned_date,
                    'time': course1.assigned_time,
                    'room': course1.assigned_room,
                    'proctor': course1.assigned_proctor_id
                },
                {
                    'date': course2.assigned_date,
                    'time': course2.assigned_time,
                    'room': course2.assigned_room,
                    'proctor': course2.assigned_proctor_id
                }
            ]
            
            # Swap (in-place)
            course1.assigned_date, course2.assigned_date = course2.assigned_date, course1.assigned_date
            course1.assigned_time, course2.assigned_time = course2.assigned_time, course1.assigned_time
            course1.assigned_room, course2.assigned_room = course2.assigned_room, course1.assigned_room
            course1.assigned_proctor_id, course2.assigned_proctor_id = course2.assigned_proctor_id, course1.assigned_proctor_id
            
        elif self.neighbor_type == 'smart':
            # Smart move: Tìm môn có vi phạm và sửa
            violations = self.constraint_checker.get_violation_details(schedule)
            
            if violations.get('location_mismatches', 0) > 0:
                # Tìm môn có location mismatch
                for idx, course in enumerate(schedule.courses):
                    if not course.is_scheduled():
                        continue
                    
                    room = self.rooms_dict.get(course.assigned_room)
                    if room and room.location != course.location:
                        # Fix bằng cách đổi phòng
                        suitable_rooms = [
                            r for r in self.rooms
                            if r.location == course.location and 
                               r.capacity >= course.student_count
                        ]
                        
                        if suitable_rooms:
                            # Backup
                            backup_data['course_indices'] = [idx]
                            backup_data['old_values'] = [{
                                'date': course.assigned_date,
                                'time': course.assigned_time,
                                'room': course.assigned_room,
                                'proctor': course.assigned_proctor_id
                            }]
                            
                            # Modify (in-place)
                            course.assigned_room = random.choice(suitable_rooms).room_id
                            return backup_data
            
            # Fallback: random move
            return self._perturb_move_random(schedule, backup_data)
        
        else:  # 'random'
            return self._perturb_move_random(schedule, backup_data)
        
        return backup_data
    
    def _perturb_move_random(self, schedule: Schedule, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực hiện random move trên 1 course hoặc 1 session.
        
        ENHANCED: Hỗ trợ xử lý sessions.
        ENHANCED: KHÔNG thay đổi môn học có is_locked=True (Pinning).
        
        Args:
            schedule: Lịch thi cần thay đổi.
            backup_data: Dict để lưu backup (sẽ được modify).
        
        Returns:
            backup_data đã được cập nhật.
        """
        # ENHANCED: Lọc ra các môn có is_locked=False
        # Chỉ được thay đổi ngày/giờ/phòng của các môn mà không bị khóa
        modifiable_courses = [
            (idx, course) for idx, course in enumerate(schedule.courses)
            if not course.is_locked
        ]
        
        # Nếu tất cả môn đều bị khóa, chỉ có thể thay đổi giám thị
        if not modifiable_courses:
            # Thay đổi giám thị cho 1 môn ngẫu nhiên (kể cả môn bị khóa)
            if self.proctors:
                idx = random.randint(0, len(schedule.courses) - 1)
                course = schedule.courses[idx]
                
                backup_data['course_indices'] = [idx]
                backup_data['old_values'] = [{
                    'date': course.assigned_date,
                    'time': course.assigned_time,
                    'room': course.assigned_room,
                    'proctor': course.assigned_proctor_id
                }]
                
                random_proctor = random.choice(self.proctors)
                course.assigned_proctor_id = random_proctor.proctor_id
            
            return backup_data
        
        # Chọn 1 môn ngẫu nhiên từ danh sách modifiable
        idx, course = random.choice(modifiable_courses)
        
        # Backup
        backup_data['course_indices'] = [idx]
        backup_data['old_values'] = [{
            'date': course.assigned_date,
            'time': course.assigned_time,
            'room': course.assigned_room,
            'proctor': course.assigned_proctor_id
        }]
        
        # Quyết định thay đổi gì (date/time/room/proctor)
        change_type = random.choice(['date', 'time', 'room', 'proctor', 'all'])
        
        # Modify (in-place)
        if change_type in ['date', 'all']:
            course.assigned_date = random.choice(self.available_dates)
        
        if change_type in ['time', 'all']:
            course.assigned_time = random.choice(self.available_times)
        
        if change_type in ['room', 'all']:
            # Tìm phòng tối ưu
            optimal_room = self._find_optimal_room(
                course.student_count,
                course.location,
                prefer_smaller=False
            )
            
            if optimal_room:
                course.assigned_room = optimal_room.room_id
            else:
                # Fallback: Ưu tiên phòng cùng địa điểm
                suitable_rooms = [
                    room for room in self.rooms
                    if room.location == course.location and 
                       room.capacity >= course.student_count
                ]
                
                if suitable_rooms and random.random() > 0.3:  # 70% chọn phòng phù hợp
                    course.assigned_room = random.choice(suitable_rooms).room_id
                else:
                    course.assigned_room = random.choice(self.rooms).room_id
        
        # Thay đổi giám thị (nếu có danh sách giám thị)
        if change_type in ['proctor', 'all'] and self.proctors:
            random_proctor = random.choice(self.proctors)
            course.assigned_proctor_id = random_proctor.proctor_id
        
        return backup_data
    
    def _undo_move(self, schedule: Schedule, backup_data: Dict[str, Any]) -> None:
        """
        Hoàn tác thay đổi dựa trên backup data (Rollback).
        
        Performance: O(k) với k là số courses bị thay đổi (thường là 1-2).
        
        Args:
            schedule: Lịch thi cần rollback.
            backup_data: Dữ liệu backup từ _perturb_move().
        """
        if not backup_data or not backup_data.get('course_indices'):
            return
        
        for idx, old_values in zip(backup_data['course_indices'], backup_data['old_values']):
            if 0 <= idx < len(schedule.courses):
                course = schedule.courses[idx]
                course.assigned_date = old_values['date']
                course.assigned_time = old_values['time']
                course.assigned_room = old_values['room']
                course.assigned_proctor_id = old_values.get('proctor')  # Restore proctor (có thể None)
    
    def _acceptance_probability(self, current_cost: float, new_cost: float, temperature: float) -> float:
        """
        Tính xác suất chấp nhận một bad move.
        
        Formula: P = exp(-ΔE / T)
            - ΔE > 0: Bad move (new worse than current)
            - T càng cao → P càng cao (chấp nhận nhiều bad moves)
            - T càng thấp → P càng thấp (chỉ chấp nhận good moves)
        
        Args:
            current_cost: Cost của solution hiện tại.
            new_cost: Cost của solution mới.
            temperature: Nhiệt độ hiện tại.
        
        Returns:
            float: Xác suất chấp nhận (0.0 - 1.0).
        """
        if new_cost < current_cost:
            return 1.0  # Always accept better solution
        
        delta_e = new_cost - current_cost
        
        try:
            probability = math.exp(-delta_e / temperature)
        except OverflowError:
            # Temperature quá nhỏ → probability ≈ 0
            probability = 0.0
        
        return probability
    
    def run(self) -> None:
        """
        Chạy thuật toán Simulated Annealing (OPTIMIZED VERSION).
        
        Main Loop (Optimized):
            1. Generate initial solution
            2. While T > T_min:
                a. Perturb (in-place modification với backup)
                b. Calculate new cost
                c. Calculate acceptance probability
                d. Accept/Reject:
                   - Accept: Giữ nguyên thay đổi
                   - Reject: Rollback bằng backup
                e. Update best solution (chỉ copy khi cần)
                f. Cool down temperature
                g. Emit signals to GUI
        
        Performance Improvements:
            - Loại bỏ deepcopy trong vòng lặp
            - Chỉ copy khi update best_solution (ít xảy ra)
            - Mỗi bước: O(1) hoặc O(k) nhỏ thay vì O(N)
        """
        try:
            # Setup
            self.is_running = True
            self.should_stop = False
            self.start_time = time.time()
            self.convergence_history = []
            self.accepted_moves = 0
            self.rejected_moves = 0
            self.total_neighbors = 0
            
            self._log("=" * 60)
            self._log("🔥 BẮT ĐẦU SIMULATED ANNEALING (OPTIMIZED)")
            self._log("=" * 60)
            
            # Step 1: Generate initial solution
            self._log("📊 Đang tạo lịch thi ban đầu...")
            current_schedule = self._generate_initial_solution()
            current_cost = current_schedule.fitness_score
            
            # Chỉ copy khi tạo best_solution (ít xảy ra)
            best_schedule = copy.deepcopy(current_schedule)
            best_cost = current_cost
            
            self._log(f"✓ Lịch ban đầu: Cost = {current_cost:.2f}")
            self.convergence_history.append(current_cost)
            
            # Step 2: Main SA loop (OPTIMIZED)
            temperature = self.initial_temperature
            iteration = 0
            
            self._log(f"🌡️ Nhiệt độ ban đầu: {temperature:.2f}")
            self._log(f"❄️ Nhiệt độ tối thiểu: {self.min_temperature:.2f}")
            self._log(f"🔽 Tốc độ làm lạnh: {self.cooling_rate}")
            self._log("-" * 60)
            
            while temperature > self.min_temperature and iteration < self.max_iterations:
                # Check stop flag
                if self.should_stop:
                    self._log("⚠️ Thuật toán đã bị dừng bởi người dùng")
                    break
                
                iteration += 1
                self.total_iterations = iteration
                
                # --- OPTIMIZED: Perturb với backup (in-place modification) ---
                backup_data = self._perturb_move(current_schedule)
                self.total_neighbors += 1
                
                # Calculate new cost (sau khi đã modify)
                new_cost = self.constraint_checker.calculate_total_violation(current_schedule)
                
                # Calculate acceptance probability
                accept_prob = self._acceptance_probability(current_cost, new_cost, temperature)
                
                # Decide whether to accept neighbor
                if random.random() < accept_prob:
                    # Accept: Giữ nguyên thay đổi (đã modify rồi)
                    current_cost = new_cost
                    self.accepted_moves += 1
                    
                    # Update best solution if better (chỉ copy khi cần)
                    if current_cost < best_cost:
                        best_schedule = copy.deepcopy(current_schedule)
                        best_cost = current_cost
                        self._log(f"🎯 Iteration {iteration}: NEW BEST! Cost = {best_cost:.2f}")
                else:
                    # Reject: Rollback bằng backup (hoàn tác thay đổi)
                    self._undo_move(current_schedule, backup_data)
                    # current_cost không đổi (vì đã rollback)
                    self.rejected_moves += 1
                
                # Store convergence history
                self.convergence_history.append(current_cost)
                
                # Cool down temperature
                temperature *= self.cooling_rate
                
                # Emit signals every 10 iterations (not too frequent to avoid GUI lag)
                if iteration % 10 == 0:
                    self.step_signal.emit(iteration, current_cost)
                    
                    # Calculate progress (based on temperature)
                    progress = int(
                        (1 - (temperature - self.min_temperature) / 
                         (self.initial_temperature - self.min_temperature)) * 100
                    )
                    self._emit_progress(progress, 100)
                
                # Log every 100 iterations
                if iteration % 100 == 0:
                    self._log(
                        f"Iter {iteration}: T={temperature:.2f}, "
                        f"Current={current_cost:.2f}, Best={best_cost:.2f}, "
                        f"Accept Rate={self.accepted_moves/self.total_neighbors*100:.1f}%"
                    )
            
            # Step 3: Finish
            self.end_time = time.time()
            self.best_solution = best_schedule
            self.current_solution = current_schedule
            
            # Calculate statistics
            execution_time = self.get_execution_time()
            improvement = ((self.convergence_history[0] - best_cost) / 
                          self.convergence_history[0] * 100) if self.convergence_history[0] > 0 else 0
            
            # Final log
            self._log("=" * 60)
            self._log("✅ HOÀN THÀNH SIMULATED ANNEALING (OPTIMIZED)")
            self._log("=" * 60)
            self._log(f"⏱️ Thời gian thực thi: {execution_time:.2f}s")
            self._log(f"🔁 Tổng số vòng lặp: {iteration}")
            self._log(f"📊 Cost ban đầu: {self.convergence_history[0]:.2f}")
            self._log(f"🎯 Cost tốt nhất: {best_cost:.2f}")
            self._log(f"📈 Cải thiện: {improvement:.2f}%")
            self._log(f"✔️ Accepted moves: {self.accepted_moves}")
            self._log(f"❌ Rejected moves: {self.rejected_moves}")
            self._log(f"📊 Acceptance rate: {self.accepted_moves/self.total_neighbors*100:.1f}%")
            
            # Check feasibility
            if self.constraint_checker.is_feasible(best_schedule):
                self._log("✅ Lịch thi KHẢ THI (không vi phạm hard constraints)")
            else:
                self._log("⚠️ Lịch thi CÒN VI PHẠM một số ràng buộc cứng")
            
            # Emit điểm cuối cùng nếu chưa được emit (đảm bảo chart có dữ liệu đầy đủ)
            if iteration % 10 != 0:
                self.step_signal.emit(iteration, best_cost)
                self._emit_progress(100, 100)
            
            # Emit finished signal
            self.finished_signal.emit(best_schedule)
            
        except Exception as e:
            self._log_error(f"Lỗi trong quá trình chạy SA: {str(e)}")
            import traceback
            self._log_error(traceback.format_exc())
        
        finally:
            self.is_running = False
            self._emit_progress(100, 100)
    
    @property
    def rooms_dict(self) -> Dict[str, Room]:
        """Helper property để truy cập rooms dictionary."""
        return self.constraint_checker.rooms_dict


