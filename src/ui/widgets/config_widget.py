"""
Widget cấu hình tham số cho thuật toán (SA và PSO).
Hỗ trợ chọn thuật toán, chỉnh tham số riêng biệt, Import dữ liệu.
Thêm: Cấu hình khoảng thời gian xếp lịch và các ràng buộc giám thị.
"""

from PyQt5.QtWidgets import (QVBoxLayout, QFormLayout, QHBoxLayout, 
                             QStackedWidget, QWidget, QGroupBox, QDateEdit, QLabel, QSpinBox,
                             QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QSize
from qfluentwidgets import (
    CardWidget, SpinBox, DoubleSpinBox, ComboBox, 
    StrongBodyLabel, BodyLabel, PushButton, PrimaryPushButton,
    InfoBar, InfoBarPosition
)
from typing import Dict, Any


class ConfigWidget(CardWidget):
    """
    Widget cấu hình tích hợp:
    - Import dữ liệu
    - Chọn thuật toán (SA/PSO)
    - Cấu hình tham số tương ứng
    """
    
    # Signals
    config_changed = pyqtSignal(dict)
    apply_clicked = pyqtSignal()
    reset_clicked = pyqtSignal()
    load_data_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._reset_defaults()

    def _init_ui(self):
        # Main layout (Responsive)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        # Set minimum width để prevent squishing
        self.setMinimumWidth(350)
        self.setMaximumWidth(500)
        
        # Create scroll area để tất cả content fit vào
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        # Container widget cho scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        
        # --- 1. HEADER & IMPORT ---
        header_layout = QHBoxLayout()
        title_label = StrongBodyLabel("⚙️ Cấu hình & Dữ liệu")
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        container_layout.addLayout(header_layout)
        
        # Nút Import (Responsive)
        self.load_data_btn = PushButton("📂 Import File Excel/CSV")
        self.load_data_btn.setToolTip("Tải danh sách Môn học và Phòng thi")
        self.load_data_btn.setMinimumHeight(36)
        self.load_data_btn.clicked.connect(self.load_data_clicked.emit)
        container_layout.addWidget(self.load_data_btn)
        
        # Label trạng thái
        self.data_status_label = BodyLabel("Trạng thái: Chưa có dữ liệu")
        self.data_status_label.setStyleSheet("color: #666; font-style: italic; font-size: 8pt")
        container_layout.addWidget(self.data_status_label)
        
        container_layout.addSpacing(8)
        
        # --- 2. DATE & TIME RANGE CONFIGURATION ---
        date_group = QGroupBox("📅 Cấu hình Khoảng Thời Gian Xếp Lịch")
        date_layout = QFormLayout(date_group)
        date_layout.setSpacing(15)
        date_layout.setLabelAlignment(Qt.AlignRight)
        
        # Ngày bắt đầu
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setToolTip("Ngày bắt đầu kỳ thi")
        date_layout.addRow(BodyLabel("Ngày bắt đầu:"), self.start_date)
        
        # Ngày kết thúc
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addDays(30))
        self.end_date.setCalendarPopup(True)
        self.end_date.setToolTip("Ngày kết thúc kỳ thi")
        date_layout.addRow(BodyLabel("Ngày kết thúc:"), self.end_date)
        
        # Kết nối sự kiện để validation
        self.start_date.dateChanged.connect(self._on_date_changed)
        self.end_date.dateChanged.connect(self._on_date_changed)
        
        # Label trạng thái ngày
        self.date_status_label = BodyLabel("✓ Hợp lệ")
        self.date_status_label.setStyleSheet("color: green; font-size: 9pt")
        date_layout.addRow("", self.date_status_label)
        
        container_layout.addWidget(date_group)
        
        # --- 3. PROCTOR CONSTRAINTS ---
        constraint_group = QGroupBox("👨‍🏫 Ràng Buộc Giám Thị")
        constraint_layout = QFormLayout(constraint_group)
        constraint_layout.setSpacing(15)
        constraint_layout.setLabelAlignment(Qt.AlignRight)
        
        # Số tối đa môn thi/tuần cho 1 giám thị
        self.max_exams_per_week = SpinBox()
        self.max_exams_per_week.setRange(1, 30)
        self.max_exams_per_week.setValue(5)
        self.max_exams_per_week.setToolTip("Tối đa số môn thi 1 giám thị gác trong 1 tuần")
        constraint_layout.addRow(
            BodyLabel("Tối đa môn/tuần/giám thị:"), 
            self.max_exams_per_week
        )
        
        # Số tối đa môn thi/ngày cho 1 giám thị
        self.max_exams_per_day = SpinBox()
        self.max_exams_per_day.setRange(1, 10)
        self.max_exams_per_day.setValue(3)
        self.max_exams_per_day.setToolTip("Tối đa số môn thi 1 giám thị gác trong 1 ngày")
        constraint_layout.addRow(
            BodyLabel("Tối đa môn/ngày/giám thị:"), 
            self.max_exams_per_day
        )
        
        # Thêm info label cho ràng buộc
        info_label = BodyLabel("Mỗi giám thị sẽ không được phân công quá số lượng trên.")
        info_label.setStyleSheet("color: #999; font-size: 8pt; font-style: italic")
        constraint_layout.addRow("", info_label)
        
        container_layout.addWidget(constraint_group)
        
        # --- 4. ALGORITHM SELECTION ---
        algo_group = QGroupBox("Chọn Thuật toán")
        algo_layout = QVBoxLayout(algo_group)
        
        self.algo_combo = ComboBox()
        self.algo_combo.addItems(["Simulated Annealing (SA)", "Particle Swarm Optimization (PSO)"])
        self.algo_combo.setToolTip("Chọn thuật toán để chạy xếp lịch")
        self.algo_combo.currentIndexChanged.connect(self._on_algo_changed)
        algo_layout.addWidget(self.algo_combo)
        
        container_layout.addWidget(algo_group)
        
        # --- 5. PARAMETERS STACK (Trang cấu hình riêng cho từng thuật toán) ---
        self.param_stack = QStackedWidget()
        
        # === Page 1: SA Parameters ===
        self.page_sa = QWidget()
        sa_layout = QFormLayout(self.page_sa)
        sa_layout.setSpacing(15)
        sa_layout.setLabelAlignment(Qt.AlignRight)
        
        self.sa_temp = DoubleSpinBox()
        self.sa_temp.setRange(10, 10000); self.sa_temp.setValue(1000)
        sa_layout.addRow(BodyLabel("Nhiệt độ (T₀):"), self.sa_temp)
        
        self.sa_cooling = DoubleSpinBox()
        self.sa_cooling.setRange(0.8, 0.9999); self.sa_cooling.setDecimals(4); self.sa_cooling.setValue(0.995)
        sa_layout.addRow(BodyLabel("Tỷ lệ làm mát (α):"), self.sa_cooling)
        
        self.sa_iter = SpinBox()
        self.sa_iter.setRange(100, 1000000); self.sa_iter.setValue(5000); self.sa_iter.setSingleStep(100)
        sa_layout.addRow(BodyLabel("Số vòng lặp tối đa:"), self.sa_iter)
        
        self.param_stack.addWidget(self.page_sa)
        
        # === Page 2: PSO Parameters ===
        self.page_pso = QWidget()
        pso_layout = QFormLayout(self.page_pso)
        pso_layout.setSpacing(15)
        pso_layout.setLabelAlignment(Qt.AlignRight)
        
        self.pso_swarm = SpinBox()
        self.pso_swarm.setRange(10, 500)
        self.pso_swarm.setValue(50)
        self.pso_swarm.setMaximumWidth(140)
        pso_layout.addRow(BodyLabel("Swarm Size (Hạt):"), self.pso_swarm)
        
        self.pso_iter = SpinBox()
        self.pso_iter.setRange(100, 100000)
        self.pso_iter.setValue(1000)
        self.pso_iter.setMaximumWidth(140)
        pso_layout.addRow(BodyLabel("Max Iterations:"), self.pso_iter)
        
        self.pso_w = DoubleSpinBox() # Inertia
        self.pso_w.setRange(0.1, 1.5)
        self.pso_w.setValue(0.7)
        self.pso_w.setSingleStep(0.1)
        self.pso_w.setMaximumWidth(140)
        pso_layout.addRow(BodyLabel("Inertia (w):"), self.pso_w)
        
        self.pso_c1 = DoubleSpinBox() # Cognitive
        self.pso_c1.setRange(0.1, 4.0)
        self.pso_c1.setValue(1.5)
        self.pso_c1.setSingleStep(0.1)
        self.pso_c1.setMaximumWidth(140)
        pso_layout.addRow(BodyLabel("Cognitive (c1):"), self.pso_c1)
        
        self.pso_c2 = DoubleSpinBox() # Social
        self.pso_c2.setRange(0.1, 4.0)
        self.pso_c2.setValue(1.5)
        self.pso_c2.setSingleStep(0.1)
        self.pso_c2.setMaximumWidth(140)
        pso_layout.addRow(BodyLabel("Social (c2):"), self.pso_c2)
        
        self.param_stack.addWidget(self.page_pso)
        
        container_layout.addWidget(self.param_stack)
        
        # --- 4. BUTTONS ---
        container_layout.addStretch()
        btn_layout = QHBoxLayout()
        
        self.reset_btn = PushButton("🔄 Reset")
        self.reset_btn.clicked.connect(self._reset_defaults)
        
        self.apply_btn = PrimaryPushButton("▶ Chạy Thuật Toán")
        self.apply_btn.clicked.connect(self.apply_clicked.emit)
        
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.apply_btn)
        
        container_layout.addLayout(btn_layout)
        
        # Set up scroll area
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _on_algo_changed(self, index):
        """Chuyển đổi giao diện tham số khi đổi thuật toán."""
        self.param_stack.setCurrentIndex(index)
    
    def _on_date_changed(self):
        """Validation ngày bắt đầu và kết thúc."""
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        
        if start > end:
            self.date_status_label.setText("⚠️ Ngày bắt đầu không được sau ngày kết thúc")
            self.date_status_label.setStyleSheet("color: #FF4D4F; font-size: 9pt")
        else:
            days_diff = (end - start).days + 1
            self.date_status_label.setText(f"✓ Hợp lệ ({days_diff} ngày)")
            self.date_status_label.setStyleSheet("color: green; font-size: 9pt")

    def _reset_defaults(self):
        """Khôi phục giá trị mặc định."""
        # Date defaults
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate().addDays(30))
        
        # Constraint defaults
        self.max_exams_per_week.setValue(5)
        self.max_exams_per_day.setValue(3)
        
        # SA Defaults
        self.sa_temp.setValue(1000.0)
        self.sa_cooling.setValue(0.995)
        self.sa_iter.setValue(5000)
        # PSO Defaults
        self.pso_swarm.setValue(50)
        self.pso_iter.setValue(1000)
        self.pso_w.setValue(0.7)
        self.pso_c1.setValue(1.5)
        self.pso_c2.setValue(1.5)
        # Reset algo
        self.algo_combo.setCurrentIndex(0)
        
        # Reset date validation
        self._on_date_changed()

    def get_config(self) -> Dict[str, Any]:
        """Lấy config dựa trên thuật toán đang chọn + cấu hình lịch."""
        algo_idx = self.algo_combo.currentIndex()
        algo_type = 'sa' if algo_idx == 0 else 'pso'
        
        config = {'algorithm': algo_type}
        
        # Thêm cấu hình lịch và ràng buộc
        config['schedule_config'] = {
            'start_date': self.start_date.date().toString('yyyy-MM-dd'),
            'end_date': self.end_date.date().toString('yyyy-MM-dd'),
            'max_exams_per_week': int(self.max_exams_per_week.value()),
            'max_exams_per_day': int(self.max_exams_per_day.value()),
        }
        
        if algo_type == 'sa':
            config.update({
                'initial_temperature': self.sa_temp.value(),
                'cooling_rate': self.sa_cooling.value(),
                'max_iterations': self.sa_iter.value(),
                'neighbor_type': 'swap'
            })
        else:
            config.update({
                'swarm_size': int(self.pso_swarm.value()),
                'max_iterations': int(self.pso_iter.value()),
                'w': self.pso_w.value(),
                'c1': self.pso_c1.value(),
                'c2': self.pso_c2.value()
            })
        return config
    
    def set_data_status(self, text: str, is_success: bool = True):
        """Cập nhật label trạng thái dữ liệu (Style đẹp)."""
        self.data_status_label.setText(f"Trạng thái: {text}")
        color = "green" if is_success else "red"
        self.data_status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 9pt")
    
    def get_schedule_config(self) -> Dict[str, Any]:
        """
        Lấy riêng cấu hình lịch thi.
        
        Returns:
            Dict chứa:
                - start_date: Ngày bắt đầu (YYYY-MM-DD)
                - end_date: Ngày kết thúc (YYYY-MM-DD)
                - max_exams_per_week: Tối đa môn/tuần/giám thị
                - max_exams_per_day: Tối đa môn/ngày/giám thị
        """
        return {
            'start_date': self.start_date.date().toString('yyyy-MM-dd'),
            'end_date': self.end_date.date().toString('yyyy-MM-dd'),
            'max_exams_per_week': int(self.max_exams_per_week.value()),
            'max_exams_per_day': int(self.max_exams_per_day.value()),
        }
    
    def get_proctor_constraints(self) -> Dict[str, int]:
        """
        Lấy ràng buộc giám thị.
        
        Returns:
            Dict chứa:
                - max_exams_per_week: Tối đa môn/tuần
                - max_exams_per_day: Tối đa môn/ngày
        """
        return {
            'max_exams_per_week': int(self.max_exams_per_week.value()),
            'max_exams_per_day': int(self.max_exams_per_day.value()),
        }
