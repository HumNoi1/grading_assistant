# grading_assistant/routes/semester_routes.py
from flask import Blueprint, request, jsonify, g
from models.database import SemesterModel
from services.auth_service import login_required

bp = Blueprint('semesters', __name__, url_prefix='/api/semesters')
semester_model = SemesterModel()

@bp.route('/', methods=['GET'])
@login_required
def get_semesters():
    """
    ดึงข้อมูลเทอมเรียนทั้งหมดของผู้ใช้
    """
    result = semester_model.get_all(g.user_id)
    return jsonify(result.data)

@bp.route('/<semester_id>', methods=['GET'])
@login_required
def get_semester(semester_id):
    """
    ดึงข้อมูลเทอมเรียนตาม ID
    """
    result = semester_model.get_by_id(semester_id)
    if not result.data:
        return jsonify({"error": "ไม่พบเทอมเรียน"}), 404
    return jsonify(result.data[0])

@bp.route('/', methods=['POST'])
@login_required
def create_semester():
    """
    สร้างเทอมเรียนใหม่
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # เพิ่ม user_id ลงในข้อมูล
    data['user_id'] = g.user_id
    
    # ตรวจสอบข้อมูลที่จำเป็น
    if 'name' not in data or 'year' not in data:
        return jsonify({"error": "กรุณากรอกชื่อเทอมและปีการศึกษา"}), 400
    
    result = semester_model.create(data)
    return jsonify(result.data[0]), 201

@bp.route('/<semester_id>', methods=['PUT'])
@login_required
def update_semester(semester_id):
    """
    อัปเดตข้อมูลเทอมเรียน
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบว่าเทอมนี้เป็นของผู้ใช้หรือไม่
    result = semester_model.get_by_id(semester_id)
    if not result.data:
        return jsonify({"error": "ไม่พบเทอมเรียน"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์แก้ไขเทอมเรียนนี้"}), 403
    
    result = semester_model.update(semester_id, data)
    return jsonify(result.data[0])

@bp.route('/<semester_id>', methods=['DELETE'])
@login_required
def delete_semester(semester_id):
    """
    ลบเทอมเรียน
    """
    # ตรวจสอบว่าเทอมนี้เป็นของผู้ใช้หรือไม่
    result = semester_model.get_by_id(semester_id)
    if not result.data:
        return jsonify({"error": "ไม่พบเทอมเรียน"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์ลบเทอมเรียนนี้"}), 403
    
    semester_model.delete(semester_id)
    return jsonify({"message": "ลบเทอมเรียนสำเร็จ"})

@bp.route('/with-classes', methods=['GET'])
@login_required
def get_semesters_with_classes():
    """
    ดึงข้อมูลเทอมเรียนพร้อมกับชั้นเรียนที่เกี่ยวข้อง
    """
    result = semester_model.get_with_classes(g.user_id)
    return jsonify(result.data)