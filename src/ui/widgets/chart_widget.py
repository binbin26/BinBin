"""
Widget hiển thị biểu đồ hội tụ của thuật toán Simulated Annealing.
Sử dụng PyQtGraph để vẽ real-time chart với hiệu năng cao.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import pyqtgraph as pg
from typing import List, Optional
import numpy as np


class ChartWidget(QWidget):
    """
    Widget vẽ biểu đồ hội tụ của thuật toán tối ưu.
    
    Features:
        - Real-time update với hiệu năng cao
        - Tự động scale trục khi có dữ liệu mới
        - Hiển thị grid để dễ đọc
        - Support theme light/dark
        - Có thể clear để chạy lại
    
    Attributes:
        plot_widget (PlotWidget): Widget chính để vẽ đồ thị
        curve (PlotDataItem): Đường đồ thị
        x_data (List[int]): Dữ liệu trục X (iterations)
        y_data (List[float]): Dữ liệu trục Y (costs)
    """
    
    def __init__(self, parent=None):
        """
        Khởi tạo Chart Widget.
        
        Args:
            parent: Parent widget (theo chuẩn Qt).
        """
        super().__init__(parent)
        
        # Data storage
        self.x_data: List[int] = []
        self.y_data: List[float] = []
        
        # Statistics
        self.best_cost = float('inf')
        self.initial_cost = None
        
        # Setup UI
        self._init_ui()
    
    def _init_ui(self):
        """
        Khởi tạo giao diện của widget.
        """
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Header với title và controls
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("📊 Biểu đồ Hội tụ (Convergence Chart)")
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Statistics labels
        self.stats_label = QLabel("Iteration: 0 | Current: N/A | Best: N/A")
        self.stats_label.setStyleSheet("color: #666; font-size: 10pt;")
        header_layout.addWidget(self.stats_label)
        
        # Clear button
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear)
        self.clear_btn.setMaximumWidth(80)
        self.clear_btn.setToolTip("Xóa dữ liệu và vẽ lại từ đầu")
        header_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # ============================================================
        # MAIN PLOT WIDGET (PyQtGraph)
        # ============================================================
        self.plot_widget = pg.PlotWidget()
        
        # Set background màu trắng
        self.plot_widget.setBackground('w')
        
        # Set labels cho trục
        self.plot_widget.setLabel('left', 'Cost (Điểm phạt)', color='black', size='11pt')
        self.plot_widget.setLabel('bottom', 'Iteration (Vòng lặp)', color='black', size='11pt')
        
        # Set title
        self.plot_widget.setTitle('Quá trình hội tụ của thuật toán', color='black', size='12pt')
        
        # Bật grid (lưới) với alpha mờ
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Customize grid style
        self.plot_widget.getAxis('left').setPen(pg.mkPen(color='k', width=1))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='k', width=1))
        self.plot_widget.getAxis('left').setTextPen('k')
        self.plot_widget.getAxis('bottom').setTextPen('k')
        
        # Enable auto-range (tự động scale trục) - FIX: Không truyền tham số
        self.plot_widget.enableAutoRange()
        
        # Add legend (chú thích)
        self.plot_widget.addLegend(offset=(10, 10))
        
        # ============================================================
        # CURVE (Đường đồ thị)
        # ============================================================
        # Tạo pen (bút vẽ) với màu xanh dương, độ dày 2
        pen = pg.mkPen(color=(0, 100, 255), width=2)
        
        # Tạo curve (PlotDataItem) - đây là đường đồ thị chính
        self.curve = self.plot_widget.plot(
            [], [],  # Dữ liệu ban đầu rỗng
            pen=pen,
            name='Cost',
            symbol='o',         # Hiển thị điểm dạng hình tròn
            symbolSize=4,       # Kích thước điểm nhỏ
            symbolBrush=(0, 100, 255),  # Màu điểm
            symbolPen=None      # Không vẽ viền điểm
        )
        
        main_layout.addWidget(self.plot_widget)
        
        # Footer với improvement info
        self.improvement_label = QLabel("💡 Chờ dữ liệu từ thuật toán...")
        self.improvement_label.setStyleSheet("color: #999; font-size: 9pt; font-style: italic;")
        main_layout.addWidget(self.improvement_label)
        
        self.setLayout(main_layout)
    
    def update_plot(self, iteration: int, cost: float):
        """
        Cập nhật điểm mới vào biểu đồ (real-time).
        
        Performance optimization:
            - Sử dụng setData() thay vì clear + plot
            - Append vào list thay vì tạo mới
            - PyQtGraph tự động optimize rendering
        
        Args:
            iteration (int): Số vòng lặp hiện tại (trục X).
            cost (float): Giá trị cost/fitness (trục Y).
        """
        # Validate cost value (tránh inf hoặc NaN)
        if not isinstance(cost, (int, float)) or cost == float('inf') or cost != cost:  # NaN check
            return  # Bỏ qua giá trị không hợp lệ
        
        # Append new data point
        self.x_data.append(iteration)
        self.y_data.append(cost)
        
        # Update curve efficiently (không vẽ lại toàn bộ)
        # setData chỉ update phần dữ liệu mới, không redraw everything
        self.curve.setData(self.x_data, self.y_data)
        
        # Update statistics
        # Set initial_cost khi nhận được điểm đầu tiên
        if self.initial_cost is None:
            self.initial_cost = cost
        
        # Update best_cost
        if cost < self.best_cost:
            self.best_cost = cost
        
        # Update labels
        self._update_statistics(iteration, cost)
    
    def _update_statistics(self, iteration: int, current_cost: float):
        """
        Cập nhật các label thống kê.
        
        Args:
            iteration: Vòng lặp hiện tại.
            current_cost: Cost hiện tại.
        """
        # Validate values
        if self.best_cost == float('inf'):
            best_display = "N/A"
        else:
            best_display = f"{self.best_cost:.2f}"
        
        # Update main stats label
        self.stats_label.setText(
            f"Iteration: {iteration} | "
            f"Current: {current_cost:.2f} | "
            f"Best: {best_display}"
        )
        
        # Update improvement label
        # Kiểm tra điều kiện: initial_cost phải hợp lệ và > 0
        if self.initial_cost is not None and self.initial_cost != float('inf') and self.initial_cost > 0:
            # Tính toán improvement
            if self.best_cost != float('inf') and self.best_cost < self.initial_cost:
                improvement = ((self.initial_cost - self.best_cost) / self.initial_cost) * 100
                
                if improvement > 0:
                    self.improvement_label.setText(
                        f"✅ Cải thiện: {improvement:.2f}% "
                        f"(từ {self.initial_cost:.2f} xuống {self.best_cost:.2f})"
                    )
                    self.improvement_label.setStyleSheet("color: green; font-size: 9pt;")
                else:
                    self.improvement_label.setText(
                        f"⏳ Đang tìm kiếm solution tốt hơn..."
                    )
                    self.improvement_label.setStyleSheet("color: orange; font-size: 9pt;")
            elif self.best_cost == float('inf'):
                # Chưa có best cost
                self.improvement_label.setText(
                    f"💡 Đang khởi tạo... (Initial: {self.initial_cost:.2f})"
                )
                self.improvement_label.setStyleSheet("color: #999; font-size: 9pt; font-style: italic;")
            else:
                # best_cost >= initial_cost (chưa cải thiện)
                self.improvement_label.setText(
                    f"⏳ Đang tìm kiếm solution tốt hơn... (Initial: {self.initial_cost:.2f})"
                )
                self.improvement_label.setStyleSheet("color: orange; font-size: 9pt;")
        else:
            # Chưa có initial_cost hợp lệ
            if self.initial_cost is None:
                self.improvement_label.setText("💡 Chờ dữ liệu từ thuật toán...")
            else:
                self.improvement_label.setText(f"💡 Đang xử lý dữ liệu... (Current: {current_cost:.2f})")
            self.improvement_label.setStyleSheet("color: #999; font-size: 9pt; font-style: italic;")
    
    def update_batch(self, iterations: List[int], costs: List[float]):
        """
        Cập nhật nhiều điểm cùng lúc (batch update).
        Hiệu quả hơn khi có nhiều dữ liệu cần vẽ cùng lúc.
        
        Args:
            iterations: Danh sách các iteration.
            costs: Danh sách các cost tương ứng.
        """
        # Filter out invalid values
        valid_data = [(i, c) for i, c in zip(iterations, costs) 
                     if isinstance(c, (int, float)) and c != float('inf') and c == c]
        
        if not valid_data:
            return
        
        valid_iterations, valid_costs = zip(*valid_data)
        
        # Extend data
        self.x_data.extend(valid_iterations)
        self.y_data.extend(valid_costs)
        
        # Update curve once (efficient)
        self.curve.setData(self.x_data, self.y_data)
        
        # Update statistics với điểm cuối
        if valid_iterations and valid_costs:
            # Set initial_cost từ điểm đầu tiên (iteration nhỏ nhất trong batch)
            min_iter_in_batch = min(valid_iterations)
            min_iter_idx = valid_iterations.index(min_iter_in_batch)
            first_cost = valid_costs[min_iter_idx]
            
            # Set initial_cost nếu chưa có hoặc nếu batch này có iteration nhỏ hơn
            if self.initial_cost is None:
                self.initial_cost = first_cost
            elif self.x_data:  # Nếu đã có dữ liệu trước đó
                min_existing_iter = min(self.x_data[:-len(valid_iterations)]) if len(self.x_data) > len(valid_iterations) else min(self.x_data)
                if min_iter_in_batch < min_existing_iter:
                    # Nếu có điểm mới có iteration nhỏ hơn, cập nhật initial_cost
                    self.initial_cost = first_cost
            else:
                # Nếu chưa có dữ liệu, set initial_cost
                self.initial_cost = first_cost
            
            # Update best_cost
            self.best_cost = min(min(valid_costs), self.best_cost)
            self._update_statistics(valid_iterations[-1], valid_costs[-1])
    
    def set_data(self, iterations: List[int], costs: List[float]):
        """
        Set toàn bộ dữ liệu cùng lúc (khi đã có full history).
        
        Args:
            iterations: Danh sách iterations.
            costs: Danh sách costs.
        """
        self.clear()
        self.update_batch(iterations, costs)
    
    def update_final(self, final_iteration: int, final_cost: float, convergence_history: Optional[List[float]] = None):
        """
        Cập nhật dữ liệu cuối cùng khi thuật toán kết thúc.
        Đảm bảo biểu đồ hiển thị đầy đủ dữ liệu và cập nhật improvement label.
        
        Args:
            final_iteration: Số iteration cuối cùng.
            final_cost: Cost cuối cùng (best cost).
            convergence_history: Lịch sử hội tụ đầy đủ (optional).
        """
        # Nếu có convergence_history, cập nhật toàn bộ dữ liệu
        if convergence_history and len(convergence_history) > 0:
            # Tạo danh sách iterations từ 0 đến len(convergence_history) - 1
            iterations = list(range(len(convergence_history)))
            self.set_data(iterations, convergence_history)
        else:
            # Nếu không có history, chỉ cập nhật điểm cuối cùng
            if final_iteration not in self.x_data:
                # Thêm điểm cuối cùng nếu chưa có
                self.update_plot(final_iteration, final_cost)
            else:
                # Nếu đã có, chỉ cập nhật statistics
                if final_cost < self.best_cost:
                    self.best_cost = final_cost
                self._update_statistics(final_iteration, final_cost)
        
        # Đảm bảo best_cost được cập nhật
        if final_cost < self.best_cost:
            self.best_cost = final_cost
        
        # Force update statistics với giá trị cuối cùng
        self._update_statistics(final_iteration, final_cost)
    
    def clear(self):
        """
        Xóa toàn bộ dữ liệu để vẽ lại từ đầu.
        """
        # Clear data
        self.x_data.clear()
        self.y_data.clear()
        
        # Clear plot widget (xóa tất cả curves)
        self.plot_widget.clear()
        
        # Re-add legend
        self.plot_widget.addLegend(offset=(10, 10))
        
        # Reset title
        self.plot_widget.setTitle('Quá trình hội tụ của thuật toán', color='black', size='12pt')
        
        # Recreate main curve
        pen = pg.mkPen(color=(0, 100, 255), width=2)
        self.curve = self.plot_widget.plot(
            [], [],
            pen=pen,
            name='Cost',
            symbol='o',
            symbolSize=4,
            symbolBrush=(0, 100, 255),
            symbolPen=None
        )
        
        # Reset statistics
        self.best_cost = float('inf')
        self.initial_cost = None
        
        # Reset labels
        self.stats_label.setText("Iteration: 0 | Current: N/A | Best: N/A")
        self.improvement_label.setText("💡 Chờ dữ liệu từ thuật toán...")
        self.improvement_label.setStyleSheet("color: #999; font-size: 9pt; font-style: italic;")
        
        # Clear comparison curves if exist
        if hasattr(self, 'sa_curve'):
            delattr(self, 'sa_curve')
        if hasattr(self, 'pso_curve'):
            delattr(self, 'pso_curve')
    
    def get_data(self):
        """
        Lấy dữ liệu hiện tại.
        
        Returns:
            Tuple[List[int], List[float]]: (iterations, costs)
        """
        return self.x_data.copy(), self.y_data.copy()
    
    def export_image(self, filepath: str):
        """
        Xuất biểu đồ ra file ảnh.
        
        Args:
            filepath: Đường dẫn file (*.png, *.jpg).
        """
        exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
        exporter.export(filepath)
    
    def plot_comparison(self, sa_history: List[float], pso_history: List[float]):
        """
        Vẽ biểu đồ so sánh giữa SA và PSO.
        
        Args:
            sa_history: Lịch sử hội tụ của Simulated Annealing (list of costs).
            pso_history: Lịch sử hội tụ của Particle Swarm Optimization (list of costs).
        """
        # Clear existing data
        self.clear()
        
        # Clear existing curves
        self.plot_widget.clear()
        
        # Update title
        self.plot_widget.setTitle('So sánh hiệu năng: SA vs PSO', color='black', size='12pt')
        
        # Tạo dữ liệu cho SA (màu đỏ)
        sa_iterations = list(range(len(sa_history)))
        sa_pen = pg.mkPen(color=(255, 0, 0), width=2)  # Màu đỏ
        sa_curve = self.plot_widget.plot(
            sa_iterations,
            sa_history,
            pen=sa_pen,
            name='Simulated Annealing (SA)',
            symbol='o',
            symbolSize=3,
            symbolBrush=(255, 0, 0),
            symbolPen=None
        )
        
        # Tạo dữ liệu cho PSO (màu xanh dương)
        pso_iterations = list(range(len(pso_history)))
        pso_pen = pg.mkPen(color=(0, 100, 255), width=2)  # Màu xanh dương
        pso_curve = self.plot_widget.plot(
            pso_iterations,
            pso_history,
            pen=pso_pen,
            name='Particle Swarm Optimization (PSO)',
            symbol='s',  # Hình vuông để phân biệt
            symbolSize=3,
            symbolBrush=(0, 100, 255),
            symbolPen=None
        )
        
        # Lưu curves để có thể xóa sau
        self.sa_curve = sa_curve
        self.pso_curve = pso_curve
        
        # Cập nhật statistics
        if sa_history:
            sa_initial = sa_history[0]
            sa_best = min(sa_history)
            sa_improvement = ((sa_initial - sa_best) / sa_initial * 100) if sa_initial > 0 else 0
        else:
            sa_initial = 0
            sa_best = 0
            sa_improvement = 0
        
        if pso_history:
            pso_initial = pso_history[0]
            pso_best = min(pso_history)
            pso_improvement = ((pso_initial - pso_best) / pso_initial * 100) if pso_initial > 0 else 0
        else:
            pso_initial = 0
            pso_best = 0
            pso_improvement = 0
        
        # Cập nhật stats label
        self.stats_label.setText(
            f"SA: Best={sa_best:.2f} ({sa_improvement:.1f}%) | "
            f"PSO: Best={pso_best:.2f} ({pso_improvement:.1f}%)"
        )
        
        # Cập nhật improvement label
        if sa_best < pso_best:
            winner = "SA"
            diff = pso_best - sa_best
            diff_pct = (diff / pso_best * 100) if pso_best > 0 else 0
            self.improvement_label.setText(
                f"🏆 SA tốt hơn PSO: {diff:.2f} ({diff_pct:.1f}%) | "
                f"SA: {sa_improvement:.1f}% | PSO: {pso_improvement:.1f}%"
            )
            self.improvement_label.setStyleSheet("color: red; font-size: 9pt; font-weight: bold;")
        elif pso_best < sa_best:
            winner = "PSO"
            diff = sa_best - pso_best
            diff_pct = (diff / sa_best * 100) if sa_best > 0 else 0
            self.improvement_label.setText(
                f"🏆 PSO tốt hơn SA: {diff:.2f} ({diff_pct:.1f}%) | "
                f"SA: {sa_improvement:.1f}% | PSO: {pso_improvement:.1f}%"
            )
            self.improvement_label.setStyleSheet("color: blue; font-size: 9pt; font-weight: bold;")
        else:
            self.improvement_label.setText(
                f"⚖️ Hòa nhau! | SA: {sa_improvement:.1f}% | PSO: {pso_improvement:.1f}%"
            )
            self.improvement_label.setStyleSheet("color: green; font-size: 9pt; font-weight: bold;")
        
        # Auto-range để hiển thị đầy đủ
        self.plot_widget.enableAutoRange()
    
    def set_theme(self, theme: str = 'light'):
        """
        Đổi theme của biểu đồ.
        
        Args:
            theme: 'light' hoặc 'dark'.
        """
        if theme == 'dark':
            # Dark theme
            self.plot_widget.setBackground('k')
            self.plot_widget.getAxis('left').setPen('w')
            self.plot_widget.getAxis('bottom').setPen('w')
            self.plot_widget.getAxis('left').setTextPen('w')
            self.plot_widget.getAxis('bottom').setTextPen('w')
            
            # Update curve color
            pen = pg.mkPen(color=(100, 200, 255), width=2)
            self.curve.setPen(pen)
            self.curve.setSymbolBrush((100, 200, 255))
        else:
            # Light theme (default)
            self.plot_widget.setBackground('w')
            self.plot_widget.getAxis('left').setPen('k')
            self.plot_widget.getAxis('bottom').setPen('k')
            self.plot_widget.getAxis('left').setTextPen('k')
            self.plot_widget.getAxis('bottom').setTextPen('k')
            
            # Update curve color
            pen = pg.mkPen(color=(0, 100, 255), width=2)
            self.curve.setPen(pen)
            self.curve.setSymbolBrush((0, 100, 255))

