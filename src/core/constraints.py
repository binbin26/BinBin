"""
Module xử lý các ràng buộc và tính toán hàm mục tiêu (cost function) cho bài toán xếp lịch thi.
Điểm phạt càng cao = lịch thi càng kém chất lượng (minimization problem).
"""

from typing import Dict, List, Tuple, Set
from collections import defaultdict
import sys
from pathlib import Path

# Import models
sys.path.append(str(Path(__file__).parent.parent))
from models.solution import Schedule
from models.course import Course
from models.room import Room


class ConstraintWeights:
    """
    Class chứa các hệ số phạt cho từng loại vi phạm.
    Dễ dàng điều chỉnh để fine-tune thuật toán.
    """
    # Hard Constraints (Vi phạm nghiêm trọng - KHÔNG được phép)
    ROOM_CONFLICT = 1000.0          # Trùng phòng cùng ngày/giờ
    ROOM_OVERCAPACITY = 500.0       # Số sinh viên vượt sức chứa phòng
    PROCTOR_CONFLICT = 1000.0       # Một giám thị coi thi 2 môn cùng thời điểm
    
    # Soft Constraints (Vi phạm nhẹ - Nên tránh nhưng chấp nhận được)
    LOCATION_MISMATCH = 50.0        # Sai địa điểm (cơ sở)
    
    # Penalty cho môn chưa xếp lịch (optional - để đảm bảo tất cả môn đều được xếp)
    UNSCHEDULED_COURSE = 2000.0     # Môn học chưa được xếp lịch
    
    # Enhanced: Tối ưu hóa sử dụng phòng
    UNDERUTILIZATION = 5.0           # Lãng phí sức chứa phòng (số SV ít nhưng chọn phòng lớn)
    ROOM_DISTANCE_PENALTY = 2.0     # Phạt khi các ca của cùng môn ở phòng xa nhau


class ConstraintChecker:
    """
    Class chính để kiểm tra các ràng buộc và tính toán điểm phạt.
    Sử dụng các cấu trúc dữ liệu tối ưu để tăng hiệu năng.
    """
    
    def __init__(self, rooms: List[Room] = None, 
                 max_exams_per_week: int = 5, 
                 max_exams_per_day: int = 3):
        """
        Khởi tạo ConstraintChecker.
        
        Args:
            rooms (List[Room], optional): Danh sách các phòng thi có sẵn.
                                         Dùng để kiểm tra sức chứa nhanh hơn.
            max_exams_per_week (int): Tối đa số môn thi 1 giám thị trong 1 tuần (mặc định: 5).
            max_exams_per_day (int): Tối đa số môn thi 1 giám thị trong 1 ngày (mặc định: 3).
        """
        self.rooms_dict: Dict[str, Room] = {}
        if rooms:
            self.rooms_dict = {room.room_id: room for room in rooms}
        
        # Proctor constraints
        self.max_exams_per_week = max_exams_per_week
        self.max_exams_per_day = max_exams_per_day
    
    def set_rooms(self, rooms: List[Room]) -> None:
        """
        Cập nhật danh sách phòng thi (hữu ích khi load dữ liệu động).
        
        Args:
            rooms (List[Room]): Danh sách các phòng thi.
        """
        self.rooms_dict = {room.room_id: room for room in rooms}
    
    def _check_overlap(self, t1_start_str: str, t1_duration: int, 
                       t2_start_str: str, t2_duration: int) -> bool:
        """
        ENHANCED: Helper method để kiểm tra xem 2 khoảng thời gian có bị chồng lấn (overlap) không.
        
        Sử dụng datetime để tính toán chính xác:
        - t1: [t1_start, t1_start + t1_duration]
        - t2: [t2_start, t2_start + t2_duration]
        
        Overlap xảy ra khi: t1_start < t2_start + t2_duration AND t2_start < t1_start + t1_duration
        
        Args:
            t1_start_str (str): Thời gian bắt đầu môn 1 (format: "HH:MM").
            t1_duration (int): Thời lượng môn 1 (phút).
            t2_start_str (str): Thời gian bắt đầu môn 2 (format: "HH:MM").
            t2_duration (int): Thời lượng môn 2 (phút).
        
        Returns:
            bool: True nếu có overlap, False nếu không.
        """
        try:
            from datetime import datetime, timedelta
            
            # Parse thời gian bắt đầu
            t1_start = datetime.strptime(t1_start_str, "%H:%M")
            t2_start = datetime.strptime(t2_start_str, "%H:%M")
            
            # Tính thời gian kết thúc
            t1_end = t1_start + timedelta(minutes=t1_duration)
            t2_end = t2_start + timedelta(minutes=t2_duration)
            
            # Kiểm tra overlap: 2 khoảng [a, b] và [c, d] overlap khi a < d AND c < b
            return t1_start < t2_end and t2_start < t1_end
        except (ValueError, TypeError):
            # Nếu parse thất bại, coi như không overlap
            return False
    
    
    def _check_room_conflicts(self, schedule: Schedule) -> float:
        """
        Kiểm tra vi phạm trùng phòng: Nhiều môn thi cùng phòng, cùng ngày, cùng giờ.
        
        ENHANCED: Hỗ trợ kiểm tra cả sessions.
        ENHANCED: Kiểm tra overlap thời gian dựa trên duration, không chỉ so sánh giờ bắt đầu.
        
        Strategy:
            - Nhóm các môn theo (date, room)
            - Kiểm tra từng cặp môn trong cùng nhóm xem thời gian có overlap không
            - Sử dụng _check_overlap để kiểm tra với duration
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
        
        Returns:
            float: Tổng điểm phạt cho vi phạm trùng phòng.
        """
        penalty = 0.0
        
        # Dictionary: (date, room) -> List[(course, time, duration)]
        room_schedule: Dict[Tuple[str, str], List[Tuple[Course, str, int]]] = defaultdict(list)
        
        for course in schedule.courses:
            # Xử lý sessions nếu có
            if course.sessions:
                for session in course.sessions:
                    if session.is_scheduled():
                        key = (session.assigned_date, session.assigned_room)
                        duration = getattr(course, 'duration', 90)  # Lấy duration từ course cha
                        room_schedule[key].append((session, session.assigned_time, duration))
            # Backward compatible: Xử lý course không chia ca
            elif course.is_scheduled():
                key = (course.assigned_date, course.assigned_room)
                duration = getattr(course, 'duration', 90)  # Lấy duration từ course
                room_schedule[key].append((course, course.assigned_time, duration))
        
        # Kiểm tra overlap giữa các cặp môn trong cùng phòng/ngày
        for (date, room), exams in room_schedule.items():
            # Kiểm tra tất cả các cặp
            for i in range(len(exams)):
                for j in range(i + 1, len(exams)):
                    exam1, time1, duration1 = exams[i]
                    exam2, time2, duration2 = exams[j]
                    
                    # Kiểm tra overlap
                    if self._check_overlap(time1, duration1, time2, duration2):
                        penalty += ConstraintWeights.ROOM_CONFLICT
        
        return penalty
    
    def _check_proctor_conflicts(self, schedule: Schedule) -> float:
        """
        Kiểm tra vi phạm trùng giám thị: Một giám thị coi thi 2 môn tại cùng một thời điểm (Ngày + Giờ).
        
        ENHANCED: Kiểm tra overlap thời gian dựa trên duration, không chỉ so sánh giờ bắt đầu.
        
        Strategy:
            - Nhóm các môn theo (date, proctor_id)
            - Kiểm tra từng cặp môn trong cùng nhóm xem thời gian có overlap không
            - Sử dụng _check_overlap để kiểm tra với duration
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
        
        Returns:
            float: Tổng điểm phạt cho vi phạm trùng giám thị.
        """
        penalty = 0.0
        
        # Dictionary: (date, proctor_id) -> List[(course, time, duration)]
        proctor_schedule: Dict[Tuple[str, str], List[Tuple[Course, str, int]]] = defaultdict(list)
        
        for course in schedule.courses:
            # Chỉ kiểm tra nếu môn học đã được xếp lịch và có giám thị
            if not course.is_scheduled() or not course.assigned_proctor_id:
                continue
            
            # Xử lý sessions nếu có
            if course.sessions:
                for session in course.sessions:
                    if session.is_scheduled() and hasattr(session, 'assigned_proctor_id') and session.assigned_proctor_id:
                        key = (session.assigned_date, session.assigned_proctor_id)
                        duration = getattr(course, 'duration', 90)
                        proctor_schedule[key].append((session, session.assigned_time, duration))
            # Backward compatible: Xử lý course không chia ca
            else:
                key = (course.assigned_date, course.assigned_proctor_id)
                duration = getattr(course, 'duration', 90)
                proctor_schedule[key].append((course, course.assigned_time, duration))
        
        # Kiểm tra overlap giữa các cặp môn cùng giám thị/ngày
        for (date, proctor_id), exams in proctor_schedule.items():
            # Kiểm tra tất cả các cặp
            for i in range(len(exams)):
                for j in range(i + 1, len(exams)):
                    exam1, time1, duration1 = exams[i]
                    exam2, time2, duration2 = exams[j]
                    
                    # Kiểm tra overlap
                    if self._check_overlap(time1, duration1, time2, duration2):
                        penalty += ConstraintWeights.PROCTOR_CONFLICT
        
        return penalty
    
    def _check_room_capacity(self, schedule: Schedule) -> float:
        """
        Kiểm tra vi phạm quá tải phòng: Số sinh viên > sức chứa phòng.
        
        ENHANCED: Hỗ trợ kiểm tra cả sessions.
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
        
        Returns:
            float: Tổng điểm phạt cho vi phạm quá tải.
        """
        penalty = 0.0
        
        for course in schedule.courses:
            # Xử lý sessions nếu có
            if course.sessions:
                for session in course.sessions:
                    if not session.is_scheduled():
                        continue
                    
                    room_id = session.assigned_room
                    
                    if room_id not in self.rooms_dict:
                        penalty += ConstraintWeights.ROOM_OVERCAPACITY
                        continue
                    
                    room = self.rooms_dict[room_id]
                    
                    # Kiểm tra sức chứa cho từng session
                    if session.student_count > room.capacity:
                        overflow = session.student_count - room.capacity
                        penalty += ConstraintWeights.ROOM_OVERCAPACITY * (1 + overflow / 10)
            
            # Backward compatible: Xử lý course không chia ca
            elif course.is_scheduled():
                room_id = course.assigned_room
                
                if room_id not in self.rooms_dict:
                    penalty += ConstraintWeights.ROOM_OVERCAPACITY
                    continue
                
                room = self.rooms_dict[room_id]
                
                # Kiểm tra sức chứa
                if course.student_count > room.capacity:
                    overflow = course.student_count - room.capacity
                    penalty += ConstraintWeights.ROOM_OVERCAPACITY * (1 + overflow / 10)
        
        return penalty
    
    def _check_location_mismatch(self, schedule: Schedule) -> float:
        """
        Kiểm tra vi phạm sai địa điểm: Môn học yêu cầu thi ở cơ sở A nhưng xếp vào phòng thuộc cơ sở B.
        
        ENHANCED: Hỗ trợ kiểm tra cả sessions.
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
        
        Returns:
            float: Tổng điểm phạt cho vi phạm sai địa điểm.
        """
        penalty = 0.0
        
        for course in schedule.courses:
            # Xử lý sessions nếu có
            if course.sessions:
                for session in course.sessions:
                    if not session.is_scheduled():
                        continue
                    
                    room_id = session.assigned_room
                    
                    if room_id not in self.rooms_dict:
                        continue
                    
                    room = self.rooms_dict[room_id]
                    course_location = course.location.strip().lower()
                    room_location = room.location.strip().lower()
                    
                    if course_location != room_location:
                        penalty += ConstraintWeights.LOCATION_MISMATCH
            
            # Backward compatible: Xử lý course không chia ca
            elif course.is_scheduled():
                room_id = course.assigned_room
                
                if room_id not in self.rooms_dict:
                    continue
                
                room = self.rooms_dict[room_id]
                course_location = course.location.strip().lower()
                room_location = room.location.strip().lower()
                
                if course_location != room_location:
                    penalty += ConstraintWeights.LOCATION_MISMATCH
        
        return penalty
    
    def _check_unscheduled_courses(self, schedule: Schedule) -> float:
        """
        Kiểm tra các môn học chưa được xếp lịch.
        (Optional - Tùy thuộc vào cách implement thuật toán SA)
        
        ENHANCED: Hỗ trợ kiểm tra cả sessions.
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
        
        Returns:
            float: Tổng điểm phạt cho các môn chưa xếp lịch.
        """
        penalty = 0.0
        
        for course in schedule.courses:
            if not course.is_scheduled():
                penalty += ConstraintWeights.UNSCHEDULED_COURSE
        
        return penalty
    
    def _check_room_underutilization(self, schedule: Schedule) -> float:
        """
        Kiểm tra lãng phí sức chứa phòng (Underutilization).
        
        Penalty: Phạt khi số lượng sinh viên ít nhưng chọn phòng lớn.
        Mục tiêu: Tối ưu utilization rate (số SV / sức chứa phòng).
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
        
        Returns:
            float: Tổng điểm phạt cho lãng phí sức chứa.
        """
        penalty = 0.0
        
        for course in schedule.courses:
            # Xử lý sessions nếu có
            if course.sessions:
                for session in course.sessions:
                    if not session.is_scheduled():
                        continue
                    
                    room_id = session.assigned_room
                    if room_id not in self.rooms_dict:
                        continue
                    
                    room = self.rooms_dict[room_id]
                    utilization = session.student_count / room.capacity if room.capacity > 0 else 0
                    
                    # Phạt nếu utilization < 50% (lãng phí > 50%)
                    if utilization < 0.5:
                        waste_ratio = 1.0 - utilization
                        penalty += ConstraintWeights.UNDERUTILIZATION * waste_ratio * room.capacity
            
            # Backward compatible: Xử lý course không chia ca
            elif course.is_scheduled():
                room_id = course.assigned_room
                if room_id not in self.rooms_dict:
                    continue
                
                room = self.rooms_dict[room_id]
                utilization = course.student_count / room.capacity if room.capacity > 0 else 0
                
                # Phạt nếu utilization < 50%
                if utilization < 0.5:
                    waste_ratio = 1.0 - utilization
                    penalty += ConstraintWeights.UNDERUTILIZATION * waste_ratio * room.capacity
        
        return penalty
    
    def _check_room_distance_penalty(self, schedule: Schedule) -> float:
        """
        Phạt khi các ca của cùng một môn học ở phòng xa nhau.
        
        Mục tiêu: Ưu tiên các ca của cùng môn ở phòng gần nhau (cùng tầng, cùng khu vực).
        
        Strategy đơn giản: Phạt nếu các ca của cùng môn ở phòng khác nhau.
        (Có thể cải thiện bằng cách tính khoảng cách thực tế giữa các phòng)
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
        
        Returns:
            float: Tổng điểm phạt cho khoảng cách phòng.
        """
        penalty = 0.0
        
        for course in schedule.courses:
            # Chỉ xử lý môn học có nhiều ca
            if not course.sessions or len(course.sessions) < 2:
                continue
            
            # Lấy danh sách phòng của các ca đã được xếp lịch
            scheduled_rooms = [
                session.assigned_room 
                for session in course.sessions 
                if session.is_scheduled()
            ]
            
            # Nếu có nhiều hơn 1 ca và các ca ở phòng khác nhau
            if len(scheduled_rooms) > 1:
                unique_rooms = set(scheduled_rooms)
                if len(unique_rooms) > 1:
                    # Phạt khi các ca ở phòng khác nhau
                    # Penalty tăng theo số lượng phòng khác nhau
                    penalty += ConstraintWeights.ROOM_DISTANCE_PENALTY * (len(unique_rooms) - 1)
        
        return penalty
    
    def calculate_total_violation(self, schedule: Schedule) -> float:
        """
        Tính tổng điểm phạt (cost/fitness) cho một lịch thi.
        
        ENHANCED: Thêm penalty cho underutilization và room distance.
        
        Công thức:
            Total Cost = Σ (Room Conflicts) + Σ (Capacity Violations) 
                        + Σ (Location Mismatches) + Σ (Unscheduled Courses)
                        + Σ (Underutilization) + Σ (Room Distance)
        
        Args:
            schedule (Schedule): Lịch thi cần đánh giá.
        
        Returns:
            float: Tổng điểm phạt (càng thấp càng tốt).
        
        Performance:
            - Time Complexity: O(n) với n là số môn học/sessions
            - Space Complexity: O(n) cho các dictionary tạm
        
        Example:
            >>> checker = ConstraintChecker(rooms)
            >>> schedule = Schedule(courses=[...])
            >>> cost = checker.calculate_total_violation(schedule)
            >>> print(f"Total violation: {cost}")
        """
        total_penalty = 0.0
        
        # 1. Kiểm tra trùng phòng (Hard)
        total_penalty += self._check_room_conflicts(schedule)
        
        # 2. Kiểm tra quá tải phòng (Hard)
        total_penalty += self._check_room_capacity(schedule)
        
        # 3. Kiểm tra trùng giám thị (Hard)
        total_penalty += self._check_proctor_conflicts(schedule)
        
        # 4. Kiểm tra sai địa điểm (Soft)
        total_penalty += self._check_location_mismatch(schedule)
        
        # 5. Kiểm tra môn chưa xếp lịch (Optional)
        total_penalty += self._check_unscheduled_courses(schedule)
        
        # 6. ENHANCED: Kiểm tra lãng phí sức chứa (Soft - Optimization)
        total_penalty += self._check_room_underutilization(schedule)
        
        # 7. ENHANCED: Kiểm tra khoảng cách phòng cho cùng môn (Soft - Optimization)
        total_penalty += self._check_room_distance_penalty(schedule)
        
        # 8. NEW: Kiểm tra khối lượng công việc giám thị theo tuần (Soft constraint)
        total_penalty += self.check_proctor_workload_per_week(schedule, self.max_exams_per_week)
        
        # 9. NEW: Kiểm tra khối lượng công việc giám thị theo ngày (Soft constraint)
        total_penalty += self.check_proctor_workload_per_day(schedule, self.max_exams_per_day)
        
        return total_penalty
    
    def get_violation_details(self, schedule: Schedule) -> Dict[str, float]:
        """
        Phân tích chi tiết từng loại vi phạm (hữu ích cho debugging và visualization).
        
        ENHANCED: Thêm thông tin về underutilization và room distance.
        
        Args:
            schedule (Schedule): Lịch thi cần phân tích.
        
        Returns:
            Dict[str, float]: Dictionary chứa điểm phạt của từng loại vi phạm.
        """
        return {
            'room_conflicts': self._check_room_conflicts(schedule),
            'capacity_violations': self._check_room_capacity(schedule),
            'proctor_conflicts': self._check_proctor_conflicts(schedule),
            'location_mismatches': self._check_location_mismatch(schedule),
            'unscheduled_courses': self._check_unscheduled_courses(schedule),
            'underutilization': self._check_room_underutilization(schedule),
            'room_distance': self._check_room_distance_penalty(schedule),
            'proctor_workload_per_week': self.check_proctor_workload_per_week(schedule, self.max_exams_per_week),
            'proctor_workload_per_day': self.check_proctor_workload_per_day(schedule, self.max_exams_per_day),
            'total': self.calculate_total_violation(schedule)
        }
    
    def check_proctor_workload_per_week(self, schedule: Schedule, max_exams_per_week: int = 5) -> float:
        """
        Kiểm tra ràng buộc: Mỗi giám thị không được coi quá max_exams_per_week môn thi trong 1 tuần.
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
            max_exams_per_week (int): Tối đa số môn thi 1 giám thị có thể gác trong 1 tuần.
        
        Returns:
            float: Tổng điểm phạt (0 nếu không vi phạm).
        """
        from datetime import datetime, timedelta
        
        violation = 0.0
        proctor_exams_per_week = defaultdict(lambda: defaultdict(int))  # {proctor_id: {week_start: count}}
        
        for course in schedule.courses:
            if not course.is_scheduled() or not course.assigned_proctor_id:
                continue
            
            try:
                course_date = datetime.strptime(course.assigned_date, "%Y-%m-%d").date()
                # Tính thứ 2 của tuần (ngày bắt đầu tuần)
                weekday = course_date.weekday()  # 0=Monday, 6=Sunday
                monday = course_date - timedelta(days=weekday)
                
                proctor_exams_per_week[course.assigned_proctor_id][monday] += 1
            except ValueError:
                pass
        
        # Kiểm tra vi phạm
        for proctor_id, weeks in proctor_exams_per_week.items():
            for week_start, exam_count in weeks.items():
                if exam_count > max_exams_per_week:
                    # Mỗi môn vượt quá giới hạn bị phạt
                    violation += (exam_count - max_exams_per_week) * 200.0  # Hệ số phạt: 200
        
        return violation
    
    def check_proctor_workload_per_day(self, schedule: Schedule, max_exams_per_day: int = 3) -> float:
        """
        Kiểm tra ràng buộc: Mỗi giám thị không được coi quá max_exams_per_day môn thi trong 1 ngày.
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
            max_exams_per_day (int): Tối đa số môn thi 1 giám thị có thể gác trong 1 ngày.
        
        Returns:
            float: Tổng điểm phạt (0 nếu không vi phạm).
        """
        violation = 0.0
        proctor_exams_per_day = defaultdict(lambda: defaultdict(int))  # {proctor_id: {date: count}}
        
        for course in schedule.courses:
            if not course.is_scheduled() or not course.assigned_proctor_id:
                continue
            
            if course.assigned_date:
                proctor_exams_per_day[course.assigned_proctor_id][course.assigned_date] += 1
        
        # Kiểm tra vi phạm
        for proctor_id, days in proctor_exams_per_day.items():
            for date, exam_count in days.items():
                if exam_count > max_exams_per_day:
                    # Mỗi môn vượt quá giới hạn bị phạt
                    violation += (exam_count - max_exams_per_day) * 100.0  # Hệ số phạt: 100
        
        return violation
    
    def is_feasible(self, schedule: Schedule) -> bool:
        """
        Kiểm tra xem lịch thi có khả thi không (không vi phạm hard constraints).
        
        Args:
            schedule (Schedule): Lịch thi cần kiểm tra.
        
        Returns:
            bool: True nếu không có vi phạm hard constraints.
        """
        # Chỉ kiểm tra hard constraints
        room_conflicts = self._check_room_conflicts(schedule)
        capacity_violations = self._check_room_capacity(schedule)
        proctor_conflicts = self._check_proctor_conflicts(schedule)
        
        return room_conflicts == 0.0 and capacity_violations == 0.0 and proctor_conflicts == 0.0


# Function wrapper để dùng nhanh (backward compatibility)
def calculate_total_violation(schedule: Schedule, rooms: List[Room] = None) -> float:
    """
    Hàm tiện ích để tính tổng điểm phạt nhanh.
    
    Args:
        schedule (Schedule): Lịch thi cần đánh giá.
        rooms (List[Room], optional): Danh sách phòng thi.
    
    Returns:
        float: Tổng điểm phạt.
    """
    checker = ConstraintChecker(rooms)
    return checker.calculate_total_violation(schedule)

