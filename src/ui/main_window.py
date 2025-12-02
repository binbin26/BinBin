"""
File: src/ui/main_window.py
Cửa sổ chính của ứng dụng Xếp lịch thi AI.
Cập nhật: Tích hợp DataLoader để đọc file Excel/CSV.
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QApplication, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QDialog, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

# Import Fluent Widgets
from qfluentwidgets import (
    FluentWindow, 
    NavigationItemPosition, 
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
    SplashScreen,
    PrimaryPushButton
)

# Thêm đường dẫn root
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Import các components của dự án
from src.models.course import Course
from src.models.room import Room
from src.models.proctor import Proctor
from src.models.solution import Schedule
from src.core.solvers.sa_solver import SASolver
from src.core.solvers.pso_solver import PSOSolver
from src.utils.data_loader import DataLoader  # <--- MỚI: Import DataLoader
from src.utils.exporter import Exporter

# Import Widgets
from src.ui.widgets.config_widget import ConfigWidget
from src.ui.widgets.chart_widget import ChartWidget
from src.ui.widgets.schedule_table import ScheduleResultTable
from src.ui.widgets.data_viewer import DataViewerWidget


class DashboardInterface(QWidget):
    """
    Giao diện Tab Dashboard: Chứa Config và Chart (Responsive).
    """
    def __init__(self, config_widget, chart_widget, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardInterface")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Bên trái: Config (chiếm 35%, responsive)
        layout.addWidget(config_widget, 35)
        
        # Bên phải: Biểu đồ (chiếm 65%, responsive)
        layout.addWidget(chart_widget, 65)


class MainWindow(FluentWindow):
    """
    Cửa sổ chính ứng dụng.
    """
    def __init__(self):
        super().__init__()
        
        # 1. Cấu hình cửa sổ cơ bản (Responsive)
        self.setWindowTitle("AI Exam Scheduling System")
        # Lấy kích thước màn hình để set default size (80% màn hình)
        desktop = QApplication.desktop().availableGeometry()
        default_width = int(desktop.width() * 0.8)
        default_height = int(desktop.height() * 0.85)
        self.resize(default_width, default_height)
        self.setMinimumSize(1024, 640)  # Minimum size để không bị lỗi layout
        self._center_window()

        # Dữ liệu chính
        self.courses = []
        self.rooms = []
        self.rooms_dict = {}
        self.proctors = []
        self.proctors_dict = {}

        # 2. Khởi tạo các Widget con
        self.config_widget = ConfigWidget()
        self.chart_widget = ChartWidget()
        self.result_table = ScheduleResultTable()
        self.data_viewer = DataViewerWidget()  # <--- NEW: Data Viewer Widget
        
        # 3. Tạo các Interface (Trang con)
        self.dashboard_interface = DashboardInterface(
            self.config_widget, 
            self.chart_widget
        )
        
        # --- CẤU HÌNH TRANG KẾT QUẢ (CÓ SỬA ĐỔI) ---
        self.result_interface = QWidget()
        self.result_interface.setObjectName("ResultInterface")
        result_layout = QVBoxLayout(self.result_interface)
        result_layout.setContentsMargins(20, 20, 20, 20)
        
        # > Thêm thanh công cụ (Toolbar) chứa nút Xuất Excel và Benchmark
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addStretch()  # Đẩy nút sang phải
        
        self.benchmark_btn = PrimaryPushButton(FIF.SPEED_HIGH, "⚡ Chạy So Sánh (Benchmark)")
        self.benchmark_btn.setToolTip("So sánh hiệu năng giữa SA và PSO trên cùng bộ dữ liệu")
        self.benchmark_btn.clicked.connect(self.run_benchmark)
        toolbar_layout.addWidget(self.benchmark_btn)
        
        self.export_btn = PrimaryPushButton(FIF.SAVE, "Xuất ra Excel")
        self.export_btn.setToolTip("Lưu kết quả xếp lịch ra file Excel")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)  # Mặc định ẩn, chỉ hiện khi có kết quả
        toolbar_layout.addWidget(self.export_btn)
        
        result_layout.addLayout(toolbar_layout)
        # > Thêm bảng kết quả
        result_layout.addWidget(self.result_table)
        # ---------------------------------------------

        self.setting_interface = QWidget()
        self.setting_interface.setObjectName("SettingInterface")

        # 4. Khởi tạo Navigation
        self._init_navigation()
        
        # 5. Kết nối sự kiện
        self._connect_signals()
        
        # Biến lưu solver
        self.solver = None
        
        # Biến cho benchmark
        self.benchmark_running = False
        self.benchmark_sa_result = None
        self.benchmark_pso_result = None
        self._temp_pso_config = None  # Lưu tạm PSO config để truyền qua callback
        self._benchmark_sa_config = None  # Lưu SA config đã dùng
        self._benchmark_pso_config = None  # Lưu PSO config đã dùng

    def _center_window(self):
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(max(0, w//2 - self.width()//2), max(0, h//2 - self.height()//2))
    
    def resizeEvent(self, event):
        """Handle window resize to maintain proportional layouts."""
        super().resizeEvent(event)

    def _init_navigation(self):
        """Thiết lập menu điều hướng."""
        self.addSubInterface(
            self.dashboard_interface, FIF.HOME, "Dashboard", NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.data_viewer, FIF.INFO, "Dữ Liệu Import", NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.result_interface, FIF.CALENDAR, "Kết quả xếp lịch", NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.setting_interface, FIF.SETTING, "Cài đặt hệ thống", NavigationItemPosition.BOTTOM
        )

    def _connect_signals(self):
        """Kết nối signal/slot."""
        self.config_widget.apply_clicked.connect(self.run_algorithm)
        self.config_widget.reset_clicked.connect(self.chart_widget.clear)
        # Kết nối nút Import dữ liệu
        self.config_widget.load_data_clicked.connect(self.import_data)

    @pyqtSlot()
    def import_data(self):
        """
        Hàm xử lý nhập file Excel/CSV.
        Quy trình: Chọn file Môn học -> (Chọn file Phòng thi) -> Load -> Cập nhật UI.
        """
        # 1. Chọn file Danh sách Môn học
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Chọn file Danh sách Môn học (Excel/CSV)", 
            "", 
            "Data Files (*.xlsx *.xls *.csv)"
        )
        
        if not file_path:
            return  # Người dùng bấm Cancel

        try:
            # Load Môn học trước để kiểm tra file có hợp lệ không
            new_courses = DataLoader.load_courses(file_path)
            
            # 2. Hỏi tiếp file Danh sách Phòng thi
            # Mặc định mở tại cùng thư mục với file môn học
            room_file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Chọn file Danh sách Phòng thi (Excel/CSV)", 
                str(Path(file_path).parent), 
                "Data Files (*.xlsx *.xls *.csv)"
            )
            
            if not room_file_path:
                # Nếu user không chọn file phòng, dùng lại phòng mẫu hoặc thông báo
                InfoBar.warning(
                    title="Chú ý",
                    content="Bạn chưa chọn file Phòng thi. Hệ thống sẽ sử dụng danh sách phòng mẫu.",
                    position=InfoBarPosition.TOP_RIGHT,
                    parent=self,
                    duration=3000
                )
            else:
                # Load Phòng thi
                new_rooms = DataLoader.load_rooms(room_file_path)
                self.rooms = new_rooms
                self.rooms_dict = {r.room_id: r for r in self.rooms}
            
            # 3. Hỏi file Danh sách Giám thị (Optional)
            proctor_file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Chọn file Danh sách Giám thị (Excel/CSV) - Tùy chọn",
                str(Path(file_path).parent),
                "Data Files (*.xlsx *.xls *.csv)"
            )
            
            if proctor_file_path:
                try:
                    new_proctors = DataLoader.load_proctors(proctor_file_path)
                    self.proctors = new_proctors
                    self.proctors_dict = {p.proctor_id: p for p in self.proctors}
                except Exception as e:
                    InfoBar.warning(
                        title="Cảnh báo",
                        content=f"Không thể load file Giám thị: {str(e)}. Hệ thống sẽ tiếp tục không có giám thị.",
                        position=InfoBarPosition.TOP_RIGHT,
                        parent=self,
                        duration=4000
                    )
                    self.proctors = []
                    self.proctors_dict = {}
            else:
                # Không chọn file giám thị - không bắt buộc
                self.proctors = []
                self.proctors_dict = {}

            # Cập nhật dữ liệu chính thức
            self.courses = new_courses
            
            # Cập nhật UI
            proctor_msg = f", {len(self.proctors)} giám thị" if self.proctors else ""
            status_msg = f"Đã nạp: {len(self.courses)} môn học, {len(self.rooms)} phòng thi{proctor_msg}."
            self.config_widget.set_data_status(status_msg, is_success=True)
            
            # <--- NEW: Cập nhật Data Viewer
            self.data_viewer.set_subjects_data(self.courses)
            self.data_viewer.set_rooms_data(self.rooms)
            self.data_viewer.set_proctors_data(self.proctors)
            self.data_viewer.update_stats(
                len(self.courses), 
                len(self.rooms), 
                len(self.proctors)
            )
            
            InfoBar.success(
                title="Import thành công",
                content=status_msg,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self,
                duration=3000
            )

        except Exception as e:
            # Thông báo lỗi chi tiết
            InfoBar.error(
                title="Lỗi Import Dữ liệu",
                content=str(e),
                position=InfoBarPosition.TOP_RIGHT,
                parent=self,
                duration=5000
            )

    @pyqtSlot()
    def run_algorithm(self):
        """
        Chạy thuật toán (SA hoặc PSO) dựa trên Config.
        """
        # 1. Lấy config từ Widget
        config = self.config_widget.get_config()
        
        # Lấy tên thuật toán từ config (nếu không có thì mặc định là SA)
        # Lưu ý: Cần đảm bảo ConfigWidget trả về key 'algorithm' là 'sa' hoặc 'pso'
        algo_type = config.get('algorithm', 'sa') 
        
        # 2. Reset biểu đồ
        self.chart_widget.clear()
        
        # 3. Deepcopy dữ liệu để không làm hỏng dữ liệu gốc
        import copy
        courses_copy = copy.deepcopy(self.courses)
        
        # 4. Khởi tạo Solver dựa trên lựa chọn (truyền proctors nếu có)
        if algo_type == 'pso':
            self.solver = PSOSolver(courses_copy, self.rooms, config, self.proctors)
            algo_name = "Particle Swarm Optimization (PSO)"
        else:
            self.solver = SASolver(courses_copy, self.rooms, config, self.proctors)
            algo_name = "Simulated Annealing (SA)"
            
        # 5. Kết nối signals
        self.solver.step_signal.connect(self.chart_widget.update_plot)
        self.solver.finished_signal.connect(self.on_solver_finished)
        self.solver.error_signal.connect(self.on_solver_error)
        
        # Kết nối log nếu có (Optional)
        if hasattr(self.solver, 'log_signal'):
             # Bạn có thể thêm 1 widget log nếu muốn, hoặc in ra console
             self.solver.log_signal.connect(print)

        # 6. Start
        self.solver.start()
        
        # UI Feedback
        self.config_widget.apply_btn.setEnabled(False)
        self.config_widget.load_data_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        InfoBar.info(
            title=f"Đang chạy {algo_name}...",
            content="Thuật toán đang tìm phương án tối ưu.",
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
            duration=3000
        )

    @pyqtSlot(object)
    def on_solver_finished(self, best_schedule: Schedule):
        """Xử lý khi thuật toán kết thúc."""
        # Mở lại các nút
        self.config_widget.apply_btn.setEnabled(True)
        self.config_widget.load_data_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # Cập nhật chart widget với dữ liệu cuối cùng
        if self.solver and best_schedule:
            # Lấy convergence history từ solver
            convergence_history = self.solver.get_convergence_history()
            final_iteration = self.solver.total_iterations if hasattr(self.solver, 'total_iterations') else len(convergence_history) - 1
            final_cost = best_schedule.fitness_score if best_schedule.fitness_score is not None else (convergence_history[-1] if convergence_history else 0.0)
            
            # Cập nhật chart với dữ liệu cuối cùng
            self.chart_widget.update_final(final_iteration, final_cost, convergence_history)
        
        # Hiển thị kết quả (truyền proctors_dict để hiển thị tên giám thị)
        self.result_table.update_data(best_schedule, self.rooms_dict, self.proctors_dict)
        
        InfoBar.success(
            title="Hoàn thành!",
            content=f"Đã tìm thấy lịch thi. Fitness Score: {best_schedule.fitness_score:.2f}",
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
            duration=5000
        )
        
        # Chuyển tab
        self.switchTo(self.result_interface)

    @pyqtSlot(str)
    def on_solver_error(self, error_msg: str):
        """Xử lý lỗi."""
        self.config_widget.apply_btn.setEnabled(True)
        self.config_widget.load_data_btn.setEnabled(True)
        
        InfoBar.error(
            title="Lỗi thuật toán",
            content=error_msg,
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
            duration=5000
        )
    
    @pyqtSlot()
    def export_data(self):
        """Xuất kết quả hiện tại ra Excel."""
        if not self.solver or not self.solver.best_solution:
            InfoBar.warning(title="Chưa có dữ liệu", content="Vui lòng chạy thuật toán trước.", parent=self)
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu file Excel", "Lich_Thi.xlsx", "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        success = Exporter.export_to_excel(self.solver.best_solution, file_path, self.proctors_dict)

        if success:
            InfoBar.success(title="Thành công", content=f"Đã lưu file tại: {file_path}", parent=self)
        else:
            InfoBar.error(title="Thất bại", content="Có lỗi khi ghi file Excel.", parent=self)
    
    @pyqtSlot()
    def run_benchmark(self):
        """
        Chạy so sánh hiệu năng giữa SA và PSO trên cùng bộ dữ liệu.
        Chạy tuần tự: SA trước, sau đó PSO.
        """
        # Kiểm tra nếu đang chạy benchmark hoặc solver khác
        if self.benchmark_running:
            InfoBar.warning(
                title="Đang chạy",
                content="Benchmark đang được thực hiện. Vui lòng đợi...",
                position=InfoBarPosition.TOP_RIGHT,
                parent=self,
                duration=3000
            )
            return
        
        if self.solver and self.solver.is_running:
            InfoBar.warning(
                title="Đang chạy",
                content="Thuật toán khác đang chạy. Vui lòng dừng trước khi chạy benchmark.",
                position=InfoBarPosition.TOP_RIGHT,
                parent=self,
                duration=3000
            )
            return
        
        # Kiểm tra dữ liệu
        if not self.courses or not self.rooms:
            InfoBar.warning(
                title="Thiếu dữ liệu",
                content="Vui lòng tải dữ liệu môn học và phòng thi trước.",
                position=InfoBarPosition.TOP_RIGHT,
                parent=self,
                duration=3000
            )
            return
        
        # Lấy config mặc định từ Widget (chỉ dùng làm base)
        base_config = self.config_widget.get_config()
        
        # Hiển thị BenchmarkConfigDialog
        try:
            from src.ui.widgets.benchmark_config_dialog import BenchmarkConfigDialog
            # Truyền base_config để dialog có thể dùng làm giá trị mặc định
            dialog = BenchmarkConfigDialog(self, default_config=base_config)
            if dialog.exec_() != QDialog.Accepted:
                return  # Người dùng bấm Cancel
            
            # Lấy settings từ dialog
            settings = dialog.get_settings()
        except ImportError:
            # Nếu dialog chưa tồn tại, dùng config mặc định từ widget
            InfoBar.warning(
                title="Dialog chưa có",
                content="BenchmarkConfigDialog chưa được tạo. Đang dùng config mặc định.",
                position=InfoBarPosition.TOP_RIGHT,
                parent=self,
                duration=3000
            )
            # Fallback: dùng config từ widget
            settings = {
                'sa_iterations': base_config.get('max_iterations', 5000),
                'pso_iterations': base_config.get('max_iterations', 500),
                'pso_swarm_size': base_config.get('swarm_size', 50)
            }
        
        # Reset kết quả và config cũ
        self.benchmark_sa_result = None
        self.benchmark_pso_result = None
        self._benchmark_sa_config = None
        self._benchmark_pso_config = None
        self._temp_pso_config = None
        
        # ============================================================
        # CÔ LẬP CẤU HÌNH (Configuration Isolation)
        # ============================================================
        # Tạo config hoàn toàn mới và độc lập cho SA
        sa_bench_config = base_config.copy()
        sa_bench_config['algorithm'] = 'sa'
        # GHI ĐÈ max_iterations từ dialog
        sa_bench_config['max_iterations'] = settings['sa_iterations']
        
        # Tạo config hoàn toàn mới và độc lập cho PSO
        pso_bench_config = base_config.copy()
        pso_bench_config['algorithm'] = 'pso'
        # GHI ĐÈ max_iterations và swarm_size từ dialog
        pso_bench_config['max_iterations'] = settings['pso_iterations']
        pso_bench_config['swarm_size'] = settings['pso_swarm_size']
        
        # Lưu config để dùng trong báo cáo
        self._benchmark_sa_config = sa_bench_config.copy()
        self._benchmark_pso_config = pso_bench_config.copy()
        
        # Lưu tạm PSO config để truyền qua callback
        self._temp_pso_config = pso_bench_config
        
        # Deepcopy dữ liệu
        import copy
        courses_copy = copy.deepcopy(self.courses)
        
        # Disable các nút
        self.benchmark_btn.setEnabled(False)
        self.config_widget.apply_btn.setEnabled(False)
        self.config_widget.load_data_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        # Clear chart
        self.chart_widget.clear()
        
        # Bước 1: Chạy SA với config đã cô lập
        InfoBar.info(
            title="Bắt đầu Benchmark",
            content=f"Đang chạy Simulated Annealing (SA) - {sa_bench_config['max_iterations']} vòng lặp...",
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
            duration=5000
        )
        
        self.benchmark_running = True
        self._run_sa_for_benchmark(courses_copy, sa_bench_config)
    
    def _run_sa_for_benchmark(self, courses_copy, sa_bench_config):
        """
        Chạy SA cho benchmark với config đã cô lập.
        
        Args:
            courses_copy: Deepcopy của courses.
            sa_bench_config: Config đã được cô lập cho SA (có max_iterations từ dialog).
        """
        # Khởi tạo SA Solver với config đã cô lập
        sa_solver = SASolver(courses_copy, self.rooms, sa_bench_config)
        
        # Kết nối signals
        sa_solver.step_signal.connect(self.chart_widget.update_plot)
        # Sử dụng lambda để truyền pso_config từ self._temp_pso_config
        sa_solver.finished_signal.connect(
            lambda schedule: self._on_sa_finished_for_benchmark(schedule, sa_solver, courses_copy)
        )
        sa_solver.error_signal.connect(
            lambda msg: self._on_benchmark_error(msg, "SA")
        )
        
        # Lưu solver để có thể stop
        self.solver = sa_solver
        
        # Start
        sa_solver.start()
    
    def _on_sa_finished_for_benchmark(self, best_schedule: Schedule, sa_solver, courses_copy):
        """
        Xử lý khi SA kết thúc trong benchmark.
        
        Args:
            best_schedule: Schedule tốt nhất từ SA.
            sa_solver: SA Solver instance.
            courses_copy: Deepcopy của courses (không dùng, chỉ để tương thích).
        """
        # Lưu kết quả SA
        sa_history = sa_solver.get_convergence_history()
        sa_time = sa_solver.get_execution_time()
        sa_iterations = sa_solver.total_iterations if hasattr(sa_solver, 'total_iterations') else len(sa_history)
        sa_initial = sa_history[0] if sa_history else 0
        sa_best = best_schedule.fitness_score if best_schedule.fitness_score is not None else (sa_history[-1] if sa_history else 0)
        sa_improvement = ((sa_initial - sa_best) / sa_initial * 100) if sa_initial > 0 else 0
        
        self.benchmark_sa_result = {
            'schedule': best_schedule,
            'history': sa_history,
            'time': sa_time,
            'iterations': sa_iterations,
            'initial_cost': sa_initial,
            'best_cost': sa_best,
            'improvement': sa_improvement,
            'feasible': sa_solver.constraint_checker.is_feasible(best_schedule) if hasattr(sa_solver, 'constraint_checker') else False
        }
        
        # Thông báo SA hoàn thành
        InfoBar.success(
            title="SA hoàn thành",
            content=f"SA: {sa_best:.2f} ({sa_improvement:.1f}%) - Đang chạy PSO...",
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
            duration=5000
        )
        
        # Bước 2: Tự động chạy PSO với config đã cô lập
        # Lấy PSO config từ biến tạm (đã được set trong run_benchmark)
        if self._temp_pso_config is None:
            self._on_benchmark_error("PSO config không tồn tại", "SA")
            return
        
        pso_bench_config = self._temp_pso_config
        import copy
        courses_copy_pso = copy.deepcopy(self.courses)
        self._run_pso_for_benchmark(courses_copy_pso, pso_bench_config)
    
    def _run_pso_for_benchmark(self, courses_copy, pso_bench_config):
        """
        Chạy PSO cho benchmark với config đã cô lập.
        
        Args:
            courses_copy: Deepcopy của courses.
            pso_bench_config: Config đã được cô lập cho PSO (có max_iterations và swarm_size từ dialog).
        """
        # Khởi tạo PSO Solver với config đã cô lập
        pso_solver = PSOSolver(courses_copy, self.rooms, pso_bench_config)
        
        # Kết nối signals - không update chart (sẽ vẽ so sánh sau)
        # pso_solver.step_signal.connect(self.chart_widget.update_plot)  # Tạm thời không vẽ real-time
        pso_solver.finished_signal.connect(
            lambda schedule: self._on_pso_finished_for_benchmark(schedule, pso_solver)
        )
        pso_solver.error_signal.connect(
            lambda msg: self._on_benchmark_error(msg, "PSO")
        )
        
        # Lưu solver để có thể stop
        self.solver = pso_solver
        
        # Start
        pso_solver.start()
    
    def _on_pso_finished_for_benchmark(self, best_schedule: Schedule, pso_solver):
        """Xử lý khi PSO kết thúc trong benchmark."""
        # Lưu kết quả PSO
        pso_history = pso_solver.get_convergence_history()
        pso_time = pso_solver.get_execution_time()
        pso_iterations = pso_solver.total_iterations if hasattr(pso_solver, 'total_iterations') else len(pso_history)
        pso_initial = pso_history[0] if pso_history else 0
        pso_best = best_schedule.fitness_score if best_schedule.fitness_score is not None else (pso_history[-1] if pso_history else 0)
        pso_improvement = ((pso_initial - pso_best) / pso_initial * 100) if pso_initial > 0 else 0
        
        self.benchmark_pso_result = {
            'schedule': best_schedule,
            'history': pso_history,
            'time': pso_time,
            'iterations': pso_iterations,
            'initial_cost': pso_initial,
            'best_cost': pso_best,
            'improvement': pso_improvement,
            'feasible': pso_solver.constraint_checker.is_feasible(best_schedule) if hasattr(pso_solver, 'constraint_checker') else False
        }
        
        # Bước 3: Vẽ biểu đồ so sánh
        if self.benchmark_sa_result and self.benchmark_pso_result:
            self.chart_widget.plot_comparison(
                self.benchmark_sa_result['history'],
                self.benchmark_pso_result['history']
            )
        
        # Bước 4: Hiển thị dialog so sánh
        self._show_benchmark_dialog()
        
        # Reset flag
        self.benchmark_running = False
        
        # Enable các nút
        self.benchmark_btn.setEnabled(True)
        self.config_widget.apply_btn.setEnabled(True)
        self.config_widget.load_data_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # Thông báo hoàn thành
        InfoBar.success(
            title="Benchmark hoàn thành!",
            content="Đã so sánh xong SA và PSO. Xem kết quả chi tiết trong dialog.",
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
            duration=5000
        )
    
    def _on_benchmark_error(self, error_msg: str, algorithm_name: str):
        """Xử lý lỗi trong benchmark."""
        self.benchmark_running = False
        
        # Enable các nút
        self.benchmark_btn.setEnabled(True)
        self.config_widget.apply_btn.setEnabled(True)
        self.config_widget.load_data_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        InfoBar.error(
            title=f"Lỗi {algorithm_name} trong Benchmark",
            content=error_msg,
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
            duration=5000
        )
    
    def _show_benchmark_dialog(self):
        """Hiển thị dialog so sánh kết quả benchmark."""
        if not self.benchmark_sa_result or not self.benchmark_pso_result:
            return
        
        # Tạo dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("📊 Kết quả So sánh Hiệu năng (Benchmark)")
        dialog.setMinimumWidth(700)
        dialog.setMinimumHeight(500)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title_label = QLabel("📊 So sánh SA vs PSO")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # Tạo bảng so sánh
        table = QTableWidget()
        table.setColumnCount(3)
        table.setRowCount(8)  # Tăng lên 8 vì thêm dòng "Số vòng lặp (Thực tế)"
        table.setHorizontalHeaderLabels(["Chỉ số", "Simulated Annealing (SA)", "Particle Swarm Optimization (PSO)"])
        
        # Dữ liệu
        sa_result = self.benchmark_sa_result
        pso_result = self.benchmark_pso_result
        
        # Xác định winner
        winner_sa = "🏆" if sa_result['best_cost'] < pso_result['best_cost'] else ""
        winner_pso = "🏆" if pso_result['best_cost'] < sa_result['best_cost'] else ""
        if sa_result['best_cost'] == pso_result['best_cost']:
            winner_sa = "⚖️"
            winner_pso = "⚖️"
        
        # Lấy số vòng lặp từ config đã dùng thực tế (KHÔNG đọc từ UI)
        sa_max_iter = self._benchmark_sa_config.get('max_iterations', sa_result['iterations']) if self._benchmark_sa_config else sa_result['iterations']
        pso_max_iter = self._benchmark_pso_config.get('max_iterations', pso_result['iterations']) if self._benchmark_pso_config else pso_result['iterations']
        
        data = [
            ("Thời gian thực thi (s)", f"{sa_result['time']:.2f}", f"{pso_result['time']:.2f}"),
            ("Số vòng lặp (Config)", f"{sa_max_iter}", f"{pso_max_iter}"),  # Dùng config đã chạy thực tế
            ("Số vòng lặp (Thực tế)", f"{sa_result['iterations']}", f"{pso_result['iterations']}"),
            ("Cost ban đầu", f"{sa_result['initial_cost']:.2f}", f"{pso_result['initial_cost']:.2f}"),
            (f"Cost tốt nhất {winner_sa}", f"{sa_result['best_cost']:.2f}", f"{pso_result['best_cost']:.2f} {winner_pso}"),
            ("Cải thiện (%)", f"{sa_result['improvement']:.2f}%", f"{pso_result['improvement']:.2f}%"),
            ("Khả thi (Feasible)", "✅ Có" if sa_result['feasible'] else "❌ Không", "✅ Có" if pso_result['feasible'] else "❌ Không"),
            ("Tốc độ (iter/s)", f"{sa_result['iterations']/sa_result['time']:.2f}" if sa_result['time'] > 0 else "N/A", 
             f"{pso_result['iterations']/pso_result['time']:.2f}" if pso_result['time'] > 0 else "N/A"),
        ]
        
        for row, (label, sa_val, pso_val) in enumerate(data):
            # Label
            table.setItem(row, 0, QTableWidgetItem(label))
            table.item(row, 0).setFlags(Qt.ItemIsEnabled)  # Read-only
            
            # SA value
            sa_item = QTableWidgetItem(sa_val)
            if row == 4:  # Best cost row (index 4 vì có thêm dòng "Số vòng lặp (Thực tế)")
                if sa_result['best_cost'] < pso_result['best_cost']:
                    sa_item.setForeground(Qt.red)
                elif sa_result['best_cost'] > pso_result['best_cost']:
                    sa_item.setForeground(Qt.blue)
            table.setItem(row, 1, sa_item)
            
            # PSO value
            pso_item = QTableWidgetItem(pso_val)
            if row == 4:  # Best cost row (index 4 vì có thêm dòng "Số vòng lặp (Thực tế)")
                if pso_result['best_cost'] < sa_result['best_cost']:
                    pso_item.setForeground(Qt.blue)
                elif pso_result['best_cost'] > sa_result['best_cost']:
                    pso_item.setForeground(Qt.red)
            table.setItem(row, 2, pso_item)
        
        # Resize columns
        table.resizeColumnsToContents()
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(table)
        
        # Summary
        if sa_result['best_cost'] < pso_result['best_cost']:
            summary = f"🏆 SA tốt hơn PSO: {pso_result['best_cost'] - sa_result['best_cost']:.2f} ({((pso_result['best_cost'] - sa_result['best_cost']) / pso_result['best_cost'] * 100):.1f}%)"
            summary_color = "red"
        elif pso_result['best_cost'] < sa_result['best_cost']:
            summary = f"🏆 PSO tốt hơn SA: {sa_result['best_cost'] - pso_result['best_cost']:.2f} ({((sa_result['best_cost'] - pso_result['best_cost']) / sa_result['best_cost'] * 100):.1f}%)"
            summary_color = "blue"
        else:
            summary = "⚖️ Hai thuật toán cho kết quả bằng nhau!"
            summary_color = "green"
        
        summary_label = QLabel(summary)
        summary_label.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {summary_color}; padding: 10px;")
        layout.addWidget(summary_label)
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()