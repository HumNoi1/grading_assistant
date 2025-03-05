# grading_assistant/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from services.auth_service import AuthService, login_required

bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_service = AuthService()

@bp.route('/signup', methods=['POST'])
def signup():
    """
    ลงทะเบียนผู้ใช้ใหม่
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบข้อมูลที่จำเป็น
    if 'email' not in data or 'password' not in data or 'name' not in data:
        return jsonify({"error": "กรุณากรอกอีเมล รหัสผ่าน และชื่อ"}), 400
    
    result = auth_service.signup(data['email'], data['password'], data['name'])
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify(result), 201

@bp.route('/login', methods=['POST'])
def login():
    """
    เข้าสู่ระบบ
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบข้อมูลที่จำเป็น
    if 'email' not in data or 'password' not in data:
        return jsonify({"error": "กรุณากรอกอีเมลและรหัสผ่าน"}), 400
    
    result = auth_service.login(data['email'], data['password'])
    
    if "error" in result:
        return jsonify(result), 401
    
    return jsonify(result)

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    ออกจากระบบ
    """
    result = auth_service.logout()
    return jsonify(result)

@bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """
    ดึงข้อมูลโปรไฟล์ของผู้ใช้ที่เข้าสู่ระบบ
    """
    from flask import g
    from models.database import supabase
    
    # ดึงข้อมูลผู้ใช้จากฐานข้อมูล
    user_data = supabase.table("users").select("*").eq("id", g.user_id).execute()
    
    if not user_data.data:
        return jsonify({"error": "ไม่พบข้อมูลผู้ใช้"}), 404
    
    # ลบข้อมูลที่ไม่ต้องการส่งกลับ
    user = user_data.data[0]
    
    return jsonify({
        "id": user["id"],
        "name": user["name"],
        "email": g.user_email,
        "role": user["role"],
        "created_at": user["created_at"]
    })