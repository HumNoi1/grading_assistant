# grading_assistant/routes/class_routes.py
from flask import Blueprint, request, jsonify, g
from models.database import ClassModel, SemesterModel
from services.auth_service import login_required

bp = Blueprint('classes', __name__, url_prefix='/api/classes')
class_model = ClassModel()
semester_model = SemesterModel()

@bp.route('/', methods=['GET'])
@login_required
def get_classes():
    """
    ดึงข้อมูลชั้นเรียนทั้งหมดของผู้ใช้
    """
    semester_id = request.args.get('semester_id')
    
    if semester_id:
        result = class_model.get_by_semester(semester_id, g.user_id)
    else:
        result = class_model.get_all(g.user_id)
        
    return jsonify(result.data)

@bp.route('/<class_id>', methods=['GET'])
@login_required
def get_class(class_id):
    """
    ดึงข้อมูลชั้นเรียนตาม ID
    """
    result = class_model.get_by_id(class_id)
    if not result.data:
        return jsonify({"error": "ไม่พบชั้นเรียน"}), 404
    return jsonify(result.data[0])

@bp.route('/', methods=['POST'])
@login_required
def create_class():
    """
    สร้างชั้นเรียนใหม่
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบข้อมูลที่จำเป็น
    if 'name' not in data or 'semester_id' not in data:
        return jsonify({"error": "กรุณากรอกชื่อชั้นเรียนและเทอมเรียน"}), 400
    
    # ตรวจสอบว่าเทอมนี้เป็นของผู้ใช้หรือไม่
    semester_result = semester_model.get_by_id(data['semester_id'])
    if not semester_result.data:
        return jsonify({"error": "ไม่พบเทอมเรียน"}), 404
    
    if semester_result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์สร้างชั้นเรียนในเทอมนี้"}), 403
    
    # เพิ่ม user_id ลงในข้อมูล
    data['user_id'] = g.user_id
    
    result = class_model.create(data)
    return jsonify(result.data[0]), 201

@bp.route('/<class_id>', methods=['PUT'])
@login_required
def update_class(class_id):
    """
    อัปเดตข้อมูลชั้นเรียน
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบว่าชั้นเรียนนี้เป็นของผู้ใช้หรือไม่
    result = class_model.get_by_id(class_id)
    if not result.data:
        return jsonify({"error": "ไม่พบชั้นเรียน"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์แก้ไขชั้นเรียนนี้"}), 403
    
    # ถ้ามีการเปลี่ยนเทอม ตรวจสอบว่าเทอมใหม่เป็นของผู้ใช้หรือไม่
    if 'semester_id' in data and data['semester_id'] != result.data[0]['semester_id']:
        semester_result = semester_model.get_by_id(data['semester_id'])
        if not semester_result.data:
            return jsonify({"error": "ไม่พบเทอมเรียน"}), 404
        
        if semester_result.data[0]['user_id'] != g.user_id:
            return jsonify({"error": "ไม่มีสิทธิ์ย้ายชั้นเรียนไปยังเทอมนี้"}), 403
    
    result = class_model.update(class_id, data)
    return jsonify(result.data[0])

@bp.route('/<class_id>', methods=['DELETE'])
@login_required
def delete_class(class_id):
    """
    ลบชั้นเรียน
    """
    # ตรวจสอบว่าชั้นเรียนนี้เป็นของผู้ใช้หรือไม่
    result = class_model.get_by_id(class_id)
    if not result.data:
        return jsonify({"error": "ไม่พบชั้นเรียน"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์ลบชั้นเรียนนี้"}), 403
    
    class_model.delete(class_id)
    return jsonify({"message": "ลบชั้นเรียนสำเร็จ"})