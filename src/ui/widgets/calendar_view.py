"""
Widget Calendar View - Hiển thị lịch thi dưới dạng ma trận theo tuần.
Cột: Phòng thi, Hàng: Ca thi (Giờ x Thứ trong tuần)
Ô: Tên môn học + Tên giám thị
Có công cụ chuyển đổi giữa các tuần khác nhau.
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple, Set

import sys
from pathlib import Path

# Import models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from src.models.solution import Schedule
from src.models.room import Room


class CalendarView(QWidget):
    """
    Widget hiển thị lịch thi dưới dạng ma trận theo tuần.
    
    - Cột (Horizontal): Danh sách các Phòng thi
    - Hàng (Vertical): Các Ca thi (Giờ x Thứ trong tuần)
    - Ô (Cell): Tên Môn học + Tên Giám thị (đầy đủ hoặc ID)
    - Công cụ chuyển đổi giữa các tuần khác nhau
    
    Attributes:
        table: QTableWidget chứa dữ liệu
        schedule: Schedule object
        rooms: Danh sách Room objects
        proctors_dict: Dictionary map proctor_id -> Proctor object
        current_week_index: Index tuần hiện tại
        weeks: Danh sách các tuần trong lịch
    """
    
    def __init__(self, parent=None):
        """Khởi tạo Calendar View."""
        super().__init__(parent)
        self.table = QTableWidget()
        self.schedule: Optional[Schedule] = None
        self.rooms: List[Room] = []
        self.proctors_dict: Dict = {}
        self.current_week_index: int = 0
        self.weeks: List[Tuple[datetime, datetime]] = []  # (start_date, end_date) của mỗi tuần
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Thiết lập giao diện (Responsive)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ========== TOOLBAR ==========
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)
        
        # Nút "Tuần Trước" (Responsive)
        self.prev_btn = QPushButton("◄ Tuần Trước")
        self.prev_btn.setMinimumWidth(100)
        self.prev_btn.setMinimumHeight(36)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                font-size: 11pt;
                font-weight: bold;
                padding: 6px 12px;
                background-color: #E3F2FD;
                border: 2px solid #1976D2;
                border-radius: 6px;
                color: #1565C0;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
            QPushButton:pressed {
                background-color: #90CAF9;
            }
        """)
        self.prev_btn.clicked.connect(self._previous_week)
        toolbar_layout.addWidget(self.prev_btn)
        
        # Label tuần (Responsive)
        self.week_label = QLabel("📅 Tuần: ---")
        self.week_label.setAlignment(Qt.AlignCenter)
        font = self.week_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.week_label.setFont(font)
        self.week_label.setStyleSheet("color: #1565C0; padding: 8px;")
        self.week_label.setMinimumHeight(36)
        toolbar_layout.addWidget(self.week_label)
        
        # ComboBox tuần (Responsive)
        self.week_combo = QComboBox()
        self.week_combo.setMinimumWidth(250)
        self.week_combo.setMinimumHeight(36)
        self.week_combo.setStyleSheet("""
            QComboBox {
                font-size: 10pt;
                padding: 6px;
                border: 2px solid #BDBDBD;
                border-radius: 5px;
                background-color: #F5F5F5;
            }
            QComboBox:focus {
                border: 2px solid #1976D2;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 40px;
            }
        """)
        self.week_combo.currentIndexChanged.connect(self._on_week_selected)
        toolbar_layout.addWidget(self.week_combo)
        
        # Nút "Tuần Sau" (Responsive)
        self.next_btn = QPushButton("Tuần Sau ►")
        self.next_btn.setMinimumWidth(100)
        self.next_btn.setMinimumHeight(36)
        self.next_btn.setStyleSheet("""
            QPushButton {
                font-size: 11pt;
                font-weight: bold;
                padding: 6px 12px;
                background-color: #E3F2FD;
                border: 2px solid #1976D2;
                border-radius: 6px;
                color: #1565C0;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
            QPushButton:pressed {
                background-color: #90CAF9;
            }
        """)
        self.next_btn.clicked.connect(self._next_week)
        toolbar_layout.addWidget(self.next_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # ========== TABLE ==========
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionMode(3)  # NoSelection
        self.table.setFocusPolicy(Qt.NoFocus)
        
        # Styling table - Enhanced
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #BBDEFB;
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                margin: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                border: 1px solid #BBDEFB;
                background-color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #1976D2;
                color: white;
                padding: 8px;
                border: 1px solid #1565C0;
                font-weight: bold;
                font-size: 12pt;
            }
            QHeaderView {
                border-radius: 3px;
            }
        """)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def update_data(self, schedule: Optional[Schedule], rooms: Optional[List[Room]], 
                   proctors_dict: Optional[Dict] = None) -> None:
        """
        Cập nhật dữ liệu lịch thi vào ma trận.
        
        Args:
            schedule (Optional[Schedule]): Lịch thi cần hiển thị
            rooms (Optional[List[Room]]): Danh sách phòng thi
            proctors_dict (Optional[Dict]): Dictionary map proctor_id -> Proctor object
        """
        # Xử lý dữ liệu rỗng
        if not schedule or not schedule.courses or not rooms:
            self._clear_table()
            return
        
        self.schedule = schedule
        self.rooms = rooms
        self.proctors_dict = proctors_dict or {}
        
        # Tính danh sách tuần
        self._calculate_weeks()
        
        # Populate combo box tuần
        self._populate_week_combo()
        
        # Reset index
        self.current_week_index = 0
        
        # Hiển thị tuần đầu tiên
        if self.weeks:
            self._update_table_for_week(0)
    
    def _calculate_weeks(self) -> None:
        """
        Tính danh sách tất cả các tuần trong lịch thi.
        
        Một tuần được định nghĩa là từ Thứ 2 đến Chủ Nhật.
        """
        if not self.schedule or not self.schedule.courses:
            self.weeks = []
            return
        
        # Lấy tất cả ngày thi duy nhất
        dates_set = set()
        for course in self.schedule.courses:
            if course.assigned_date:
                try:
                    # Parse date string (định dạng YYYY-MM-DD)
                    date_obj = datetime.strptime(course.assigned_date, "%Y-%m-%d").date()
                    dates_set.add(date_obj)
                except ValueError:
                    pass
        
        if not dates_set:
            self.weeks = []
            return
        
        dates_sorted = sorted(dates_set)
        
        # Tính tuần (Monday = 0, Sunday = 6)
        weeks_dict = {}
        for date_obj in dates_sorted:
            weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
            
            # Tính ngày bắt đầu tuần (Thứ 2)
            monday = date_obj - timedelta(days=weekday)
            sunday = monday + timedelta(days=6)
            
            week_key = monday
            if week_key not in weeks_dict:
                weeks_dict[week_key] = (monday, sunday)
        
        # Sort by week start date
        self.weeks = sorted(weeks_dict.values(), key=lambda x: x[0])
    
    def _populate_week_combo(self) -> None:
        """Populate combo box với danh sách các tuần."""
        self.week_combo.blockSignals(True)
        self.week_combo.clear()
        
        for idx, (start_date, end_date) in enumerate(self.weeks):
            label = f"Tuần {idx + 1}: {start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')}"
            self.week_combo.addItem(label, idx)
        
        self.week_combo.blockSignals(False)
    
    def _on_week_selected(self, index: int) -> None:
        """Xử lý khi người dùng chọn tuần từ combo box."""
        if 0 <= index < len(self.weeks):
            self._update_table_for_week(index)
    
    def _previous_week(self) -> None:
        """Chuyển đến tuần trước."""
        if self.current_week_index > 0:
            self.current_week_index -= 1
            self.week_combo.setCurrentIndex(self.current_week_index)
    
    def _next_week(self) -> None:
        """Chuyển đến tuần tiếp theo."""
        if self.current_week_index < len(self.weeks) - 1:
            self.current_week_index += 1
            self.week_combo.setCurrentIndex(self.current_week_index)
    
    def _update_table_for_week(self, week_index: int) -> None:
        """
        Cập nhật bảng cho một tuần cụ thể.
        
        Args:
            week_index (int): Index của tuần
        """
        if week_index < 0 or week_index >= len(self.weeks):
            self._clear_table()
            return
        
        self.current_week_index = week_index
        start_date, end_date = self.weeks[week_index]
        
        # Update label
        self.week_label.setText(
            f"Tuần: {start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')}"
        )
        
        # Lấy courses cho tuần này
        week_courses = self._get_courses_for_week(start_date, end_date)
        
        if not week_courses:
            self._clear_table()
            return
        
        # Lấy phòng thi
        room_ids = self._get_sorted_room_ids()
        if not room_ids:
            self._clear_table()
            return
        
        # Lấy ca thi trong tuần
        time_slots = self._get_sorted_time_slots_for_courses(week_courses)
        if not time_slots:
            self._clear_table()
            return
        
        # Tạo ma trận
        self.table.setColumnCount(len(room_ids))
        self.table.setRowCount(len(time_slots))
        
        # Set header
        self.table.setHorizontalHeaderLabels(room_ids)
        
        # Set row labels (ngày + giờ để dễ đọc hơn)
        row_labels = []
        for date_str, time_str in time_slots:
            # Parse date để lấy ngày/tháng
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                date_label = date_obj.strftime("%a %d/%m")  # "Mon 15/11"
                row_labels.append(f"{date_label}\n{time_str}")
            except ValueError:
                row_labels.append(f"{date_str}\n{time_str}")
        
        self.table.setVerticalHeaderLabels(row_labels)
        
        # Điền dữ liệu
        self._fill_courses_to_table_week(week_courses, room_ids, time_slots)
        
        # Style
        self._style_table()
    
    def _get_courses_for_week(self, start_date, end_date) -> List:
        """Lấy tất cả courses trong tuần từ start_date đến end_date (inclusive)."""
        week_courses = []
        
        for course in self.schedule.courses:
            if not course.assigned_date:
                continue
            
            try:
                course_date = datetime.strptime(course.assigned_date, "%Y-%m-%d").date()
                if start_date <= course_date <= end_date:
                    week_courses.append(course)
            except ValueError:
                pass
        
        return week_courses
    
    def _get_sorted_room_ids(self) -> List[str]:
        """
        Lấy danh sách ID phòng thi được sắp xếp.
        
        Returns:
            List[str]: Danh sách phòng ID sắp xếp theo tên
        """
        room_dict = {room.room_id: room for room in self.rooms}
        room_ids = list(room_dict.keys())
        room_ids.sort()
        return room_ids
    
    def _get_sorted_time_slots_for_courses(self, courses: List) -> List[Tuple[str, str]]:
        """
        Lấy danh sách các ca thi (ngày + giờ) duy nhất từ danh sách courses, được sắp xếp.
        
        Returns:
            List[Tuple[str, str]]: Danh sách (date, time) sắp xếp
        """
        time_slots_set = set()
        
        for course in courses:
            if course.is_scheduled():
                time_slots_set.add((course.assigned_date, course.assigned_time))
        
        if not time_slots_set:
            return []
        
        # Chuyển thành list và sắp xếp
        time_slots_list = list(time_slots_set)
        time_slots_list.sort(key=lambda x: (x[0], x[1]))
        
        return time_slots_list
    
    def _fill_courses_to_table_week(self, week_courses: List, room_ids: List[str], 
                                    time_slots: List[Tuple[str, str]]) -> None:
        """
        Điền dữ liệu các môn học vào bảng cho tuần này.
        
        Args:
            week_courses: Danh sách courses trong tuần
            room_ids: Danh sách phòng ID
            time_slots: Danh sách ca thi
        """
        # Tạo dict mapping cho tìm kiếm nhanh
        room_col_map = {room_id: idx for idx, room_id in enumerate(room_ids)}
        time_slot_row_map = {slot: idx for idx, slot in enumerate(time_slots)}
        
        # List màu khác nhau cho từng phòng
        colors = [
            QColor(200, 230, 255),  # Xanh nhạt
            QColor(200, 255, 230),  # Lục nhạt
            QColor(255, 230, 200),  # Cam nhạt
            QColor(255, 200, 230),  # Hồng nhạt
            QColor(230, 230, 255),  # Tím nhạt
            QColor(255, 255, 200),  # Vàng nhạt
        ]
        
        # Duyệt qua courses
        for course in week_courses:
            if not course.is_scheduled():
                continue
            
            # Tìm hàng (row)
            slot = (course.assigned_date, course.assigned_time)
            if slot not in time_slot_row_map:
                continue
            row = time_slot_row_map[slot]
            
            # Tìm cột (col)
            if course.assigned_room not in room_col_map:
                continue
            col = room_col_map[course.assigned_room]
            
            # Tạo text cho ô
            cell_text = self._create_cell_text(course)
            
            # Tạo QTableWidgetItem
            item = QTableWidgetItem(cell_text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Read-only
            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            
            # Set font - TO HƠN
            font = item.font()
            font.setPointSize(11)
            font.setBold(True)
            item.setFont(font)
            
            # Set màu nền - rotate colors
            color_idx = col % len(colors)
            color = colors[color_idx]
            item.setBackground(color)
            
            # Set màu chữ
            item.setForeground(QColor(0, 0, 0))
            
            # Đặt vào table
            self.table.setItem(row, col, item)
    
    def _create_cell_text(self, course) -> str:
        """
        Tạo text hiển thị trong ô.
        
        Format: "Tên Môn\n(GT: Tên Giám thị)" 
        
        Args:
            course: Course object
        
        Returns:
            str: Text để hiển thị
        """
        text = course.name
        
        # Thêm giám thị nếu có
        if course.assigned_proctor_id:
            proctor_name = course.assigned_proctor_id
            
            # Nếu có proctors_dict, lấy tên đầy đủ
            if self.proctors_dict:
                proctor_obj = self.proctors_dict.get(course.assigned_proctor_id)
                if proctor_obj and hasattr(proctor_obj, 'name'):
                    proctor_name = proctor_obj.name
            
            text += f"\n👨‍🏫 {proctor_name}"
        
        return text
    
    def _style_table(self) -> None:
        """Thiết lập styling cho bảng (Responsive)."""
        # Responsive column width - tính dựa trên tổng chiều rộng table
        total_width = self.table.width() if self.table.width() > 0 else 1000
        col_width = max(120, int(total_width / max(1, self.table.columnCount())))
        
        for col in range(self.table.columnCount()):
            self.table.setColumnWidth(col, col_width)
        
        # Responsive row height - scale based on content
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 80)
        
        # Enable word wrap for all items
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setFlags(item.flags() | Qt.TextWordWrap)
    
    def _clear_table(self) -> None:
        """Xóa tất cả dữ liệu trong bảng."""
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.week_label.setText("Tuần: ---")
        self.week_combo.clear()
        self.schedule = None
        self.rooms = []
        self.weeks = []
        self.current_week_index = 0
    
    def export_as_image(self, file_path: str) -> bool:
        """
        Xuất bảng ra hình ảnh (PNG).
        
        Args:
            file_path (str): Đường dẫn file hình ảnh
        
        Returns:
            bool: True nếu xuất thành công
        """
        try:
            pixmap = self.table.grab()
            pixmap.save(file_path)
            return True
        except Exception as e:
            print(f"Lỗi xuất hình ảnh: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Lấy thống kê từ lịch thi.
        
        Returns:
            Dict chứa thống kê
        """
        if not self.schedule or not self.schedule.courses:
            return {}
        
        total_courses = len([c for c in self.schedule.courses if c.is_scheduled()])
        total_rooms = len(self.rooms)
        
        # Tính tổng ca thi
        all_time_slots = set()
        for course in self.schedule.courses:
            if course.assigned_date and course.assigned_time:
                all_time_slots.add((course.assigned_date, course.assigned_time))
        
        total_time_slots = len(all_time_slots)
        
        return {
            'total_courses': total_courses,
            'total_rooms': total_rooms,
            'total_time_slots': total_time_slots,
        }
