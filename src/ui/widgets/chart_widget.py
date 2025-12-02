"""
Widget hiển thị Gantt Chart để biểu diễn các thông số thuật toán trong quá trình chạy.
Hiển thị: Iteration, Temperature/Inertia, Cost, Acceptance Rate, Updates, etc.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QBrush
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from typing import List, Optional, Dict, Any
import numpy as np
import matplotlib
import warnings
import os

# Cấu hình Matplotlib để hỗ trợ tiếng Việt - dùng font hỗ trợ Unicode
try:
    # Thử các font có hỗ trợ tiếng Việt
    font_list = [
        'DejaVu Sans',  # Fallback
        'Times New Roman',
        'Arial',
        'Liberation Sans',
        'Courier New'
    ]
    
    # Trên Windows, kiểm tra Vietnamese font
    if os.name == 'nt':  # Windows
        font_list.insert(0, 'Segoe UI')
        font_list.insert(0, 'Calibri')
    
    matplotlib.rcParams['font.sans-serif'] = font_list
    matplotlib.rcParams['axes.unicode_minus'] = False
    matplotlib.rcParams['font.size'] = 10
except Exception as e:
    pass

# Tắt warning về missing glyph
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')


class ChartWidget(QWidget):
    """
    Widget biểu diễn Gantt Chart và bảng thông số của thuật toán.
    
    Features:
        - Hiển thị biểu đồ Gantt theo iteration
        - Bảng chi tiết các thông số thuật toán
        - Real-time update các giá trị
        - Thống kê hiệu năng
        - Support theme light/dark
    
    Attributes:
        canvas: Matplotlib canvas cho Gantt Chart
        data_table: Bảng hiển thị chi tiết
        algorithm_stats: Từ điển lưu thông số thuật toán
    """
    
    def __init__(self, parent=None):
        """
        Khởi tạo Chart Widget.
        
        Args:
            parent: Parent widget (theo chuẩn Qt).
        """
        super().__init__(parent)
        
        # Data storage
        self.iterations: List[int] = []
        self.costs: List[float] = []
        self.temperatures: List[float] = []  # Cho SA
        self.inertias: List[float] = []  # Cho PSO
        self.acceptance_rates: List[float] = []
        self.updates: List[int] = []
        
        # Algorithm info
        self.algorithm_name = "SA"
        self.algorithm_stats: Dict[str, Any] = {}
        
        # Statistics
        self.best_cost = float('inf')
        self.initial_cost = None
        self.current_iteration = 0
        
        # Setup UI
        self._init_ui()
    
    def _init_ui(self):
        """Khởi tạo giao diện của widget (Responsive)."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ========== HEADER ==========
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # Title (Responsive font size)
        title_label = QLabel("📊 Gantt Chart - Thông Số Thuật Toán")
        title_font = title_label.font()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Statistics label
        self.stats_label = QLabel("Waiting for data...")
        self.stats_label.setStyleSheet("color: #666; font-size: 10pt;")
        header_layout.addWidget(self.stats_label)
        
        # Clear button
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear)
        self.clear_btn.setMaximumWidth(80)
        header_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # ========== TAB WIDGET ==========
        self.tab_widget = QTabWidget()
        
        # Tab 1: Gantt Chart
        self.gantt_widget = QWidget()
        gantt_layout = QVBoxLayout(self.gantt_widget)
        
        # Matplotlib figure cho Gantt Chart (Responsive size)
        self.fig = Figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumHeight(400)
        gantt_layout.addWidget(self.canvas)
        
        self.tab_widget.addTab(self.gantt_widget, "[Chart] Gantt Chart")
        
        # Tab 2: Bảng Chi Tiết
        self.table_widget = QWidget()
        table_layout = QVBoxLayout(self.table_widget)
        
        # Tạo bảng
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(8)
        self.data_table.setHorizontalHeaderLabels([
            "Iteration", "Cost", "Improvement %", 
            "Temp/Inertia", "Acceptance Rate", "Updates", "Time (s)", "Status"
        ])
        
        # Set column widths
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setStyleSheet("""
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
            }
        """)
        
        table_layout.addWidget(self.data_table)
        self.tab_widget.addTab(self.table_widget, "[Detail] Details")
        
        main_layout.addWidget(self.tab_widget)
        
        # ========== IMPROVEMENT LABEL ==========
        self.improvement_label = QLabel("[INFO] Waiting for algorithm...")
        self.improvement_label.setStyleSheet("color: #999; font-size: 10pt; font-style: italic;")
        main_layout.addWidget(self.improvement_label)
        
        self.setLayout(main_layout)
    
    def update_plot(self, iteration: int, cost: float, 
                   temperature: float = 0.0, 
                   inertia: float = 0.0,
                   acceptance_rate: float = 0.0,
                   updates: int = 0):
        """
        Cập nhật biểu đồ và bảng với dữ liệu mới.
        
        Args:
            iteration: Vòng lặp hiện tại
            cost: Cost/fitness hiện tại
            temperature: Temperature (SA) - default 0.0
            inertia: Inertia weight (PSO) - default 0.0
            acceptance_rate: Tỷ lệ chấp nhận
            updates: Số lần cập nhật
        """
        # Validate cost
        if not isinstance(cost, (int, float)) or cost == float('inf') or cost != cost:
            return
        
        # Append data
        self.iterations.append(iteration)
        self.costs.append(cost)
        
        if temperature > 0:
            self.temperatures.append(temperature)
            self.algorithm_name = "SA"
        
        if inertia > 0:
            self.inertias.append(inertia)
            self.algorithm_name = "PSO"
        
        if acceptance_rate > 0:
            self.acceptance_rates.append(acceptance_rate)
        
        if updates > 0:
            self.updates.append(updates)
        
        # Update statistics
        if self.initial_cost is None:
            self.initial_cost = cost
        
        if cost < self.best_cost:
            self.best_cost = cost
        
        self.current_iteration = iteration
        
        # Update labels
        self._update_statistics()
        
        # Cập nhật biểu đồ (mỗi 10 iterations để không quá nhanh)
        if iteration % 10 == 0 or iteration == 1:
            self._redraw_gantt_chart()
        
        # Cập nhật bảng với dòng mới
        self._add_table_row(iteration, cost, temperature if temperature > 0 else None, 
                           inertia if inertia > 0 else None, 
                           acceptance_rate if acceptance_rate > 0 else None, 
                           updates if updates > 0 else None, None)
    
    def _redraw_gantt_chart(self):
        """Vẽ lại Gantt Chart với dữ liệu hiện tại."""
        self.fig.clear()
        
        if not self.iterations:
            return
        
        # Tạo subplots
        ax1 = self.fig.add_subplot(2, 2, 1)
        ax2 = self.fig.add_subplot(2, 2, 2)
        ax3 = self.fig.add_subplot(2, 2, 3)
        ax4 = self.fig.add_subplot(2, 2, 4)
        
        # ========== SUBPLOT 1: Cost Trend ==========
        ax1.plot(self.iterations, self.costs, color='#0066FF', linewidth=2, marker='o', markersize=3)
        ax1.set_xlabel('Iteration', fontsize=10, fontweight='bold')
        ax1.set_ylabel('Cost', fontsize=10, fontweight='bold')
        ax1.set_title('[Cost Trend] Trend over iterations', fontsize=11, fontweight='bold', color='#0066FF')
        ax1.grid(True, alpha=0.3)
        ax1.set_facecolor('#F5F5F5')
        
        # ========== SUBPLOT 2: Temperature/Inertia ==========
        if self.temperatures:
            ax2.plot(self.iterations[-len(self.temperatures):], self.temperatures, 
                    color='#FF6600', linewidth=2, marker='s', markersize=3)
            ax2.set_title('[Temperature] SA Temperature', fontsize=11, fontweight='bold', color='#FF6600')
        elif self.inertias:
            ax2.plot(self.iterations[-len(self.inertias):], self.inertias,
                    color='#00CC00', linewidth=2, marker='^', markersize=3)
            ax2.set_title('[Inertia] PSO Inertia Weight', fontsize=11, fontweight='bold', color='#00CC00')
        
        ax2.set_xlabel('Iteration', fontsize=10, fontweight='bold')
        ax2.set_ylabel('Value', fontsize=10, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.set_facecolor('#F5F5F5')
        
        # ========== SUBPLOT 3: Acceptance Rate ==========
        if self.acceptance_rates:
            ax3.plot(self.iterations[-len(self.acceptance_rates):], self.acceptance_rates,
                    color='#FF00FF', linewidth=2, marker='d', markersize=3)
            ax3.set_ylim([0, 100])
            ax3.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='50%')
            ax3.legend()
        else:
            ax3.text(0.5, 0.5, 'No data', ha='center', va='center',
                    transform=ax3.transAxes, fontsize=10, color='#999')
        
        ax3.set_xlabel('Iteration', fontsize=10, fontweight='bold')
        ax3.set_ylabel('Rate (%)', fontsize=10, fontweight='bold')
        ax3.set_title('[Acceptance Rate] Acceptance rate over iterations (%)', fontsize=11, fontweight='bold', color='#FF00FF')
        ax3.grid(True, alpha=0.3)
        ax3.set_facecolor('#F5F5F5')
        
        # ========== SUBPLOT 4: Updates ==========
        if self.updates:
            colors = ['#00AA00' if u > 0 else '#CCCCCC' for u in self.updates]
            ax4.bar(self.iterations[-len(self.updates):], self.updates, color=colors, alpha=0.7)
        else:
            ax4.text(0.5, 0.5, 'Không có dữ liệu', ha='center', va='center',
                    transform=ax4.transAxes, fontsize=10, color='#999')
        
        ax4.set_xlabel('Iteration', fontsize=10, fontweight='bold')
        ax4.set_ylabel('Updates Count', fontsize=10, fontweight='bold')
        ax4.set_title('[Updates] Number of updates', fontsize=11, fontweight='bold', color='#66CC00')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.set_facecolor('#F5F5F5')
        
        # Layout
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _add_table_row(self, iteration: int, cost: float, 
                      temperature: Optional[float] = None,
                      inertia: Optional[float] = None,
                      acceptance_rate: Optional[float] = None,
                      updates: Optional[int] = None,
                      elapsed_time: Optional[float] = None):
        """Thêm dòng mới vào bảng (mỗi 10 iterations)."""
        if iteration % 10 != 0 and iteration != 1:
            return
        
        row_position = self.data_table.rowCount()
        self.data_table.insertRow(row_position)
        
        # Calculate improvement
        if self.initial_cost and self.initial_cost > 0:
            improvement = ((self.initial_cost - cost) / self.initial_cost) * 100
        else:
            improvement = 0
        
        # Prepare row data
        row_data = [
            str(iteration),
            f"{cost:.2f}",
            f"{improvement:.2f}%",
            f"{temperature:.2f}" if temperature else (f"{inertia:.2f}" if inertia else "N/A"),
            f"{acceptance_rate:.1f}%" if acceptance_rate else "N/A",
            str(updates) if updates else "N/A",
            f"{elapsed_time:.2f}s" if elapsed_time else "N/A",
            "[OK] Tốt" if improvement > 0 else "[CHỜ] Chờ đợi"
        ]
        
        # Add items
        for col, data in enumerate(row_data):
            item = QTableWidgetItem(data)
            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            
            # Color coding
            if col == 1:  # Cost
                if cost < self.best_cost * 1.1:  # Gần với best
                    item.setBackground(QBrush(QColor("#C8E6C9")))  # Xanh nhạt
                else:
                    item.setBackground(QBrush(QColor("#FFE0B2")))  # Cam nhạt
            
            elif col == 2:  # Improvement
                if improvement > 10:
                    item.setBackground(QBrush(QColor("#A5D6A7")))  # Xanh đậm
                elif improvement > 0:
                    item.setBackground(QBrush(QColor("#C8E6C9")))  # Xanh nhạt
                else:
                    item.setBackground(QBrush(QColor("#FFCCBC")))  # Cam đậm
            
            elif col == 7:  # Status
                if improvement > 0:
                    item.setForeground(QColor("#00AA00"))  # Xanh
                else:
                    item.setForeground(QColor("#FF9800"))  # Cam
            
            self.data_table.setItem(row_position, col, item)
        
        # Scroll to bottom
        self.data_table.scrollToBottom()
    
    def _update_statistics(self):
        """Cập nhật label thống kê."""
        if self.best_cost == float('inf'):
            best_display = "N/A"
        else:
            best_display = f"{self.best_cost:.2f}"
        
        if self.initial_cost is None:
            improvement_display = "N/A"
        elif self.initial_cost > 0:
            improvement = ((self.initial_cost - self.best_cost) / self.initial_cost) * 100
            improvement_display = f"{improvement:.2f}%"
        else:
            improvement_display = "N/A"
        
        # Update stats label
        self.stats_label.setText(
            f"Iteration: {self.current_iteration} | "
            f"Current: {(self.costs[-1] if self.costs else 'N/A')} | "
            f"Best: {best_display} | "
            f"Improvement: {improvement_display}"
        )
        
        # Update improvement label
        if self.initial_cost and self.best_cost < float('inf'):
            improvement = ((self.initial_cost - self.best_cost) / self.initial_cost) * 100
            if improvement > 0:
                self.improvement_label.setText(
                    f"[IMPROVED] Improvement: {improvement:.2f}% "
                    f"({self.initial_cost:.2f} -> {self.best_cost:.2f})"
                )
                self.improvement_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.improvement_label.setText(
                    f"[SEARCHING] Finding better solution... "
                    f"(Best: {self.best_cost:.2f})"
                )
                self.improvement_label.setStyleSheet("color: orange;")
        else:
            self.improvement_label.setText("[LOADING] Processing data...")
            self.improvement_label.setStyleSheet("color: #999;")
    
    def update_batch(self, data: List[Dict[str, Any]]):
        """
        Cập nhật nhiều điểm cùng lúc.
        
        Args:
            data: Danh sách dict chứa {iteration, cost, temperature, inertia, ...}
        """
        for point in data:
            # Extract values with defaults
            iteration = point.get('iteration', 0)
            cost = point.get('cost', float('inf'))
            temperature = point.get('temperature', 0.0)
            inertia = point.get('inertia', 0.0)
            acceptance_rate = point.get('acceptance_rate', 0.0)
            updates = point.get('updates', 0)
            
            # Call update_plot with positional args
            self.update_plot(iteration, cost, temperature, inertia, acceptance_rate, updates)
    
    def update_final(self, final_iteration: int, final_cost: float, 
                    convergence_history: Optional[List[float]] = None,
                    algorithm_stats: Optional[Dict[str, Any]] = None):
        """
        Cập nhật khi thuật toán kết thúc.
        
        Args:
            final_iteration: Iteration cuối cùng
            final_cost: Cost cuối cùng
            convergence_history: Lịch sử hội tụ (tùy chọn)
            algorithm_stats: Thống kê thuật toán
        """
        if final_cost < self.best_cost:
            self.best_cost = final_cost
        
        if algorithm_stats:
            self.algorithm_stats = algorithm_stats
        
        self._update_statistics()
        self._redraw_gantt_chart()
    
    def clear(self):
        """Xóa tất cả dữ liệu."""
        self.iterations.clear()
        self.costs.clear()
        self.temperatures.clear()
        self.inertias.clear()
        self.acceptance_rates.clear()
        self.updates.clear()
        
        self.best_cost = float('inf')
        self.initial_cost = None
        self.current_iteration = 0
        
        # Clear table
        self.data_table.setRowCount(0)
        
        # Clear chart
        self.fig.clear()
        self.canvas.draw()
        
        # Reset labels
        self.stats_label.setText("Chờ dữ liệu...")
        self.improvement_label.setText("[INFO] Chờ dữ liệu từ thuật toán...")
        self.improvement_label.setStyleSheet("color: #999;")
    
    def get_data(self):
        """Lấy dữ liệu hiện tại."""
        return {
            'iterations': self.iterations.copy(),
            'costs': self.costs.copy(),
            'temperatures': self.temperatures.copy(),
            'inertias': self.inertias.copy(),
            'acceptance_rates': self.acceptance_rates.copy(),
            'updates': self.updates.copy()
        }
    
    def export_image(self, filepath: str):
        """Xuất biểu đồ ra file ảnh."""
        self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
    
    def plot_comparison(self, sa_history: List[float], pso_history: List[float]):
        """
        Vẽ biểu đồ so sánh SA vs PSO.
        
        Args:
            sa_history: Lịch sử chi phí của SA
            pso_history: Lịch sử chi phí của PSO
        """
        self.fig.clear()
        
        ax = self.fig.add_subplot(1, 1, 1)
        
        # SA curve
        sa_x = list(range(1, len(sa_history) + 1))
        ax.plot(sa_x, sa_history, color='#FF6600', linewidth=2, marker='o', 
               markersize=3, label='SA Algorithm')
        
        # PSO curve
        pso_x = list(range(1, len(pso_history) + 1))
        ax.plot(pso_x, pso_history, color='#0099FF', linewidth=2, marker='s',
               markersize=3, label='PSO Algorithm')
        
        ax.set_xlabel('Iteration', fontsize=11, fontweight='bold')
        ax.set_ylabel('Cost', fontsize=11, fontweight='bold')
        ax.set_title('Comparison: SA vs PSO', fontsize=12, fontweight='bold', color='#0066FF')
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#F5F5F5')
        ax.legend(loc='upper right')
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def set_data(self, iterations: List[int], costs: List[float]):
        """
        Thiết lập dữ liệu cho biểu đồ (thay thế toàn bộ).
        
        Args:
            iterations: Danh sách iterations
            costs: Danh sách costs
        """
        self.clear()
        for iteration, cost in zip(iterations, costs):
            self.update_plot(iteration, cost)
    
    def set_theme(self, theme: str = 'light'):
        """
        Đặt theme cho biểu đồ.
        
        Args:
            theme: 'light' hoặc 'dark'
        """
        if theme == 'dark':
            self.fig.patch.set_facecolor('#1e1e1e')
        else:
            self.fig.patch.set_facecolor('#ffffff')
