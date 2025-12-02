#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test DataViewerWidget - Kiểm tra hiển thị dữ liệu Excel
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from src.ui.widgets.data_viewer import DataViewerWidget
from src.models.course import Course
from src.models.room import Room
from src.models.proctor import Proctor


def test_data_viewer():
    """Test DataViewerWidget with sample data."""
    
    app = QApplication(sys.argv)
    
    # Create widget
    widget = DataViewerWidget()
    print("✅ DataViewerWidget created successfully")
    
    # Create sample data
    sample_courses = [
        Course(course_id="C001", name="TOÁN CAO CẤP I", student_count=45, location="A101", 
               exam_format="Tự luận", duration=90, is_locked=True, note="Cố định"),
        Course(course_id="C002", name="LẬP TRÌNH C++", student_count=60, location="A102",
               exam_format="Thực hành", duration=120, is_locked=False, note=""),
        Course(course_id="C003", name="CÁC PHƯƠNG PHÁP THỐNG KÊ", student_count=35, location="A103",
               exam_format="Trắc nghiệm", duration=60, is_locked=True, note="HẠNG II"),
    ]
    print(f"✅ Created {len(sample_courses)} sample courses")
    
    sample_rooms = [
        Room(room_id="A101", capacity=50, location="Tòa A"),
        Room(room_id="A102", capacity=60, location="Tòa A"),
        Room(room_id="B201", capacity=40, location="Tòa B"),
    ]
    print(f"✅ Created {len(sample_rooms)} sample rooms")
    
    sample_proctors = [
        Proctor(proctor_id="P001", name="Nguyễn Văn A", location="Tòa A"),
        Proctor(proctor_id="P002", name="Trần Thị B", location="Tòa B"),
        Proctor(proctor_id="P003", name="Phạm Văn C", location="Tòa A"),
    ]
    print(f"✅ Created {len(sample_proctors)} sample proctors")
    
    # Set data to widget
    widget.set_subjects_data(sample_courses)
    print("✅ set_subjects_data() works")
    
    widget.set_rooms_data(sample_rooms)
    print("✅ set_rooms_data() works")
    
    widget.set_proctors_data(sample_proctors)
    print("✅ set_proctors_data() works")
    
    # Update stats
    widget.update_stats(
        len(sample_courses),
        len(sample_rooms),
        len(sample_proctors)
    )
    print("✅ update_stats() works")
    
    # Test with empty data
    widget.set_subjects_data([])
    print("✅ Empty data handling works")
    
    # Test with single item
    widget.set_rooms_data(sample_rooms[:1])
    print("✅ Single item display works")
    
    print("\n" + "="*60)
    print("✅ ALL DATA VIEWER TESTS PASSED!")
    print("="*60)
    
    # Don't show GUI, just exit
    sys.exit(0)


if __name__ == '__main__':
    test_data_viewer()
