"""
File: src/ui/widgets/schedule_table.py
Widget hiển thị bảng kết quả xếp lịch thi với lựa chọn giữa View bảng và View lưới.
"""

from PyQt5.QtWidgets import (
    QHeaderView, QTableWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, 
    QRadioButton, QButtonGroup, QLabel
)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from qfluentwidgets import TableWidget

import sys
from pathlib import Path

# Thêm đường dẫn root để import models
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.solution import Schedule
from src.models.course import Course
from src.models.room import Room
from src.ui.widgets.calendar_view import CalendarView


class ScheduleResultTable(QWidget):
    """
    Widget kết hợp: Bảng kết quả xếp lịch + Thời khóa biểu dạng lưới.
    Người dùng có thể chuyển đổi giữa 2 view bằng radio button.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.schedule = None
        self.rooms_dict = {}
        self.proctors_dict = {}
        
        # Tạo 2 view
        self.table_widget = TableWidget()
        self.calendar_view = CalendarView()
        
        # Setup UI
        self._setup_ui()
        
        # Cấu hình bảng mặc định
        self._configure_table()
    
    def _setup_ui(self) -> None:
        """Thiết lập giao diện (Responsive)."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Toolbar cho chuyển đổi view
        toolbar_layout = QHBoxLayout()
        
        view_label = QLabel("Chế độ xem:")
        toolbar_layout.addWidget(view_label)
        
        self.view_group = QButtonGroup()
        
        self.table_radio = QRadioButton("Bảng chi tiết")
        self.table_radio.setChecked(True)
        self.table_radio.clicked.connect(self._switch_to_table)
        self.view_group.addButton(self.table_radio, 0)
        toolbar_layout.addWidget(self.table_radio)
        
        self.calendar_radio = QRadioButton("Thời khóa biểu (Lưới)")
        self.calendar_radio.clicked.connect(self._switch_to_calendar)
        self.view_group.addButton(self.calendar_radio, 1)
        toolbar_layout.addWidget(self.calendar_radio)
        
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        
        # Stack widget để chứa 2 view
        self.table_widget.setBorderVisible(True)
        self.table_widget.setBorderRadius(8)
        self.table_widget.setWordWrap(False)
        self.table_widget.setAlternatingRowColors(True)
        
        main_layout.addWidget(self.table_widget)
        main_layout.addWidget(self.calendar_view)
        
        # Ẩn calendar_view lúc đầu
        self.calendar_view.hide()
    
    def _configure_table(self) -> None:
        """Cấu hình bảng."""
        # Định nghĩa cột
        headers = [
            "Mã LHP", "Tên HP", "Ngày thi", "Giờ thi", 
            "Phòng thi", "Giám thị", "Địa điểm", "Hình thức thi", 
            "Sĩ số/Sức chứa", "Ghi chú"
        ]
        
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # Cấu hình độ rộng cột
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Màu sắc highlight
        self.COLOR_ERROR = QColor("#FF4D4F")
        self.COLOR_WARNING = QColor("#FAAD14")
        self.COLOR_DEFAULT = None
    
    def _switch_to_table(self) -> None:
        """Chuyển sang chế độ xem bảng."""
        self.table_widget.show()
        self.calendar_view.hide()
    
    def _switch_to_calendar(self) -> None:
        """Chuyển sang chế độ xem lưới."""
        self.table_widget.hide()
        self.calendar_view.show()

    def update_data(self, schedule: Schedule, rooms_dict: dict, proctors_dict: dict = None):
        """
        Cập nhật dữ liệu hiển thị trong cả bảng lẫn lưới.
        
        Args:
            schedule: Lịch thi cần hiển thị.
            rooms_dict: Dictionary map room_id -> Room object.
            proctors_dict: Dictionary map proctor_id -> Proctor object (optional).
        """
        self.schedule = schedule
        self.rooms_dict = rooms_dict
        self.proctors_dict = proctors_dict or {}
        
        # Cập nhật bảng
        self._update_table_data()
        
        # Cập nhật lưới
        if rooms_dict:
            rooms_list = list(rooms_dict.values())
            self.calendar_view.update_data(schedule, rooms_list, proctors_dict)

    def _update_table_data(self) -> None:
        """Cập nhật dữ liệu trong bảng chi tiết."""
        self.table_widget.setRowCount(0)
        
        if not self.schedule or not self.schedule.courses:
            return

        self.table_widget.setUpdatesEnabled(False)

        sorted_courses = sorted(
            self.schedule.courses, 
            key=lambda x: (str(x.assigned_date), str(x.assigned_time), str(x.assigned_room))
        )

        for row_idx, course in enumerate(sorted_courses):
            self.table_widget.insertRow(row_idx)
            
            assigned_room_obj = self.rooms_dict.get(course.assigned_room)
            
            capacity_str = "?"
            room_capacity_val = 0
            if assigned_room_obj:
                capacity_str = str(assigned_room_obj.capacity)
                room_capacity_val = assigned_room_obj.capacity
            
            student_info = f"{course.student_count}/{capacity_str}"
            
            # Lấy tên giám thị (hoặc ID nếu không tìm thấy)
            proctor_name = "---"
            if course.assigned_proctor_id:
                proctor_obj = self.proctors_dict.get(course.assigned_proctor_id)
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
                item = QTableWidgetItem(str(value)) 
                
                if row_text_color:
                    item.setForeground(QBrush(row_text_color))
                
                if col_idx in [1, 9]:  # Cột "Tên HP" và "Ghi chú" căn trái
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                
                self.table_widget.setItem(row_idx, col_idx, item)

        self.table_widget.setUpdatesEnabled(True)
