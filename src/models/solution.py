"""
Data class đại diện cho một giải pháp xếp lịch thi hoàn chỉnh.
Đây là đối tượng được các thuật toán (SA, PSO) thao tác và truyền qua lại với GUI.
"""

from dataclasses import dataclass, field
from typing import List

from .course import Course


@dataclass
class Schedule:
    """
    Class đại diện cho một lịch thi hoàn chỉnh (một solution candidate).
    
    Attributes:
        courses (List[Course]): Danh sách các môn học đã được xếp lịch.
        fitness_score (float): Điểm đánh giá chất lượng của lịch thi 
                               (càng thấp càng tốt - minimization problem).
    
    Note:
        - fitness_score được tính toán bởi hàm mục tiêu (cost function) dựa trên các ràng buộc:
          + Ràng buộc cứng: Trùng phòng, trùng giờ, quá sức chứa
          + Ràng buộc mềm: Khoảng cách giữa các ca thi, phân bố đều, lãng phí sức chứa
        - SA solver đã được optimize: Sử dụng in-place modification với backup/rollback
          thay vì deepcopy trong vòng lặp (chỉ dùng deepcopy khi update best_solution).
    """
    
    courses: List[Course] = field(default_factory=list)
    fitness_score: float = 0.0
    
    def get_scheduled_count(self) -> int:
        """
        Đếm số môn học đã được xếp lịch đầy đủ.
        
        Returns:
            int: Số lượng môn học đã có đủ thông tin ngày, giờ, phòng.
        """
        return sum(1 for course in self.courses if course.is_scheduled())
    
    def get_unscheduled_count(self) -> int:
        """
        Đếm số môn học chưa được xếp lịch.
        
        Returns:
            int: Số lượng môn học chưa xếp lịch hoặc xếp lịch chưa đầy đủ.
        """
        return len(self.courses) - self.get_scheduled_count()
    
    def is_complete(self) -> bool:
        """
        Kiểm tra xem lịch thi đã hoàn chỉnh chưa (tất cả môn học đã được xếp lịch).
        
        Returns:
            bool: True nếu tất cả môn học đã được xếp lịch đầy đủ.
        """
        return self.get_unscheduled_count() == 0
    
    def get_courses_by_date(self, date: str) -> List[Course]:
        """
        Lấy danh sách các môn học thi vào một ngày cụ thể.
        
        Args:
            date (str): Ngày cần tìm (định dạng phụ thuộc vào cách lưu trữ).
        
        Returns:
            List[Course]: Danh sách môn học thi vào ngày đó.
        """
        return [
            course for course in self.courses
            if course.assigned_date == date
        ]
    
    def get_courses_by_room(self, room_id: str) -> List[Course]:
        """
        Lấy danh sách các môn học được phân công vào một phòng cụ thể.
        
        Args:
            room_id (str): Mã phòng cần tìm.
        
        Returns:
            List[Course]: Danh sách môn học được xếp vào phòng đó.
        """
        return [
            course for course in self.courses
            if course.assigned_room == room_id
        ]
    
    def __str__(self) -> str:
        """
        Trả về chuỗi mô tả tổng quan về lịch thi.
        """
        total = len(self.courses)
        scheduled = self.get_scheduled_count()
        return (
            f"Lịch thi: {scheduled}/{total} môn đã xếp | "
            f"Fitness Score: {self.fitness_score:.2f}"
        )
    
    def __len__(self) -> int:
        """
        Trả về tổng số môn học trong lịch.
        """
        return len(self.courses)

