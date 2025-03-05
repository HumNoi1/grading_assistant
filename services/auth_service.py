# grading_assistant/services/auth_service.py
import os
import jwt
from functools import wraps
from flask import request, jsonify, g
from models.database import supabase
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

# ข้อมูลความลับสำหรับสร้าง JWT token
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

class AuthService:
    """
    คลาสสำหรับการจัดการการยืนยันตัวตน
    """
    def __init__(self):
        self.supabase = supabase
    
    def signup(self, email, password, name):
        """
        ลงทะเบียนผู้ใช้ใหม่
        
        Args:
            email (str): อีเมลของผู้ใช้
            password (str): รหัสผ่านของผู้ใช้
            name (str): ชื่อของผู้ใช้
            
        Returns:
            dict: ข้อมูลผู้ใช้ที่ลงทะเบียน
        """
        try:
            # ลงทะเบียนผู้ใช้ใน Supabase Auth
            res = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            user_id = res.user.id
            
            # สร้างข้อมูลผู้ใช้ในตาราง users
            user_data = {
                "id": user_id,
                "name": name,
                "email": email,
                "role": "teacher"  # เริ่มต้นให้เป็นอาจารย์
            }
            
            self.supabase.table("users").insert(user_data).execute()
            
            return {
                "success": True,
                "user": {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "role": "teacher"
                }
            }
        except Exception as e:
            return {"error": f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}"}
    
    def login(self, email, password):
        """
        เข้าสู่ระบบ
        
        Args:
            email (str): อีเมลของผู้ใช้
            password (str): รหัสผ่านของผู้ใช้
            
        Returns:
            dict: ข้อมูลการเข้าสู่ระบบ
        """
        try:
            # เข้าสู่ระบบผ่าน Supabase Auth
            res = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # ดึงข้อมูลผู้ใช้จากตาราง users
            user_id = res.user.id
            user_data = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not user_data.data:
                return {"error": "ไม่พบข้อมูลผู้ใช้"}
            
            user = user_data.data[0]
            
            # สร้าง JWT token
            token = jwt.encode({
                "user_id": user_id,
                "email": email,
                "role": user["role"]
            }, JWT_SECRET, algorithm="HS256")
            
            return {
                "success": True,
                "token": token,
                "user": {
                    "id": user_id,
                    "name": user["name"],
                    "email": email,
                    "role": user["role"]
                }
            }
        except Exception as e:
            return {"error": f"เกิดข้อผิดพลาดในการเข้าสู่ระบบ: {str(e)}"}
    
    def logout(self):
        """
        ออกจากระบบ
        
        Returns:
            dict: สถานะการออกจากระบบ
        """
        try:
            self.supabase.auth.sign_out()
            return {"success": True, "message": "ออกจากระบบสำเร็จ"}
        except Exception as e:
            return {"error": f"เกิดข้อผิดพลาดในการออกจากระบบ: {str(e)}"}

# Decorator สำหรับการตรวจสอบการยืนยันตัวตน
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "ไม่มีการยืนยันตัวตน"}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # ตรวจสอบ JWT token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            g.user_id = payload["user_id"]
            g.user_email = payload["email"]
            g.user_role = payload["role"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "หมดเวลาการเข้าสู่ระบบ"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token ไม่ถูกต้อง"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function