# File: main.py
import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    # Hỗ trợ màn hình độ phân giải cao (High DPI)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    from PyQt5.QtCore import Qt # Import Qt để set attribute
    main()