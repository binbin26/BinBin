"""
Data class đại diện cho một phòng thi trong hệ thống xếp lịch.
Chứa thông tin về sức chứa và vị trí địa lý của phòng.
"""

from dataclasses import dataclass


@dataclass
class Room:
    """
    Class đại diện cho một phòng thi.
    
    Attributes:
        room_id (str): Tên/mã phòng (ví dụ: "A101", "B205").
        capacity (int): Sức chứa tối đa của phòng (số lượng sinh viên).
        location (str): Cơ sở mà phòng thuộc về (ví dụ: "Cơ sở 1", "Cơ sở 2").
    
    Note:
        - capacity được sử dụng như một ràng buộc cứng: 
          Không được phân công một môn học có student_count > capacity vào phòng này.
        - location được dùng để đảm bảo môn học được thi ở đúng cơ sở.
    """
    
    room_id: str
    capacity: int
    location: str
    
    def can_accommodate(self, student_count: int) -> bool:
        """
        Kiểm tra xem phòng có đủ sức chứa cho số lượng sinh viên không.
        
        Args:
            student_count (int): Số lượng sinh viên cần chứa.
        
        Returns:
            bool: True nếu phòng đủ sức chứa, False nếu không đủ.
        """
        return self.capacity >= student_count
    
    def matches_location(self, required_location: str) -> bool:
        """
        Kiểm tra xem phòng có khớp với yêu cầu về cơ sở không.
        
        Args:
            required_location (str): Cơ sở yêu cầu.
        
        Returns:
            bool: True nếu khớp cơ sở, False nếu không khớp.
        """
        return self.location == required_location
    
    def __str__(self) -> str:
        """
        Trả về chuỗi mô tả ngắn gọn về phòng thi.
        """
        return f"Phòng {self.room_id} ({self.location}) - Sức chứa: {self.capacity}"

