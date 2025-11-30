"""
Dialog cấu hình tham số cho Benchmark (So sánh SA vs PSO).
Cho phép người dùng nhập cấu hình riêng cho từng thuật toán.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, PushButton,
    StrongBodyLabel, BodyLabel
)
from typing import Dict, Any


class BenchmarkConfigDialog(QDialog):
    """
    Dialog cấu hình tham số cho Benchmark.
    
    Cho phép người dùng nhập:
    - Số vòng lặp cho SA (sa_iterations)
    - Số vòng lặp cho PSO (pso_iterations)
    - Swarm size cho PSO (pso_swarm_size)
    """
    
    def __init__(self, parent=None, default_config: Dict[str, Any] = None):
        """
        Khởi tạo Benchmark Config Dialog.
        
        Args:
            parent: Parent widget.
            default_config: Dictionary chứa config mặc định (optional).
                Nếu có, sẽ dùng để set giá trị mặc định cho các spinbox.
        """
        super().__init__(parent)
        
        self.setWindowTitle("⚙️ Cấu hình Benchmark")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setModal(True)
        
        # Giá trị mặc định
        if default_config:
            self.sa_iterations = default_config.get('max_iterations', 5000)
            self.pso_iterations = default_config.get('max_iterations', 500)
            self.pso_swarm_size = default_config.get('swarm_size', 50)
        else:
            self.sa_iterations = 5000
            self.pso_iterations = 500
            self.pso_swarm_size = 50
        
        self._init_ui()
    
    def _init_ui(self):
        """Khởi tạo giao diện."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = StrongBodyLabel("⚡ Cấu hình So sánh Hiệu năng")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = BodyLabel(
            "Nhập tham số cho từng thuật toán. "
            "Các giá trị này sẽ được dùng riêng cho benchmark và không ảnh hưởng đến cấu hình chính."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(desc_label)
        
        # ============================================================
        # SA Configuration Group
        # ============================================================
        sa_group = QGroupBox("🔥 Simulated Annealing (SA)")
        sa_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        sa_layout = QFormLayout(sa_group)
        sa_layout.setSpacing(15)
        sa_layout.setContentsMargins(15, 20, 15, 15)
        
        # SA Iterations
        self.sa_iter_spinbox = QSpinBox()
        self.sa_iter_spinbox.setMinimum(100)
        self.sa_iter_spinbox.setMaximum(100000)
        self.sa_iter_spinbox.setValue(self.sa_iterations)
        self.sa_iter_spinbox.setSingleStep(100)
        self.sa_iter_spinbox.setSuffix(" vòng lặp")
        self.sa_iter_spinbox.setToolTip("Số vòng lặp tối đa cho thuật toán SA")
        sa_layout.addRow("Số vòng lặp:", self.sa_iter_spinbox)
        
        layout.addWidget(sa_group)
        
        # ============================================================
        # PSO Configuration Group
        # ============================================================
        pso_group = QGroupBox("🐝 Particle Swarm Optimization (PSO)")
        pso_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        pso_layout = QFormLayout(pso_group)
        pso_layout.setSpacing(15)
        pso_layout.setContentsMargins(15, 20, 15, 15)
        
        # PSO Iterations
        self.pso_iter_spinbox = QSpinBox()
        self.pso_iter_spinbox.setMinimum(50)
        self.pso_iter_spinbox.setMaximum(100000)
        self.pso_iter_spinbox.setValue(self.pso_iterations)
        self.pso_iter_spinbox.setSingleStep(50)
        self.pso_iter_spinbox.setSuffix(" vòng lặp")
        self.pso_iter_spinbox.setToolTip("Số vòng lặp tối đa cho thuật toán PSO")
        pso_layout.addRow("Số vòng lặp:", self.pso_iter_spinbox)
        
        # PSO Swarm Size
        self.pso_swarm_spinbox = QSpinBox()
        self.pso_swarm_spinbox.setMinimum(10)
        self.pso_swarm_spinbox.setMaximum(200)
        self.pso_swarm_spinbox.setValue(self.pso_swarm_size)
        self.pso_swarm_spinbox.setSingleStep(10)
        self.pso_swarm_spinbox.setSuffix(" hạt")
        self.pso_swarm_spinbox.setToolTip("Số lượng hạt trong bầy đàn (swarm size)")
        pso_layout.addRow("Kích thước bầy đàn:", self.pso_swarm_spinbox)
        
        layout.addWidget(pso_group)
        
        # Spacer
        layout.addStretch()
        
        # ============================================================
        # Buttons
        # ============================================================
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = PushButton("❌ Hủy")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        # OK button
        ok_btn = PrimaryPushButton("✅ Bắt đầu Benchmark")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setMinimumWidth(150)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Lấy các giá trị cấu hình từ dialog.
        
        Returns:
            Dict chứa:
                - 'sa_iterations': int
                - 'pso_iterations': int
                - 'pso_swarm_size': int
        """
        return {
            'sa_iterations': self.sa_iter_spinbox.value(),
            'pso_iterations': self.pso_iter_spinbox.value(),
            'pso_swarm_size': self.pso_swarm_spinbox.value()
        }
    
    def set_default_values(self, sa_iterations: int = 5000, 
                          pso_iterations: int = 500, 
                          pso_swarm_size: int = 50):
        """
        Thiết lập giá trị mặc định cho các spinbox.
        
        Args:
            sa_iterations: Số vòng lặp mặc định cho SA.
            pso_iterations: Số vòng lặp mặc định cho PSO.
            pso_swarm_size: Swarm size mặc định cho PSO.
        """
        self.sa_iter_spinbox.setValue(sa_iterations)
        self.pso_iter_spinbox.setValue(pso_iterations)
        self.pso_swarm_spinbox.setValue(pso_swarm_size)



