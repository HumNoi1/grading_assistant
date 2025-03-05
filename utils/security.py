# grading_assistant/utils/security.py
import os
import re
import hashlib
import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

# ข้อมูลความลับสำหรับสร้าง JWT token
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

def validate_email(email):
    """
    ตรวจสอบรูปแบบอีเมล
    
    Args:
        email (str): อีเมลที่ต้องการตรวจสอบ
        
    Returns:
        bool: True ถ้าอีเมลถูกต้อง, False ถ้าไม่ถูกต้อง
    """
    # รูปแบบพื้นฐานของอีเมล
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    """
    ตรวจสอบความแข็งแรงของรหัสผ่าน
    
    Args:
        password (str): รหัสผ่านที่ต้องการตรวจสอบ
        
    Returns:
        tuple: (bool, str) - ผลการตรวจสอบและข้อความ
    """
    # ตรวจสอบความยาว
    if len(password) < 8:
        return False, "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร"
    
    # ตรวจสอบว่ามีตัวเลขหรือไม่
    if not any(char.isdigit() for char in password):
        return False, "รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว"
    
    # ตรวจสอบว่ามีตัวอักษรพิมพ์ใหญ่หรือไม่
    if not any(char.isupper() for char in password):
        return False, "รหัสผ่านต้องมีตัวอักษรพิมพ์ใหญ่อย่างน้อย 1 ตัว"
    
    # ตรวจสอบว่ามีตัวอักษรพิมพ์เล็กหรือไม่
    if not any(char.islower() for char in password):
        return False, "รหัสผ่านต้องมีตัวอักษรพิมพ์เล็กอย่างน้อย 1 ตัว"
    
    return True, "รหัสผ่านมีความแข็งแรงเพียงพอ"

def hash_password(password, salt=None):
    """
    แฮชรหัสผ่านด้วย SHA-256
    
    Args:
        password (str): รหัสผ่านที่ต้องการแฮช
        salt (str, optional): salt สำหรับการแฮช
        
    Returns:
        tuple: (hashed_password, salt)
    """
    if salt is None:
        # สร้าง salt ใหม่
        salt = os.urandom(32).hex()
    
    # แฮชรหัสผ่านพร้อม salt
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    
    return hashed, salt

def verify_password(password, hashed_password, salt):
    """
    ตรวจสอบว่ารหัสผ่านถูกต้องหรือไม่
    
    Args:
        password (str): รหัสผ่านที่ต้องการตรวจสอบ
        hashed_password (str): รหัสผ่านที่แฮชแล้ว
        salt (str): salt ที่ใช้ในการแฮช
        
    Returns:
        bool: True ถ้ารหัสผ่านถูกต้อง, False ถ้าไม่ถูกต้อง
    """
    # แฮชรหัสผ่านด้วย salt เดิม
    hashed, _ = hash_password(password, salt)
    
    return hashed == hashed_password

def generate_token(user_id, email, role="teacher"):
    """
    สร้าง JWT token
    
    Args:
        user_id (str): ID ของผู้ใช้
        email (str): อีเมลของผู้ใช้
        role (str, optional): บทบาทของผู้ใช้
        
    Returns:
        str: JWT token
    """
    # กำหนดเวลาหมดอายุ
    expire_time = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    
    # สร้าง payload
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": expire_time
    }
    
    # สร้าง token
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    return token

def verify_token(token):
    """
    ตรวจสอบ JWT token
    
    Args:
        token (str): JWT token ที่ต้องการตรวจสอบ
        
    Returns:
        dict: ข้อมูลใน token หรือข้อความข้อผิดพลาด
    """
    try:
        # ถอดรหัส token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        return {"success": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"error": "Token หมดอายุ"}
    except jwt.InvalidTokenError:
        return {"error": "Token ไม่ถูกต้อง"}

def sanitize_input(input_str):
    """
    ทำความสะอาดข้อมูลที่รับเข้ามา
    
    Args:
        input_str (str): ข้อความที่ต้องการทำความสะอาด
        
    Returns:
        str: ข้อความที่ทำความสะอาดแล้ว
    """
    if not input_str:
        return input_str
    
    # ลบ HTML tags
    clean_str = re.sub(r'<[^>]*>', '', input_str)
    
    # ป้องกัน XSS
    clean_str = clean_str.replace('&', '&amp;')
    clean_str = clean_str.replace('<', '&lt;')
    clean_str = clean_str.replace('>', '&gt;')
    clean_str = clean_str.replace('"', '&quot;')
    clean_str = clean_str.replace("'", '&#x27;')
    
    return clean_str