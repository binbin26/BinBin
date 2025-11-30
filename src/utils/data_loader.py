"""
Module đọc dữ liệu từ file Excel/CSV vào các đối tượng Course và Room.
Sử dụng pandas để xử lý dữ liệu hiệu quả và hỗ trợ nhiều định dạng file.
"""

import pandas as pd
import random
from typing import List, Optional
from pathlib import Path
import logging

# Import các model classes
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.course import Course
from models.room import Room
from models.proctor import Proctor

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Class chịu trách nhiệm đọc dữ liệu từ file Excel/CSV và chuyển đổi
    thành các đối tượng Course và Room.
    
    Hỗ trợ:
        - File Excel (.xlsx, .xls)
        - File CSV (.csv)
        - Xử lý dữ liệu thiếu và dòng trống
        - Random số lượng sinh viên nếu không có dữ liệu
    """
    
    # Mapping tên cột trong file -> tên thuộc tính trong class
    COURSE_COLUMN_MAPPING = {
        'Mã LHP': 'course_id',
        'Tên HP': 'name',
        'Địa điểm': 'location',
        'Hình thức thi': 'exam_format',
        'Ghi chú': 'note',
        'Số lượng ĐK': 'student_count',
        'Số lượng SV': 'student_count',  # Alias
        'SL ĐK': 'student_count',  # Alias
        # ENHANCED: Thêm hỗ trợ cho duration và is_locked
        'Thời lượng': 'duration',
        'Duration': 'duration',  # Alias
        'Số phút': 'duration',  # Alias
        'Cố định': 'is_locked',
        'Locked': 'is_locked',  # Alias
        'Khóa': 'is_locked',  # Alias
    }
    
    ROOM_COLUMN_MAPPING = {
        'Tên phòng': 'room_id',
        'Phòng': 'room_id',  # Alias
        'Mã phòng': 'room_id',  # Alias
        'Sức chứa': 'capacity',
        'Sức chứa tối đa': 'capacity',  # Alias
        'Địa điểm': 'location',
        'Cơ sở': 'location',  # Alias
    }
    
    PROCTOR_COLUMN_MAPPING = {
        'Mã GT': 'proctor_id',
        'Mã Giám thị': 'proctor_id',  # Alias
        'ID': 'proctor_id',  # Alias
        'Tên GT': 'name',
        'Họ tên': 'name',  # Alias
        'Tên Giám thị': 'name',  # Alias
        'Cơ sở': 'location',
        'Địa điểm': 'location',  # Alias
    }
    
    @staticmethod
    def _detect_file_type(file_path: str) -> str:
        """
        Xác định loại file dựa trên phần mở rộng.
        
        Args:
            file_path (str): Đường dẫn đến file.
        
        Returns:
            str: Loại file ('excel' hoặc 'csv').
        
        Raises:
            ValueError: Nếu định dạng file không được hỗ trợ.
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension in ['.xlsx', '.xls']:
            return 'excel'
        elif extension == '.csv':
            return 'csv'
        else:
            raise ValueError(
                f"Định dạng file không được hỗ trợ: {extension}. "
                f"Chỉ hỗ trợ .xlsx, .xls, .csv"
            )
    
    @staticmethod
    def _read_file(file_path: str) -> pd.DataFrame:
        """
        Đọc file Excel hoặc CSV thành DataFrame.
        
        Args:
            file_path (str): Đường dẫn đến file.
        
        Returns:
            pd.DataFrame: Dữ liệu đã đọc.
        
        Raises:
            FileNotFoundError: Nếu file không tồn tại.
            Exception: Nếu có lỗi khi đọc file.
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        try:
            file_type = DataLoader._detect_file_type(file_path)
            
            if file_type == 'excel':
                df = pd.read_excel(file_path)
                logger.info(f"Đã đọc file Excel: {file_path}")
            else:  # csv
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                logger.info(f"Đã đọc file CSV: {file_path}")
            
            return df
        
        except Exception as e:
            logger.error(f"Lỗi khi đọc file {file_path}: {str(e)}")
            raise Exception(f"Không thể đọc file: {str(e)}")
    
    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Làm sạch DataFrame: xóa dòng trống, strip whitespace.
        
        Args:
            df (pd.DataFrame): DataFrame cần làm sạch.
        
        Returns:
            pd.DataFrame: DataFrame đã được làm sạch.
        """
        # Xóa các dòng hoàn toàn trống
        df = df.dropna(how='all')
        
        # Strip whitespace từ tên cột
        df.columns = df.columns.str.strip()
        
        # Strip whitespace từ các giá trị string
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
        
        # Thay thế 'nan' string thành NaN thực sự
        df = df.replace('nan', pd.NA)
        
        return df
    
    @staticmethod
    def _find_column(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """
        Tìm tên cột trong DataFrame dựa trên danh sách các tên có thể.
        
        Args:
            df (pd.DataFrame): DataFrame cần tìm.
            possible_names (List[str]): Danh sách các tên cột có thể.
        
        Returns:
            Optional[str]: Tên cột tìm thấy hoặc None.
        """
        for name in possible_names:
            if name in df.columns:
                return name
        return None
    
    @classmethod
    def load_courses(cls, file_path: str) -> List[Course]:
        """
        Đọc danh sách môn học từ file Excel/CSV.
        
        Args:
            file_path (str): Đường dẫn đến file chứa danh sách môn học.
        
        Returns:
            List[Course]: Danh sách các đối tượng Course.
        
        Raises:
            FileNotFoundError: Nếu file không tồn tại.
            Exception: Nếu có lỗi khi xử lý dữ liệu.
        
        Example:
            >>> loader = DataLoader()
            >>> courses = loader.load_courses('data/input/subjects.xlsx')
            >>> print(f"Đã load {len(courses)} môn học")
        """
        try:
            # Đọc file
            df = cls._read_file(file_path)
            df = cls._clean_dataframe(df)
            
            logger.info(f"Số dòng dữ liệu: {len(df)}")
            logger.info(f"Các cột: {df.columns.tolist()}")
            
            # Tìm các cột cần thiết
            column_map = {}
            
            # Xử lý từng cột một cách riêng biệt để tìm tất cả alias
            course_id_col = cls._find_column(df, ['Mã LHP', 'Ma LHP'])
            name_col = cls._find_column(df, ['Tên HP', 'Ten HP', 'Tên môn', 'Ten mon'])
            location_col = cls._find_column(df, ['Địa điểm', 'Dia diem', 'Cơ sở', 'Co so'])
            exam_format_col = cls._find_column(df, ['Hình thức thi', 'Hinh thuc thi', 'Hình thức'])
            
            # Optional columns
            note_col = cls._find_column(df, ['Ghi chú', 'Ghi chu', 'Note', 'Ghi chép'])
            student_count_col = cls._find_column(df, ['Số lượng ĐK', 'So luong DK', 'Số lượng SV', 'So luong SV', 'SL ĐK', 'SL DK'])
            duration_col = cls._find_column(df, ['Thời lượng', 'Thoi luong', 'Duration', 'Số phút', 'So phut'])
            is_locked_col = cls._find_column(df, ['Cố định', 'Co dinh', 'Locked', 'Khóa', 'Khoa'])
            
            # Kiểm tra các cột bắt buộc
            if not all([course_id_col, name_col, location_col, exam_format_col]):
                raise ValueError(
                    f"Thiếu các cột bắt buộc. "
                    f"Các cột hiện có: {df.columns.tolist()}"
                )
            
            
            # Kiểm tra xem có cột số lượng sinh viên không
            has_student_count = student_count_col is not None
            if not has_student_count:
                logger.warning(
                    "Không tìm thấy cột số lượng sinh viên. "
                    "Sẽ random số lượng từ 30-60 cho mỗi môn."
                )
            
            # Chuyển đổi DataFrame thành list Course objects
            courses = []
            for idx, row in df.iterrows():
                try:
                    # Chuẩn bị dữ liệu
                    course_data = {
                        'course_id': str(row[course_id_col]) if course_id_col else '',
                        'name': str(row[name_col]) if name_col else '',
                        'location': str(row[location_col]) if location_col else '',
                        'exam_format': str(row[exam_format_col]) if exam_format_col else '',
                        'note': str(row[note_col]) if note_col and pd.notna(row[note_col]) else '',
                    }
                    
                    # Xử lý student_count
                    if has_student_count and pd.notna(row[student_count_col]):
                        try:
                            course_data['student_count'] = int(row[student_count_col])
                        except (ValueError, TypeError):
                            course_data['student_count'] = 0
                    else:
                        course_data['student_count'] = 0
                    
                    # Random số lượng sinh viên nếu không có
                    if course_data['student_count'] == 0:
                        course_data['student_count'] = random.randint(30, 60)
                    
                    # ENHANCED: Xử lý duration
                    duration = 90  # Mặc định
                    if duration_col and pd.notna(row[duration_col]):
                        try:
                            duration = int(row[duration_col])
                        except (ValueError, TypeError):
                            duration = 90
                    course_data['duration'] = duration
                    
                    # ENHANCED: Xử lý is_locked
                    is_locked = False  # Mặc định
                    if is_locked_col and pd.notna(row[is_locked_col]):
                        value = str(row[is_locked_col]).strip().lower()
                        # Kiểm tra các giá trị: "yes", "true", "x", "1", "có", "đúng"
                        is_locked = value in ['yes', 'true', 'x', '1', 'có', 'đúng', 'locked']
                    course_data['is_locked'] = is_locked
                    
                    # Nếu is_locked=True, kiểm tra xem có sẵn lịch không
                    if is_locked:
                        # Tìm các cột ngày/giờ/phòng nếu có
                        assigned_date_col = cls._find_column(df, ['Ngày thi', 'Ngay thi', 'Date', 'Assigned Date'])
                        assigned_time_col = cls._find_column(df, ['Giờ thi', 'Gio thi', 'Time', 'Assigned Time'])
                        assigned_room_col = cls._find_column(df, ['Phòng thi', 'Phong thi', 'Room', 'Assigned Room'])
                        
                        # Nếu có đầy đủ thông tin: gán lịch ban đầu
                        if all([assigned_date_col, assigned_time_col, assigned_room_col]):
                            if pd.notna(row[assigned_date_col]) and pd.notna(row[assigned_time_col]) and pd.notna(row[assigned_room_col]):
                                course_data['assigned_date'] = str(row[assigned_date_col]).strip()
                                course_data['assigned_time'] = str(row[assigned_time_col]).strip()
                                course_data['assigned_room'] = str(row[assigned_room_col]).strip()
                    
                    # Tạo Course object
                    course = Course(
                        course_id=course_data['course_id'],
                        name=course_data['name'],
                        location=course_data['location'],
                        exam_format=course_data['exam_format'],
                        note=course_data.get('note', ''),
                        student_count=course_data['student_count'],
                        duration=course_data.get('duration', 90),
                        is_locked=course_data.get('is_locked', False),
                        assigned_date=course_data.get('assigned_date'),
                        assigned_time=course_data.get('assigned_time'),
                        assigned_room=course_data.get('assigned_room')
                    )
                    
                    courses.append(course)
                
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý dòng {idx + 1}: {str(e)}")
                    continue
            
            logger.info(f"✅ Đã load thành công {len(courses)} môn học")
            return courses
        
        except Exception as e:
            logger.error(f"❌ Lỗi khi load courses: {str(e)}")
            raise
    
    @classmethod
    def load_rooms(cls, file_path: str) -> List[Room]:
        """
        Đọc danh sách phòng thi từ file Excel/CSV.
        
        Args:
            file_path (str): Đường dẫn đến file chứa danh sách phòng.
        
        Returns:
            List[Room]: Danh sách các đối tượng Room.
        
        Raises:
            FileNotFoundError: Nếu file không tồn tại.
            Exception: Nếu có lỗi khi xử lý dữ liệu.
        
        Example:
            >>> loader = DataLoader()
            >>> rooms = loader.load_rooms('data/input/rooms.xlsx')
            >>> print(f"Đã load {len(rooms)} phòng thi")
        """
        try:
            # Đọc file
            df = cls._read_file(file_path)
            df = cls._clean_dataframe(df)
            
            logger.info(f"Số dòng dữ liệu: {len(df)}")
            logger.info(f"Các cột: {df.columns.tolist()}")
            
            # Tìm các cột cần thiết
            column_map = {}
            for possible_names, attr_name in cls.ROOM_COLUMN_MAPPING.items():
                if isinstance(possible_names, str):
                    possible_names = [possible_names]
                
                col = cls._find_column(df, possible_names)
                if col:
                    column_map[col] = attr_name
            
            # Kiểm tra các cột bắt buộc
            required_attrs = ['room_id', 'capacity', 'location']
            missing_attrs = [
                attr for attr in required_attrs 
                if attr not in column_map.values()
            ]
            
            if missing_attrs:
                raise ValueError(
                    f"Thiếu các cột bắt buộc trong file: {missing_attrs}. "
                    f"Các cột hiện có: {df.columns.tolist()}"
                )
            
            # Chuyển đổi DataFrame thành list Room objects
            rooms = []
            for idx, row in df.iterrows():
                try:
                    # Chuẩn bị dữ liệu
                    room_data = {}
                    
                    for col, attr in column_map.items():
                        value = row[col]
                        
                        # Xử lý giá trị thiếu
                        if pd.isna(value):
                            logger.warning(
                                f"Dòng {idx + 1}: Thiếu giá trị cho cột '{col}'"
                            )
                            if attr == 'capacity':
                                value = 30  # Giá trị mặc định
                            else:
                                value = ""
                        
                        room_data[attr] = value
                    
                    # Đảm bảo capacity là integer
                    room_data['capacity'] = int(room_data.get('capacity', 30))
                    
                    # Tạo Room object
                    room = Room(
                        room_id=str(room_data.get('room_id', '')),
                        capacity=room_data['capacity'],
                        location=str(room_data.get('location', ''))
                    )
                    
                    rooms.append(room)
                
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý dòng {idx + 1}: {str(e)}")
                    continue
            
            logger.info(f"✅ Đã load thành công {len(rooms)} phòng thi")
            return rooms
        
        except Exception as e:
            logger.error(f"❌ Lỗi khi load rooms: {str(e)}")
            raise
    
    @classmethod
    def load_proctors(cls, file_path: str) -> List[Proctor]:
        """
        Đọc danh sách giám thị từ file Excel/CSV.
        
        Args:
            file_path (str): Đường dẫn đến file chứa danh sách giám thị.
        
        Returns:
            List[Proctor]: Danh sách các đối tượng Proctor.
        
        Raises:
            FileNotFoundError: Nếu file không tồn tại.
            Exception: Nếu có lỗi khi xử lý dữ liệu.
        
        Example:
            >>> loader = DataLoader()
            >>> proctors = loader.load_proctors('data/input/proctors.xlsx')
            >>> print(f"Đã load {len(proctors)} giám thị")
        """
        try:
            # Đọc file
            df = cls._read_file(file_path)
            df = cls._clean_dataframe(df)
            
            logger.info(f"Số dòng dữ liệu: {len(df)}")
            logger.info(f"Các cột: {df.columns.tolist()}")
            
            # Tìm các cột cần thiết
            column_map = {}
            for possible_names, attr_name in cls.PROCTOR_COLUMN_MAPPING.items():
                if isinstance(possible_names, str):
                    possible_names = [possible_names]
                
                col = cls._find_column(df, possible_names)
                if col:
                    column_map[col] = attr_name
            
            # Kiểm tra các cột bắt buộc
            required_attrs = ['proctor_id', 'name']
            missing_attrs = [
                attr for attr in required_attrs 
                if attr not in column_map.values()
            ]
            
            if missing_attrs:
                raise ValueError(
                    f"Thiếu các cột bắt buộc trong file: {missing_attrs}. "
                    f"Các cột hiện có: {df.columns.tolist()}"
                )
            
            # Chuyển đổi DataFrame thành list Proctor objects
            proctors = []
            for idx, row in df.iterrows():
                try:
                    # Chuẩn bị dữ liệu
                    proctor_data = {}
                    
                    for col, attr in column_map.items():
                        value = row[col]
                        
                        # Xử lý giá trị thiếu
                        if pd.isna(value):
                            if attr == 'location':
                                value = None  # location là optional
                            else:
                                logger.warning(
                                    f"Dòng {idx + 1}: Thiếu giá trị cho cột '{col}'"
                                )
                                value = ""
                        
                        proctor_data[attr] = value
                    
                    # Tạo Proctor object
                    proctor = Proctor(
                        proctor_id=str(proctor_data.get('proctor_id', '')),
                        name=str(proctor_data.get('name', '')),
                        location=str(proctor_data.get('location', '')) if proctor_data.get('location') else None
                    )
                    
                    proctors.append(proctor)
                
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý dòng {idx + 1}: {str(e)}")
                    continue
            
            logger.info(f"✅ Đã load thành công {len(proctors)} giám thị")
            return proctors
        
        except Exception as e:
            logger.error(f"❌ Lỗi khi load proctors: {str(e)}")
            raise

