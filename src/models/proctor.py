"""
Data class đại diện cho một giám thị trong hệ thống xếp lịch thi.
Chứa thông tin cơ bản về giám thị để phân công coi thi.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Proctor:
    """
    Class đại diện cho một giám thị.
    
    Attributes:
        proctor_id (str): Mã giám thị (định danh duy nhất).
        name (str): Tên giám thị.
        location (Optional[str]): Cơ sở làm việc (nếu có).
    
    Note:
        - proctor_id được sử dụng để phân công giám thị cho các môn học.
        - location có thể được dùng để ưu tiên phân công giám thị ở cùng cơ sở với phòng thi.
    """
    
    proctor_id: str
    name: str
    location: Optional[str] = None
    
    def __str__(self) -> str:
        """
        Trả về chuỗi mô tả ngắn gọn về giám thị.
        """
        location_str = f" ({self.location})" if self.location else ""
        return f"[{self.proctor_id}] {self.name}{location_str}"

