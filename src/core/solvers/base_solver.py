"""
Base class cho các thuật toán tối ưu xếp lịch thi.
Kế thừa từ QThread để chạy thuật toán trên luồng riêng biệt, tránh làm đơ giao diện.
Cung cấp interface chung cho SA, PSO và các thuật toán khác.
"""

from PyQt5.QtCore import QThread, pyqtSignal
from typing import List, Dict, Any, Optional
from abc import ABCMeta, abstractmethod
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Import models
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.solution import Schedule
from src.models.course import Course
from src.models.room import Room
from src.models.proctor import Proctor


# ============================================================================
# FIX METACLASS CONFLICT
# ============================================================================
class QThreadMeta(type(QThread), ABCMeta):
    """
    Combined metaclass để giải quyết conflict giữa QThread và ABC.
    
    QThread có metaclass: sip.wrappertype
    ABC có metaclass: ABCMeta
    
    Cần tạo metaclass mới kế thừa cả 2 để không bị conflict.
    """
    pass


class BaseSolver(QThread, metaclass=QThreadMeta):
    """
    Abstract Base Class cho các thuật toán tối ưu (SA, PSO, GA, ...).
    
    Kế thừa từ QThread để:
        - Chạy thuật toán trên luồng riêng (không block GUI)
        - Gửi tín hiệu về GUI để cập nhật real-time
        - Có thể dừng an toàn khi người dùng bấm nút Stop
    
    Signals:
        step_signal(int, float): Phát tín hiệu sau mỗi iteration
            - Param 1 (int): Số vòng lặp hiện tại
            - Param 2 (float): Cost/fitness của solution hiện tại
        
        finished_signal(Schedule): Phát tín hiệu khi thuật toán kết thúc
            - Param: Solution tốt nhất tìm được
        
        progress_signal(int): Phát tín hiệu để cập nhật progress bar
            - Param: Phần trăm hoàn thành (0-100)
        
        log_signal(str): Phát tín hiệu để ghi log lên GUI
            - Param: Thông báo log
        
        error_signal(str): Phát tín hiệu khi có lỗi xảy ra
            - Param: Thông báo lỗi
    
    Attributes:
        courses (List[Course]): Danh sách môn học cần xếp lịch
        rooms (List[Room]): Danh sách phòng thi có sẵn
        best_solution (Schedule): Solution tốt nhất tìm được
        convergence_history (List[float]): Lịch sử cost qua các iteration
        is_running (bool): Trạng thái đang chạy hay không
        should_stop (bool): Cờ để dừng thuật toán an toàn
    """
    
    # Định nghĩa các signals
    # step_signal có thể phát 2 hoặc 6 tham số:
    # - 2 params: (iteration: int, cost: float)
    # - 6 params: (iteration: int, cost: float, temperature: float, inertia: float, acceptance_rate: float, updates: int)
    step_signal = pyqtSignal(int, float, float, float, float, int)  # All 6 params
    finished_signal = pyqtSignal(object)  # (best_schedule)
    progress_signal = pyqtSignal(int)     # (percentage: 0-100)
    log_signal = pyqtSignal(str)          # (log_message)
    error_signal = pyqtSignal(str)        # (error_message)
    
    def __init__(self, 
                 courses: List[Course], 
                 rooms: List[Room],
                 config: Optional[Dict[str, Any]] = None,
                 proctors: Optional[List[Proctor]] = None,
                 parent=None):
        """
        Khởi tạo Base Solver.
        
        Args:
            courses (List[Course]): Danh sách môn học cần xếp lịch.
            rooms (List[Room]): Danh sách phòng thi có sẵn.
            config (Dict[str, Any], optional): Dictionary chứa các tham số cấu hình thuật toán.
                Ví dụ: {'max_iterations': 1000, 'temperature': 100, ...}
            proctors (List[Proctor], optional): Danh sách giám thị có sẵn.
            parent (QObject, optional): Parent object (theo chuẩn Qt).
        """
        super().__init__(parent)
        
        # Dữ liệu đầu vào
        self.courses: List[Course] = courses
        self.rooms: List[Room] = rooms
        self.proctors: List[Proctor] = proctors or []  # Danh sách giám thị (có thể rỗng)
        self.config: Dict[str, Any] = config or {}
        
        # Kết quả và trạng thái
        self.best_solution: Optional[Schedule] = None
        self.current_solution: Optional[Schedule] = None
        self.convergence_history: List[float] = []
        
        # Control flags
        self.is_running: bool = False
        self.should_stop: bool = False
        
        # Thống kê
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.total_iterations: int = 0
        
        # ENHANCED: Cấu hình cho dải thời gian linh hoạt
        self.exam_dates: List[str] = self.config.get('exam_dates', None)
        self.daily_start_time: str = self.config.get('daily_start_time', '07:30')
        self.daily_end_time: str = self.config.get('daily_end_time', '14:30')
        
        # Tạo không gian tìm kiếm chung cho mọi thuật toán
        if self.exam_dates is None:
            self.available_dates = self._generate_exam_dates()
        else:
            self.available_dates = self.exam_dates
        
        self.available_times = self._generate_time_slots()
        
        # Validate input
        self._validate_input()
    
    def _validate_input(self) -> None:
        """
        Kiểm tra tính hợp lệ của dữ liệu đầu vào.
        
        Raises:
            ValueError: Nếu dữ liệu không hợp lệ.
        """
        if not self.courses:
            raise ValueError("Danh sách môn học không được rỗng!")
        
        if not self.rooms:
            raise ValueError("Danh sách phòng thi không được rỗng!")
    
    @abstractmethod
    def run(self) -> None:
        """
        Method chính của QThread - Chạy thuật toán tối ưu.
        
        Method này PHẢI được override bởi các lớp con (SA, PSO, ...).
        
        Cấu trúc chuẩn của run():
            1. Khởi tạo solution ban đầu
            2. Vòng lặp chính:
                - Kiểm tra should_stop
                - Thực hiện một bước của thuật toán
                - Emit step_signal để cập nhật GUI
            3. Emit finished_signal khi xong
        
        Example:
            def run(self):
                self.is_running = True
                self.start_time = time.time()
                
                # Initialize
                current = self.generate_initial_solution()
                
                # Main loop
                for i in range(self.max_iterations):
                    if self.should_stop:
                        break
                    
                    # Algorithm logic here...
                    cost = self.calculate_cost(current)
                    
                    # Emit signals
                    self.step_signal.emit(i, cost)
                
                self.end_time = time.time()
                self.finished_signal.emit(self.best_solution)
                self.is_running = False
        """
        pass
    
    def stop(self) -> None:
        """
        Dừng thuật toán một cách an toàn (graceful shutdown).
        
        Method này được gọi khi:
            - User bấm nút "Stop" trên GUI
            - Muốn cancel task đang chạy
        
        Cơ chế:
            - Set cờ should_stop = True
            - Vòng lặp trong run() sẽ kiểm tra cờ này và thoát
            - Đảm bảo không làm crash chương trình
        """
        if self.is_running:
            self.should_stop = True
            self._log("⚠ Đang dừng thuật toán...")
        else:
            self._log("ℹ Thuật toán chưa chạy hoặc đã dừng")
    
    def get_best_solution(self) -> Optional[Schedule]:
        """
        Lấy solution tốt nhất hiện tại.
        
        Returns:
            Schedule hoặc None nếu chưa có solution nào.
        """
        return self.best_solution
    
    def get_convergence_history(self) -> List[float]:
        """
        Lấy lịch sử hội tụ (cost theo từng iteration).
        
        Dùng để vẽ biểu đồ convergence trên GUI.
        
        Returns:
            List[float]: Danh sách các giá trị cost theo thời gian.
        """
        return self.convergence_history
    
    def get_execution_time(self) -> float:
        """
        Tính thời gian thực thi của thuật toán.
        
        Returns:
            float: Thời gian thực thi (giây) hoặc 0 nếu chưa chạy xong.
        """
        if self.start_time is None:
            return 0.0
        
        if self.end_time is None:
            # Đang chạy -> tính thời gian hiện tại
            return time.time() - self.start_time
        
        return self.end_time - self.start_time
    
    def _generate_exam_dates(self) -> List[str]:
        """
        Tạo danh sách ngày thi từ schedule_config hoặc mặc định.
        
        Returns:
            List[str]: Danh sách ngày (format: "YYYY-MM-DD").
        """
        # Lấy cấu hình lịch nếu có
        schedule_config = self.config.get('schedule_config', {})
        
        if schedule_config and 'start_date' in schedule_config and 'end_date' in schedule_config:
            # Sử dụng khoảng thời gian từ config
            start_str = schedule_config['start_date']
            end_str = schedule_config['end_date']
            
            try:
                start = datetime.strptime(start_str, "%Y-%m-%d")
                end = datetime.strptime(end_str, "%Y-%m-%d")
                
                dates = []
                current = start
                while current <= end:
                    dates.append(current.strftime("%Y-%m-%d"))
                    current += timedelta(days=1)
                
                return dates
            except (ValueError, KeyError, TypeError):
                pass
        
        # Mặc định: 14 ngày bắt đầu từ 2025-06-01
        dates = []
        base_date = "2025-06-01"
        start = datetime.strptime(base_date, "%Y-%m-%d")
        for i in range(14):
            date = start + timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        return dates
    
    def _generate_time_slots(self) -> List[str]:
        """
        Tạo danh sách các ca thi trong ngày dựa trên cấu hình.
        
        ENHANCED: Hỗ trợ dải thời gian linh hoạt từ daily_start_time đến daily_end_time.
        Hiện tại sử dụng danh sách cố định để tương thích với yêu cầu hiện tại.
        
        Returns:
            List[str]: Danh sách giờ thi (format: "HH:MM").
        """
        # Sử dụng danh sách cố định hiện tại
        # TODO: Có thể mở rộng để tính toán dựa trên daily_start_time, daily_end_time và khoảng cách
        return ["07:30", "09:30", "13:30", "15:30"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Lấy các thống kê tổng quan về quá trình chạy thuật toán.
        
        Returns:
            Dict chứa các thông tin:
                - execution_time: Thời gian chạy (giây)
                - total_iterations: Tổng số vòng lặp đã chạy
                - best_cost: Cost của solution tốt nhất
                - initial_cost: Cost ban đầu (nếu có)
                - improvement: Mức cải thiện (%)
        """
        stats = {
            'execution_time': self.get_execution_time(),
            'total_iterations': self.total_iterations,
            'convergence_history': self.convergence_history,
        }
        
        if self.best_solution:
            stats['best_cost'] = self.best_solution.fitness_score
        
        if len(self.convergence_history) > 0:
            stats['initial_cost'] = self.convergence_history[0]
            
            if stats.get('best_cost') is not None and stats['initial_cost'] > 0:
                improvement = (
                    (stats['initial_cost'] - stats['best_cost']) 
                    / stats['initial_cost'] * 100
                )
                stats['improvement_percentage'] = improvement
        
        return stats
    
    def reset(self) -> None:
        """
        Reset trạng thái của solver (chuẩn bị cho lần chạy mới).
        
        Xóa:
            - Best solution
            - Convergence history
            - Các cờ trạng thái
        """
        self.best_solution = None
        self.current_solution = None
        self.convergence_history = []
        self.is_running = False
        self.should_stop = False
        self.start_time = None
        self.end_time = None
        self.total_iterations = 0
        
        self._log("✓ Solver đã được reset")
    
    def _emit_progress(self, current_iteration: int, max_iterations: int) -> None:
        """
        Helper method để emit progress signal.
        
        Args:
            current_iteration (int): Vòng lặp hiện tại.
            max_iterations (int): Tổng số vòng lặp.
        """
        if max_iterations > 0:
            percentage = int((current_iteration / max_iterations) * 100)
            self.progress_signal.emit(percentage)
    
    def _log(self, message: str) -> None:
        """
        Helper method để ghi log (wrapper cho log_signal).
        
        Args:
            message (str): Thông báo cần ghi.
        """
        self.log_signal.emit(message)
    
    def _find_optimal_room(self, student_count: int, location: str, 
                          prefer_smaller: bool = True) -> Optional[Room]:
        """
        Tìm phòng tối ưu cho số lượng sinh viên.
        
        ENHANCED: Tối ưu hóa lựa chọn phòng dựa trên utilization.
        
        Strategy:
            - Ưu tiên phòng cùng địa điểm
            - Ưu tiên phòng có sức chứa phù hợp (không quá lớn, không quá nhỏ)
            - Nếu prefer_smaller=True: Ưu tiên phòng nhỏ nhất đủ sức chứa
            - Nếu prefer_smaller=False: Ưu tiên phòng có utilization tốt nhất (60-90%)
        
        Args:
            student_count (int): Số lượng sinh viên.
            location (str): Địa điểm yêu cầu.
            prefer_smaller (bool): True nếu ưu tiên phòng nhỏ hơn, False nếu ưu tiên utilization.
        
        Returns:
            Optional[Room]: Phòng tối ưu hoặc None nếu không tìm thấy.
        """
        # Lọc phòng cùng địa điểm và đủ sức chứa
        suitable_rooms = [
            room for room in self.rooms
            if room.location == location and room.capacity >= student_count
        ]
        
        if not suitable_rooms:
            return None
        
        if prefer_smaller:
            # Ưu tiên phòng nhỏ nhất đủ sức chứa
            return min(suitable_rooms, key=lambda r: r.capacity)
        else:
            # Ưu tiên phòng có utilization tốt nhất (60-90% là lý tưởng)
            best_room = None
            best_score = -1
            
            for room in suitable_rooms:
                utilization = student_count / room.capacity
                # Tính điểm: utilization càng gần 80% càng tốt
                if 0.6 <= utilization <= 0.9:
                    score = 1.0 - abs(utilization - 0.8)  # Điểm cao nhất khi utilization = 80%
                elif utilization < 0.6:
                    score = utilization * 0.5  # Phạt nếu utilization thấp
                else:
                    score = (1.0 - utilization) * 0.5  # Phạt nếu utilization quá cao (>90%)
                
                if score > best_score:
                    best_score = score
                    best_room = room
            
            return best_room if best_room else suitable_rooms[0]
    
    def _split_course_into_multiple_courses(self, course: Course, max_capacity: int) -> List[Course]:
        """
        Chia môn học thành nhiều Course objects riêng biệt (thay vì sessions).
        
        Strategy đơn giản hơn: Mỗi ca thi = 1 Course object riêng.
        
        Args:
            course (Course): Môn học cần chia.
            max_capacity (int): Sức chứa tối đa của phòng lớn nhất.
        
        Returns:
            List[Course]: Danh sách các Course objects đã được chia.
        """
        # Tính số ca cần thiết (làm tròn lên)
        num_sessions = (course.student_count + max_capacity - 1) // max_capacity
        if num_sessions < 1:
            num_sessions = 1
        
        # Tính số sinh viên mỗi ca (chia đều)
        students_per_session = course.student_count // num_sessions
        remainder = course.student_count % num_sessions  # Số dư để phân bổ vào các ca đầu
        
        # Tạo các Course objects
        split_courses = []
        remaining_students = course.student_count
        
        for i in range(num_sessions):
            # Phân bổ số sinh viên: các ca đầu nhận thêm 1 nếu có số dư
            if i < remainder:
                session_students = students_per_session + 1
            else:
                session_students = students_per_session
            
            # Đảm bảo không vượt quá max_capacity
            session_students = min(session_students, max_capacity, remaining_students)
            
            if session_students > 0:
                # Tạo Course mới với course_id = "PHI101_C1", "PHI101_C2", ...
                new_course = Course(
                    course_id=f"{course.course_id}_C{i+1}",
                    name=course.name,
                    location=course.location,
                    exam_format=course.exam_format,
                    note=f"{course.note} (Ca {i+1})" if course.note else f"Ca {i+1}",
                    student_count=session_students
                )
                split_courses.append(new_course)
                remaining_students -= session_students
        
        # Đảm bảo tất cả sinh viên đã được phân bổ
        if remaining_students > 0 and split_courses:
            split_courses[-1].student_count += remaining_students
        
        return split_courses
    
    def _prepare_courses_with_sessions(self, courses: List[Course], 
                                      auto_split: bool = True) -> List[Course]:
        """
        Chuẩn bị danh sách courses, tự động chia thành nhiều Course objects nếu cần.
        
        ENHANCED: Thay vì dùng sessions, chia thành nhiều Course objects riêng biệt.
        
        Strategy:
            - Nếu số lượng sinh viên > max_capacity: Chia thành nhiều Course
            - Nếu không có phòng đủ sức chứa cho toàn bộ số sinh viên: Chia thành nhiều Course
            - Mỗi ca thi = 1 Course object riêng với course_id = "PHI101_C1", "PHI101_C2", ...
        
        Args:
            courses (List[Course]): Danh sách môn học gốc.
            auto_split (bool): True nếu tự động chia môn học thành nhiều ca.
        
        Returns:
            List[Course]: Danh sách courses đã được xử lý (có thể có nhiều Course từ 1 môn gốc).
        """
        if not auto_split:
            return courses
        
        # Tìm sức chứa tối đa
        max_capacity = max((room.capacity for room in self.rooms), default=100)
        
        # Chia các môn học cần thiết
        processed_courses = []
        for course in courses:
            # Kiểm tra xem có phòng nào đủ sức chứa cho toàn bộ số sinh viên không
            suitable_rooms = [
                room for room in self.rooms
                if room.location == course.location and room.capacity >= course.student_count
            ]
            
            # Nếu số lượng sinh viên > max_capacity HOẶC không có phòng phù hợp
            if course.needs_splitting(max_capacity) or not suitable_rooms:
                # Chia thành nhiều Course objects
                split_courses = self._split_course_into_multiple_courses(course, max_capacity)
                processed_courses.extend(split_courses)
                self._log(f"📋 Đã chia môn {course.course_id} ({course.student_count} SV) thành {len(split_courses)} ca thi riêng biệt")
            else:
                processed_courses.append(course)
        
        return processed_courses
    
    def _log_error(self, error_message: str) -> None:
        """
        Helper method để ghi error log.
        
        Args:
            error_message (str): Thông báo lỗi.
        """
        self.error_signal.emit(f"❌ ERROR: {error_message}")
    
    def __str__(self) -> str:
        """
        Trả về chuỗi mô tả solver.
        """
        return (
            f"{self.__class__.__name__} - "
            f"Courses: {len(self.courses)}, "
            f"Rooms: {len(self.rooms)}, "
            f"Running: {self.is_running}"
        )


class SolverConfig:
    """
    Helper class để quản lý cấu hình của các solver.
    Giúp code clean hơn và dễ validate.
    """
    
    def __init__(self, **kwargs):
        """
        Khởi tạo config từ keyword arguments.
        
        Example:
            config = SolverConfig(
                max_iterations=1000,
                initial_temperature=100,
                cooling_rate=0.95
            )
        """
        self.params = kwargs
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị của một parameter.
        
        Args:
            key (str): Tên parameter.
            default (Any): Giá trị mặc định nếu không tìm thấy.
        
        Returns:
            Giá trị của parameter.
        """
        return self.params.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Cập nhật giá trị của một parameter.
        
        Args:
            key (str): Tên parameter.
            value (Any): Giá trị mới.
        """
        self.params[key] = value
    
    def validate(self, required_keys: List[str]) -> bool:
        """
        Kiểm tra xem config có đủ các parameter bắt buộc không.
        
        Args:
            required_keys (List[str]): Danh sách các parameter bắt buộc.
        
        Returns:
            bool: True nếu hợp lệ.
        
        Raises:
            ValueError: Nếu thiếu parameter bắt buộc.
        """
        missing = [key for key in required_keys if key not in self.params]
        
        if missing:
            raise ValueError(f"Thiếu các parameter bắt buộc: {missing}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Chuyển config thành dictionary.
        
        Returns:
            Dict chứa tất cả parameters.
        """
        return self.params.copy()
    
    def __str__(self) -> str:
        """
        Trả về chuỗi mô tả config.
        """
        return f"SolverConfig({self.params})"

