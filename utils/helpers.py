# grading_assistant/utils/helpers.py
import os
import json
import csv
import time
import io
from datetime import datetime

def format_date(date_str, format_str="%Y-%m-%d %H:%M:%S"):
    """
    แปลงรูปแบบวันที่
    
    Args:
        date_str (str): วันที่ในรูปแบบ ISO
        format_str (str): รูปแบบที่ต้องการแสดง
        
    Returns:
        str: วันที่ในรูปแบบที่กำหนด
    """
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime(format_str)
    except Exception:
        return date_str

def parse_json(json_str):
    """
    แปลง JSON string เป็น dict
    
    Args:
        json_str (str): JSON string
        
    Returns:
        dict: ข้อมูล JSON หรือ None ถ้าแปลงไม่ได้
    """
    try:
        return json.loads(json_str)
    except Exception:
        return None

def to_json(data):
    """
    แปลง dict เป็น JSON string
    
    Args:
        data (dict): ข้อมูลที่ต้องการแปลง
        
    Returns:
        str: JSON string
    """
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        return "{}"

def generate_csv(data, headers):
    """
    สร้างไฟล์ CSV จากข้อมูล
    
    Args:
        data (list): รายการข้อมูล
        headers (list): รายการหัวข้อ
        
    Returns:
        io.StringIO: ไฟล์ CSV ในรูปแบบ StringIO
    """
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # เขียนหัวข้อ
        writer.writerow(headers)
        
        # เขียนข้อมูล
        for row in data:
            writer.writerow([row.get(header, '') for header in headers])
        
        output.seek(0)
        return output
    except Exception:
        return io.StringIO()

def ensure_dir(directory):
    """
    สร้างไดเรกทอรีถ้ายังไม่มี
    
    Args:
        directory (str): พาธของไดเรกทอรี
        
    Returns:
        bool: True ถ้าสร้างสำเร็จหรือมีอยู่แล้ว, False ถ้าไม่สำเร็จ
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception:
        return False

def get_file_size_text(size_bytes):
    """
    แปลงขนาดไฟล์เป็นข้อความที่อ่านง่าย
    
    Args:
        size_bytes (int): ขนาดไฟล์ในหน่วยไบต์
        
    Returns:
        str: ขนาดไฟล์ในรูปแบบที่อ่านง่าย
    """
    # ตรวจสอบว่าเป็นตัวเลขหรือไม่
    if not isinstance(size_bytes, (int, float)):
        return "0 B"
    
    # แปลงขนาดไฟล์
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} PB"

def trunc_string(string, max_length=100, suffix="..."):
    """
    ตัดข้อความที่ยาวเกินไป
    
    Args:
        string (str): ข้อความที่ต้องการตัด
        max_length (int): ความยาวสูงสุดที่ต้องการ
        suffix (str): ข้อความที่ต้องการเพิ่มท้ายข้อความที่ถูกตัด
        
    Returns:
        str: ข้อความที่ถูกตัด
    """
    if not string:
        return ""
    
    if len(string) <= max_length:
        return string
    
    return string[:max_length - len(suffix)] + suffix

def generate_random_password(length=12):
    """
    สร้างรหัสผ่านแบบสุ่ม
    
    Args:
        length (int): ความยาวของรหัสผ่าน
        
    Returns:
        str: รหัสผ่านที่สร้างขึ้น
    """
    import random
    import string
    
    # สร้างรหัสผ่านแบบสุ่ม
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(chars) for _ in range(length))
    
    return password

def parse_thai_date(date_str):
    """
    แปลงวันที่ภาษาไทยเป็นวัตถุ datetime
    
    Args:
        date_str (str): วันที่ในรูปแบบภาษาไทย (เช่น "1 มกราคม 2566")
        
    Returns:
        datetime: วัตถุ datetime หรือ None ถ้าแปลงไม่ได้
    """
    # แปลงชื่อเดือนภาษาไทยเป็นตัวเลข
    thai_months = {
        'มกราคม': 1,
        'กุมภาพันธ์': 2,
        'มีนาคม': 3,
        'เมษายน': 4,
        'พฤษภาคม': 5,
        'มิถุนายน': 6,
        'กรกฎาคม': 7,
        'สิงหาคม': 8,
        'กันยายน': 9,
        'ตุลาคม': 10,
        'พฤศจิกายน': 11,
        'ธันวาคม': 12
    }
    
    try:
        parts = date_str.split()
        day = int(parts[0])
        month = thai_months.get(parts[1])
        
        # แปลงปี พ.ศ. เป็น ค.ศ.
        year = int(parts[2]) - 543
        
        return datetime(year, month, day)
    except Exception:
        return None

def calculate_percentage(value, total):
    """
    คำนวณค่าร้อยละ
    
    Args:
        value (float): ค่าที่ต้องการคำนวณร้อยละ
        total (float): ค่ารวมทั้งหมด
        
    Returns:
        float: ค่าร้อยละ
    """
    try:
        if total == 0:
            return 0
        return (value / total) * 100
    except Exception:
        return 0

def format_grade(score, total_score=100):
    """
    แปลงคะแนนเป็นเกรด
    
    Args:
        score (float): คะแนน
        total_score (float): คะแนนเต็ม
        
    Returns:
        str: เกรด
    """
    # คำนวณเปอร์เซ็นต์
    percentage = calculate_percentage(score, total_score)
    
    # แปลงเป็นเกรด
    if percentage >= 80:
        return "A"
    elif percentage >= 75:
        return "B+"
    elif percentage >= 70:
        return "B"
    elif percentage >= 65:
        return "C+"
    elif percentage >= 60:
        return "C"
    elif percentage >= 55:
        return "D+"
    elif percentage >= 50:
        return "D"
    else:
        return "F"