"""
File: src/ui/widgets/schedule_table.py
Widget hiển thị bảng kết quả xếp lịch thi.
SỬA LỖI: Dùng QTableWidgetItem thay vì TableItem.
"""

from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem  # <--- IMPORT QTableWidgetItem TẠI ĐÂY
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from qfluentwidgets import TableWidget # <--- BỎ TableItem

import sys
from pathlib import Path

# Thêm đường dẫn root để import models
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.solution import Schedule
from src.models.course import Course
from src.models.room import Room

class ScheduleResultTable(TableWidget):
    """
    Bảng hiển thị kết quả xếp lịch thi.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Cấu hình giao diện bảng
        self.setBorderVisible(True)
        self.setBorderRadius(8)
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)
        
        # 2. Định nghĩa cột
        headers = [
            "Mã LHP", "Tên HP", "Ngày thi", "Giờ thi", 
            "Phòng thi", "Giám thị", "Địa điểm", "Hình thức thi", 
            "Sĩ số/Sức chứa", "Ghi chú"
        ]
        
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 3. Cấu hình độ rộng cột
        header = self.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Màu sắc highlight
        self.COLOR_ERROR = QColor("#FF4D4F")
        self.COLOR_WARNING = QColor("#FAAD14")
        self.COLOR_DEFAULT = None 

    def update_data(self, schedule: Schedule, rooms_dict: dict, proctors_dict: dict = None):
        """
        Cập nhật dữ liệu hiển thị trong bảng.
        
        Args:
            schedule: Lịch thi cần hiển thị.
            rooms_dict: Dictionary map room_id -> Room object.
            proctors_dict: Dictionary map proctor_id -> Proctor object (optional).
        """
        self.setRowCount(0)
        
        if not schedule or not schedule.courses:
            return

        self.setUpdatesEnabled(False)
        
        # Xử lý proctors_dict (có thể None nếu không có giám thị)
        if proctors_dict is None:
            proctors_dict = {}

        sorted_courses = sorted(
            schedule.courses, 
            key=lambda x: (str(x.assigned_date), str(x.assigned_time), str(x.assigned_room))
        )

        for row_idx, course in enumerate(sorted_courses):
            self.insertRow(row_idx)
            
            assigned_room_obj = rooms_dict.get(course.assigned_room)
            
            capacity_str = "?"
            room_capacity_val = 0
            if assigned_room_obj:
                capacity_str = str(assigned_room_obj.capacity)
                room_capacity_val = assigned_room_obj.capacity
            
            student_info = f"{course.student_count}/{capacity_str}"
            
            # Lấy tên giám thị (hoặc ID nếu không tìm thấy)
            proctor_name = "---"
            if course.assigned_proctor_id:
                proctor_obj = proctors_dict.get(course.assigned_proctor_id)
                if proctor_obj:
                    proctor_name = proctor_obj.name
                else:
                    proctor_name = course.assigned_proctor_id  # Fallback: hiển thị ID
            
            row_data = [
                course.course_id, course.name,
                course.assigned_date or "---", course.assigned_time or "---",
                course.assigned_room or "---", proctor_name,
                course.location, course.exam_format, student_info, course.note
            ]

            row_text_color = self.COLOR_DEFAULT
            is_error = False
            
            # Logic Highlight
            if course.assigned_room and assigned_room_obj:
                if course.student_count > room_capacity_val:
                    row_text_color = self.COLOR_ERROR
                    is_error = True
            
            if course.assigned_room and assigned_room_obj and not is_error:
                req_loc = course.location.strip().lower()
                act_loc = assigned_room_obj.location.strip().lower()
                if req_loc != act_loc:
                    row_text_color = self.COLOR_WARNING

            for col_idx, value in enumerate(row_data):
                # --- SỬA Ở ĐÂY: Dùng QTableWidgetItem ---
                item = QTableWidgetItem(str(value)) 
                
                if row_text_color:
                    item.setForeground(QBrush(row_text_color))
                
                if col_idx in [1, 9]:  # Cột "Tên HP" và "Ghi chú" căn trái
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                
                self.setItem(row_idx, col_idx, item)

        self.setUpdatesEnabled(True)