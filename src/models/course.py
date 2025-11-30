"""
Data class đại diện cho một môn học trong hệ thống xếp lịch thi.
Chứa thông tin cơ bản về môn học và các thuộc tính để lưu kết quả xếp lịch.

ENHANCED: Hỗ trợ chia môn học thành nhiều ca thi (sessions).
ENHANCED: Hỗ trợ khóa cứng lịch thi (Pinning) và thời lượng thi linh hoạt.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, timedelta


@dataclass
class Course:
    """
    Class đại diện cho một môn học/lớp học phần.
    
    ENHANCED: Hỗ trợ chia môn học thành nhiều ca thi (sessions).
    ENHANCED: Hỗ trợ khóa cứng lịch thi (is_locked) và thời lượng thi linh hoạt (duration).
    
    Attributes:
        course_id (str): Mã lớp học phần (định danh duy nhất).
        name (str): Tên môn học.
        location (str): Cơ sở học/thi (ví dụ: "Cơ sở 1", "Cơ sở 2").
        exam_format (str): Hình thức thi (ví dụ: "Tự luận", "Trắc nghiệm").
        note (str): Ghi chú bổ sung về môn học.
        student_count (int): Số lượng sinh viên đăng ký môn học (tổng số).
        assigned_date (Optional[str]): Ngày thi được phân công (None nếu chưa xếp lịch hoặc dùng sessions).
        assigned_time (Optional[str]): Giờ thi được phân công (None nếu chưa xếp lịch hoặc dùng sessions).
        assigned_room (Optional[str]): Phòng thi được phân công (None nếu chưa xếp lịch hoặc dùng sessions).
        assigned_proctor_id (Optional[str]): ID giám thị được phân công.
        sessions (Optional[List]): Danh sách các ca thi (None nếu môn học không được chia ca).
        max_session_size (int): Số lượng sinh viên tối đa trong một ca (mặc định: 100).
        is_locked (bool): Nếu True, thuật toán KHÔNG được thay đổi lịch của môn này (mặc định: False).
        duration (int): Thời lượng làm bài tính bằng phút (ví dụ: 60, 90, 120). Mặc định: 90.
    
    Note:
        - Nếu sessions không None: Môn học được chia thành nhiều ca, dùng sessions để xếp lịch.
        - Nếu sessions là None: Môn học chỉ có 1 ca, dùng assigned_date/time/room như cũ (backward compatible).
        - Tổng student_count của tất cả sessions phải bằng student_count của Course.
        - Nếu is_locked=True và đã có lịch: Lịch này sẽ được giữ nguyên trong quá trình tối ưu.
    """
    
    # Thông tin cơ bản từ dữ liệu đầu vào
    course_id: str
    name: str
    location: str
    exam_format: str
    note: str = ""
    student_count: int = 0
    
    # Kết quả xếp lịch (được gán bởi thuật toán)
    # Backward compatible: Dùng cho môn học không chia ca
    assigned_date: Optional[str] = None
    assigned_time: Optional[str] = None
    assigned_room: Optional[str] = None
    assigned_proctor_id: Optional[str] = None  # ID giám thị được phân công
    
    # DEPRECATED: Hỗ trợ sessions (giữ lại để backward compatibility)
    # Hiện tại hệ thống chia thành nhiều Course objects thay vì sessions
    sessions: Optional[List] = None  # List[CourseSession] - Legacy support only
    max_session_size: int = 100  # Số lượng sinh viên tối đa trong một ca (không còn sử dụng)
    
    # ENHANCED: Hỗ trợ khóa cứng lịch thi và thời lượng thi
    is_locked: bool = False  # Nếu True, lịch này KHÔNG được thay đổi bởi thuật toán
    duration: int = 90  # Thời lượng làm bài tính bằng phút (mặc định 90 phút)
    
    def is_scheduled(self) -> bool:
        """
        Kiểm tra xem môn học đã được xếp lịch đầy đủ chưa.
        
        Returns:
            bool: True nếu đã có đủ thông tin ngày, giờ và phòng thi.
        """
        # Nếu có sessions, kiểm tra tất cả sessions đã được xếp lịch
        if self.sessions:
            return all(session.is_scheduled() for session in self.sessions)
        
        # Backward compatible: Kiểm tra assigned_date/time/room
        # Note: assigned_proctor_id là optional, không bắt buộc để is_scheduled() = True
        return all([
            self.assigned_date is not None,
            self.assigned_time is not None,
            self.assigned_room is not None
        ])
    
    def clear_schedule(self) -> None:
        """
        Xóa thông tin xếp lịch của môn học (đặt lại về trạng thái chưa xếp lịch).
        Hữu ích khi cần reset hoặc tạo lịch mới.
        """
        # Xóa sessions nếu có
        if self.sessions:
            for session in self.sessions:
                session.clear_schedule()
        
        # Xóa thông tin cũ (backward compatible)
        self.assigned_date = None
        self.assigned_time = None
        self.assigned_room = None
        self.assigned_proctor_id = None
    
    def get_total_scheduled_students(self) -> int:
        """
        Lấy tổng số sinh viên đã được xếp lịch (từ các sessions).
        
        Returns:
            int: Tổng số sinh viên đã được xếp lịch.
        """
        if self.sessions:
            return sum(session.student_count for session in self.sessions if session.is_scheduled())
        elif self.is_scheduled():
            return self.student_count
        return 0
    
    def needs_splitting(self, max_capacity: int) -> bool:
        """
        Kiểm tra xem môn học có cần chia thành nhiều ca không.
        
        Args:
            max_capacity: Sức chứa tối đa của phòng lớn nhất.
        
        Returns:
            bool: True nếu student_count > max_capacity.
        """
        return self.student_count > max_capacity
    
    def get_session_count(self) -> int:
        """
        Lấy số lượng ca thi của môn học.
        
        Returns:
            int: Số lượng sessions nếu có, hoặc 1 nếu không chia ca.
        """
        if self.sessions:
            return len(self.sessions)
        return 1
    
    @property
    def start_time_obj(self) -> Optional[datetime]:
        """
        Tính toán thời gian bắt đầu thi dựa trên assigned_time.
        
        Returns:
            Optional[datetime]: Đối tượng datetime đại diện cho thời gian bắt đầu.
                               None nếu assigned_date hoặc assigned_time chưa xác định.
        """
        if self.assigned_date is None or self.assigned_time is None:
            return None
        try:
            # Kết hợp ngày và giờ
            datetime_str = f"{self.assigned_date} {self.assigned_time}"
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return None
    
    @property
    def end_time_obj(self) -> Optional[datetime]:
        """
        Tính toán thời gian kết thúc thi dựa trên assigned_time và duration.
        
        Returns:
            Optional[datetime]: Đối tượng datetime đại diện cho thời gian kết thúc.
                               None nếu assigned_date hoặc assigned_time chưa xác định.
        """
        start_time = self.start_time_obj
        if start_time is None:
            return None
        # Cộng thêm duration (tính bằng phút)
        return start_time + timedelta(minutes=self.duration)
    
    def __str__(self) -> str:
        """
        Trả về chuỗi mô tả ngắn gọn về môn học.
        """
        schedule_info = (
            f"{self.assigned_date} {self.assigned_time} - {self.assigned_room}"
            if self.is_scheduled()
            else "Chưa xếp lịch"
        )
        return f"[{self.course_id}] {self.name} - {schedule_info}"

