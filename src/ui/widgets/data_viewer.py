"""
Data Viewer Widget - Hiển thị dữ liệu Excel được import dưới dạng bảng.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QTabWidget, QPushButton, QLabel, QHeaderView, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QBrush
from qfluentwidgets import InfoBar, InfoBarPosition
from typing import List, Dict, Any, Optional
import pandas as pd


class DataViewerWidget(QWidget):
    """
    Widget hiển thị dữ liệu từ các file Excel/CSV được import.
    
    Features:
        - Hiển thị dữ liệu Subjects (Môn học)
        - Hiển thị dữ liệu Rooms (Phòng thi)
        - Hiển thị dữ liệu Proctors (Giám thị)
        - Color-coded rows
        - Thống kê dữ liệu
        - Export dữ liệu
    """
    
    def __init__(self, parent=None):
        """Khởi tạo Data Viewer Widget."""
        super().__init__(parent)
        self.setObjectName("DataViewerWidget")
        
        # Data storage
        self.subjects_df: Optional[pd.DataFrame] = None
        self.rooms_df: Optional[pd.DataFrame] = None
        self.proctors_df: Optional[pd.DataFrame] = None
        
        # Setup UI
        self._init_ui()
    
    def _init_ui(self):
        """Khởi tạo giao diện (Responsive)."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ========== HEADER ==========
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # Title (Responsive font size)
        title_label = QLabel("📊 Dữ Liệu Được Import")
        title_font = title_label.font()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Stats label (Responsive)
        self.stats_label = QLabel("Chờ dữ liệu...")
        self.stats_label.setStyleSheet("color: #666; font-size: 9pt;")
        header_layout.addWidget(self.stats_label)
        
        main_layout.addLayout(header_layout)
        
        # ========== TAB WIDGET ==========
        self.tab_widget = QTabWidget()
        
        # Tab 1: Subjects
        self.subjects_table = QTableWidget()
        self._setup_table(self.subjects_table)
        self.tab_widget.addTab(self.subjects_table, "📚 Môn Học (Subjects)")
        
        # Tab 2: Rooms
        self.rooms_table = QTableWidget()
        self._setup_table(self.rooms_table)
        self.tab_widget.addTab(self.rooms_table, "🏫 Phòng Thi (Rooms)")
        
        # Tab 3: Proctors
        self.proctors_table = QTableWidget()
        self._setup_table(self.proctors_table)
        self.tab_widget.addTab(self.proctors_table, "👨‍🏫 Giám Thị (Proctors)")
        
        main_layout.addWidget(self.tab_widget)
        
        # ========== FOOTER ==========
        footer_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.clicked.connect(self.refresh_data)
        footer_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("💾 Xuất Excel")
        export_btn.clicked.connect(self.export_data)
        footer_layout.addWidget(export_btn)
        
        footer_layout.addStretch()
        
        self.info_label = QLabel("Chưa có dữ liệu")
        self.info_label.setStyleSheet("color: #999; font-size: 9pt; font-style: italic;")
        footer_layout.addWidget(self.info_label)
        
        main_layout.addLayout(footer_layout)
        
        self.setLayout(main_layout)
    
    def _setup_table(self, table: QTableWidget):
        """Setup table style."""
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E0E0E0;
                background-color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #1976D2;
                color: white;
                padding: 5px;
                border: 1px solid #1565C0;
                font-weight: bold;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #EEEEEE;
            }
            QTableWidget::item:selected {
                background-color: #BBDEFB;
                color: #000;
            }
        """)
        
        # Enable sorting
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        
        # Resize columns
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Set row height
        table.verticalHeader().setDefaultSectionSize(35)
    
    def set_subjects_data(self, courses: List[Any]):
        """
        Thiết lập dữ liệu môn học.
        
        Args:
            courses: Danh sách Course objects
        """
        self.subjects_table.setRowCount(0)
        self.subjects_table.setColumnCount(0)
        
        if not courses:
            self.subjects_table.setRowCount(1)
            self.subjects_table.setColumnCount(1)
            item = QTableWidgetItem("Không có dữ liệu môn học")
            item.setForeground(QColor("#999"))
            self.subjects_table.setItem(0, 0, item)
            return
        
        # Set columns
        columns = [
            "Mã LHP", "Tên HP", "SL ĐK", "Địa điểm", 
            "Hình thức", "Thời lượng (phút)", "Cố định", "Ghi chú"
        ]
        self.subjects_table.setColumnCount(len(columns))
        self.subjects_table.setHorizontalHeaderLabels(columns)
        
        # Set rows
        self.subjects_table.setRowCount(len(courses))
        
        for row, course in enumerate(courses):
            # Mã LHP
            item = QTableWidgetItem(str(course.course_id))
            item.setTextAlignment(Qt.AlignCenter)
            self.subjects_table.setItem(row, 0, item)
            
            # Tên HP
            item = QTableWidgetItem(str(course.name))
            self.subjects_table.setItem(row, 1, item)
            
            # SL ĐK
            item = QTableWidgetItem(str(course.student_count))
            item.setTextAlignment(Qt.AlignCenter)
            self.subjects_table.setItem(row, 2, item)
            
            # Địa điểm
            item = QTableWidgetItem(str(course.location if hasattr(course, 'location') else 'N/A'))
            self.subjects_table.setItem(row, 3, item)
            
            # Hình thức
            item = QTableWidgetItem(str(course.exam_format if hasattr(course, 'exam_format') else 'N/A'))
            self.subjects_table.setItem(row, 4, item)
            
            # Thời lượng
            duration = getattr(course, 'duration', 120)
            item = QTableWidgetItem(str(duration))
            item.setTextAlignment(Qt.AlignCenter)
            self.subjects_table.setItem(row, 5, item)
            
            # Cố định
            is_locked = getattr(course, 'is_locked', False)
            locked_text = "✅" if is_locked else "❌"
            item = QTableWidgetItem(locked_text)
            item.setTextAlignment(Qt.AlignCenter)
            if is_locked:
                item.setForeground(QColor("#00AA00"))
            self.subjects_table.setItem(row, 6, item)
            
            # Ghi chú
            item = QTableWidgetItem(str(course.note if hasattr(course, 'note') else ''))
            self.subjects_table.setItem(row, 7, item)
            
            # Color alternate rows
            if row % 2 == 0:
                for col in range(len(columns)):
                    self.subjects_table.item(row, col).setBackground(QBrush(QColor("#F5F5F5")))
        
        # Auto-resize columns
        self.subjects_table.resizeColumnsToContents()
    
    def set_rooms_data(self, rooms: List[Any]):
        """
        Thiết lập dữ liệu phòng thi.
        
        Args:
            rooms: Danh sách Room objects
        """
        self.rooms_table.setRowCount(0)
        self.rooms_table.setColumnCount(0)
        
        if not rooms:
            self.rooms_table.setRowCount(1)
            self.rooms_table.setColumnCount(1)
            item = QTableWidgetItem("Không có dữ liệu phòng thi")
            item.setForeground(QColor("#999"))
            self.rooms_table.setItem(0, 0, item)
            return
        
        # Set columns
        columns = ["Tên Phòng", "Sức Chứa", "Địa Điểm", "Dung Lượng Hiện Tại"]
        self.rooms_table.setColumnCount(len(columns))
        self.rooms_table.setHorizontalHeaderLabels(columns)
        
        # Set rows
        self.rooms_table.setRowCount(len(rooms))
        
        for row, room in enumerate(rooms):
            # Tên Phòng (room_id)
            item = QTableWidgetItem(room.room_id)
            self.rooms_table.setItem(row, 0, item)
            
            # Sức Chứa
            item = QTableWidgetItem(str(room.capacity))
            item.setTextAlignment(Qt.AlignCenter)
            self.rooms_table.setItem(row, 1, item)
            
            # Địa Điểm
            item = QTableWidgetItem(room.location)
            self.rooms_table.setItem(row, 2, item)
            
            # Dung Lượng Hiện Tại (tính toán)
            current_capacity = getattr(room, 'current_capacity', 0)
            capacity_percent = (current_capacity / room.capacity * 100) if room.capacity > 0 else 0
            item = QTableWidgetItem(f"{current_capacity}/{room.capacity} ({capacity_percent:.0f}%)")
            item.setTextAlignment(Qt.AlignCenter)
            
            # Color based on utilization
            if capacity_percent >= 80:
                item.setForeground(QColor("#D32F2F"))  # Red
            elif capacity_percent >= 50:
                item.setForeground(QColor("#F57C00"))  # Orange
            else:
                item.setForeground(QColor("#00AA00"))  # Green
            
            self.rooms_table.setItem(row, 3, item)
            
            # Color alternate rows
            if row % 2 == 0:
                for col in range(len(columns)):
                    self.rooms_table.item(row, col).setBackground(QBrush(QColor("#F5F5F5")))
        
        self.rooms_table.resizeColumnsToContents()
    
    def set_proctors_data(self, proctors: List[Any]):
        """
        Thiết lập dữ liệu giám thị.
        
        Args:
            proctors: Danh sách Proctor objects
        """
        self.proctors_table.setRowCount(0)
        self.proctors_table.setColumnCount(0)
        
        if not proctors:
            self.proctors_table.setRowCount(1)
            self.proctors_table.setColumnCount(1)
            item = QTableWidgetItem("Không có dữ liệu giám thị")
            item.setForeground(QColor("#999"))
            self.proctors_table.setItem(0, 0, item)
            return
        
        # Set columns
        columns = ["Mã GT", "Họ Tên", "Cơ Sở", "Số Môn Đảm Nhận"]
        self.proctors_table.setColumnCount(len(columns))
        self.proctors_table.setHorizontalHeaderLabels(columns)
        
        # Set rows
        self.proctors_table.setRowCount(len(proctors))
        
        for row, proctor in enumerate(proctors):
            # Mã GT
            item = QTableWidgetItem(str(getattr(proctor, 'proctor_id', 'N/A')))
            item.setTextAlignment(Qt.AlignCenter)
            self.proctors_table.setItem(row, 0, item)
            
            # Họ Tên
            item = QTableWidgetItem(proctor.name)
            self.proctors_table.setItem(row, 1, item)
            
            # Cơ Sở
            item = QTableWidgetItem(getattr(proctor, 'location', 'N/A'))
            self.proctors_table.setItem(row, 2, item)
            
            # Số Môn Đảm Nhận
            assigned_count = len(getattr(proctor, 'assigned_courses', []))
            item = QTableWidgetItem(str(assigned_count))
            item.setTextAlignment(Qt.AlignCenter)
            
            # Color based on workload
            if assigned_count >= 5:
                item.setForeground(QColor("#D32F2F"))  # Red (overloaded)
            elif assigned_count >= 3:
                item.setForeground(QColor("#F57C00"))  # Orange (moderate)
            else:
                item.setForeground(QColor("#00AA00"))  # Green (light)
            
            self.proctors_table.setItem(row, 3, item)
            
            # Color alternate rows
            if row % 2 == 0:
                for col in range(len(columns)):
                    self.proctors_table.item(row, col).setBackground(QBrush(QColor("#F5F5F5")))
        
        self.proctors_table.resizeColumnsToContents()
    
    def update_stats(self, subjects_count: int = 0, rooms_count: int = 0, proctors_count: int = 0):
        """
        Cập nhật thống kê.
        
        Args:
            subjects_count: Số môn học
            rooms_count: Số phòng thi
            proctors_count: Số giám thị
        """
        total = subjects_count + rooms_count + proctors_count
        if total > 0:
            self.stats_label.setText(
                f"📚 {subjects_count} Môn | 🏫 {rooms_count} Phòng | 👨‍🏫 {proctors_count} Giám thị"
            )
            self.info_label.setText("✅ Dữ liệu đã được tải thành công")
            self.info_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.stats_label.setText("Chưa có dữ liệu")
            self.info_label.setText("❌ Chưa import dữ liệu")
            self.info_label.setStyleSheet("color: red; font-weight: bold;")
    
    def refresh_data(self):
        """Làm mới dữ liệu."""
        self.info_label.setText("🔄 Đang làm mới...")
        # Dữ liệu sẽ được refresh từ main_window khi có update
    
    def export_data(self):
        """Xuất dữ liệu ra Excel."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Lưu dữ liệu",
            "",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.xlsx'):
                    with pd.ExcelWriter(file_path) as writer:
                        if self.subjects_df is not None:
                            self.subjects_df.to_excel(writer, sheet_name='Subjects', index=False)
                        if self.rooms_df is not None:
                            self.rooms_df.to_excel(writer, sheet_name='Rooms', index=False)
                        if self.proctors_df is not None:
                            self.proctors_df.to_excel(writer, sheet_name='Proctors', index=False)
                else:
                    # For CSV, save the first available dataframe
                    if self.subjects_df is not None:
                        self.subjects_df.to_csv(file_path, index=False)
                
                self.info_label.setText(f"✅ Đã xuất dữ liệu: {file_path}")
                self.info_label.setStyleSheet("color: green;")
            except Exception as e:
                self.info_label.setText(f"❌ Lỗi xuất: {str(e)}")
                self.info_label.setStyleSheet("color: red;")
