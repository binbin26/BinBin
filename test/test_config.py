"""Test script để debug config truyền từ ConfigWidget đến Solver."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Setup paths
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDate
from src.ui.widgets.config_widget import ConfigWidget


def test_config_widget():
    """Test ConfigWidget trả về config đúng không."""
    print("=" * 60)
    print("TEST CONFIG WIDGET")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # Tạo ConfigWidget
    config_widget = ConfigWidget()
    
    # Đặt ngày tùy ý
    test_start = QDate(2025, 12, 1)
    test_end = QDate(2025, 12, 15)
    
    config_widget.start_date.setDate(test_start)
    config_widget.end_date.setDate(test_end)
    config_widget.max_exams_per_week.setValue(7)
    config_widget.max_exams_per_day.setValue(4)
    
    print(f"\n📅 Ngày bắt đầu được chọn: {config_widget.start_date.date().toString('yyyy-MM-dd')}")
    print(f"📅 Ngày kết thúc được chọn: {config_widget.end_date.date().toString('yyyy-MM-dd')}")
    
    # Lấy config
    config = config_widget.get_config()
    
    print(f"\n📋 Config trả về từ get_config():")
    print(f"  - algorithm: {config.get('algorithm')}")
    print(f"  - schedule_config: {config.get('schedule_config')}")
    
    schedule_config = config.get('schedule_config', {})
    if schedule_config:
        print(f"\n  📌 Trong schedule_config:")
        print(f"    - start_date: {schedule_config.get('start_date')} (type: {type(schedule_config.get('start_date'))})")
        print(f"    - end_date: {schedule_config.get('end_date')} (type: {type(schedule_config.get('end_date'))})")
        print(f"    - max_exams_per_week: {schedule_config.get('max_exams_per_week')}")
        print(f"    - max_exams_per_day: {schedule_config.get('max_exams_per_day')}")
    
    # Mô phỏng _generate_exam_dates
    print(f"\n🔄 Mô phỏng _generate_exam_dates():")
    schedule_config = config.get('schedule_config', {})
    print(f"  - schedule_config từ config: {schedule_config}")
    
    if schedule_config and 'start_date' in schedule_config and 'end_date' in schedule_config:
        start_str = schedule_config['start_date']
        end_str = schedule_config['end_date']
        print(f"  - Sẽ sử dụng: {start_str} đến {end_str}")
        
        try:
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.strptime(end_str, "%Y-%m-%d")
            
            dates = []
            current = start
            while current <= end:
                dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)
            
            print(f"  - Số ngày sinh ra: {len(dates)}")
            print(f"  - Ngày đầu: {dates[0]}")
            print(f"  - Ngày cuối: {dates[-1]}")
            print(f"  - Tất cả ngày: {dates[:5]}... (hiển thị 5 ngày đầu)")
            
        except Exception as e:
            print(f"  ❌ LỖI: {e}")
    else:
        print(f"  ❌ schedule_config không hợp lệ hoặc rỗng")
        print(f"  - 'start_date' in schedule_config: {'start_date' in schedule_config}")
        print(f"  - 'end_date' in schedule_config: {'end_date' in schedule_config}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_config_widget()
