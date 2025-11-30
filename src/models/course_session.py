"""
Data class đại diện cho một ca thi của môn học.
Một môn học có thể được chia thành nhiều ca thi (ví dụ: 200 sinh viên chia thành 2 ca, mỗi ca 100).

DEPRECATED: Class này được giữ lại để backward compatibility.
Hiện tại, hệ thống sử dụng cách tiếp cận đơn giản hơn: Chia môn học thành nhiều Course objects riêng biệt
thay vì sử dụng sessions (ví dụ: PHI101_C1, PHI101_C2 thay vì PHI101 với sessions).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CourseSession:
    """
    Class đại diện cho một ca thi của môn học.
    
    DEPRECATED: Class này được giữ lại để backward compatibility và xử lý dữ liệu cũ.
    Không nên tạo mới CourseSession objects. Thay vào đó, sử dụng nhiều Course objects riêng biệt.
    
    Attributes:
        session_id (str): ID của session (ví dụ: "CS101_S1", "CS101_S2").
        assigned_date (Optional[str]): Ngày thi được phân công.
        assigned_time (Optional[str]): Giờ thi được phân công.
        assigned_room (Optional[str]): Phòng thi được phân công.
        student_count (int): Số lượng sinh viên trong ca này.
    
    Note:
        - Một Course có thể có nhiều CourseSession (legacy support)
        - Tổng student_count của tất cả sessions = student_count của Course gốc
        - ConstraintChecker vẫn hỗ trợ kiểm tra courses có sessions để tương thích ngược
    """
    
    session_id: str
    assigned_date: Optional[str] = None
    assigned_time: Optional[str] = None
    assigned_room: Optional[str] = None
    student_count: int = 0
    
    def is_scheduled(self) -> bool:
        """
        Kiểm tra xem ca thi đã được xếp lịch đầy đủ chưa.
        
        Returns:
            bool: True nếu đã có đủ thông tin ngày, giờ và phòng thi.
        """
        return all([
            self.assigned_date is not None,
            self.assigned_time is not None,
            self.assigned_room is not None
        ])
    
    def clear_schedule(self) -> None:
        """Xóa thông tin xếp lịch của ca thi."""
        self.assigned_date = None
        self.assigned_time = None
        self.assigned_room = None
    
    def __str__(self) -> str:
        """Trả về chuỗi mô tả ca thi."""
        schedule_info = (
            f"{self.assigned_date} {self.assigned_time} - {self.assigned_room}"
            if self.is_scheduled()
            else "Chưa xếp lịch"
        )
        return f"[{self.session_id}] {schedule_info} ({self.student_count} SV)"

