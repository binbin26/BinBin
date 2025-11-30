"""
Package models - Tầng dữ liệu của ứng dụng xếp lịch thi.

Module này cung cấp các data classes cơ bản:
- Course: Đại diện cho một môn học
- CourseSession: Đại diện cho một ca thi của môn học
- Room: Đại diện cho một phòng thi
- Schedule: Đại diện cho một giải pháp xếp lịch hoàn chỉnh

Các class này hoàn toàn độc lập với logic thuật toán và giao diện người dùng.
"""

from .course import Course
from .course_session import CourseSession
from .room import Room
from .solution import Schedule

__all__ = ['Course', 'CourseSession', 'Room', 'Schedule']

