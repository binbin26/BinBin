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
            for possible_names, attr_name in cls.COURSE_COLUMN_MAPPING.items():
                if isinstance(possible_names, str):
                    possible_names = [possible_names]
                
                col = cls._find_column(df, possible_names)
                if col:
                    column_map[col] = attr_name
            
            # Kiểm tra các cột bắt buộc
            required_attrs = ['course_id', 'name', 'location', 'exam_format']
            missing_attrs = [
                attr for attr in required_attrs 
                if attr not in column_map.values()
            ]
            
            if missing_attrs:
                raise ValueError(
                    f"Thiếu các cột bắt buộc trong file: {missing_attrs}. "
                    f"Các cột hiện có: {df.columns.tolist()}"
                )
            
            # Kiểm tra xem có cột số lượng sinh viên không
            has_student_count = 'student_count' in column_map.values()
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
                    course_data = {}
                    
                    for col, attr in column_map.items():
                        value = row[col]
                        
                        # Xử lý giá trị thiếu
                        if pd.isna(value):
                            if attr == 'note':
                                value = ""
                            elif attr == 'student_count':
                                value = 0
                            else:
                                logger.warning(
                                    f"Dòng {idx + 1}: Thiếu giá trị cho cột '{col}'"
                                )
                                value = ""
                        
                        course_data[attr] = value
                    
                    # Random số lượng sinh viên nếu không có
                    if not has_student_count or course_data.get('student_count', 0) == 0:
                        course_data['student_count'] = random.randint(30, 60)
                    
                    # Đảm bảo student_count là integer
                    course_data['student_count'] = int(course_data.get('student_count', 0))
                    
                    # Tạo Course object
                    course = Course(
                        course_id=str(course_data.get('course_id', '')),
                        name=str(course_data.get('name', '')),
                        location=str(course_data.get('location', '')),
                        exam_format=str(course_data.get('exam_format', '')),
                        note=str(course_data.get('note', '')),
                        student_count=course_data['student_count']
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

