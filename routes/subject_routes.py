# grading_assistant/routes/subject_routes.py
from flask import Blueprint, request, jsonify, g
from models.database import SubjectModel, ClassModel
from services.auth_service import login_required

bp = Blueprint('subjects', __name__, url_prefix='/api/subjects')
subject_model = SubjectModel()
class_model = ClassModel()

@bp.route('/', methods=['GET'])
@login_required
def get_subjects():
    """
    ดึงข้อมูลวิชาทั้งหมดของผู้ใช้
    """
    class_id = request.args.get('class_id')
    
    if class_id:
        result = subject_model.get_by_class(class_id, g.user_id)
    else:
        result = subject_model.get_all(g.user_id)
        
    return jsonify(result.data)

@bp.route('/<subject_id>', methods=['GET'])
@login_required
def get_subject(subject_id):
    """
    ดึงข้อมูลวิชาตาม ID
    """
    result = subject_model.get_by_id(subject_id)
    if not result.data:
        return jsonify({"error": "ไม่พบวิชา"}), 404
    return jsonify(result.data[0])

@bp.route('/', methods=['POST'])
@login_required
def create_subject():
    """
    สร้างวิชาใหม่
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบข้อมูลที่จำเป็น
    if 'name' not in data or 'class_id' not in data:
        return jsonify({"error": "กรุณากรอกชื่อวิชาและชั้นเรียน"}), 400
    
    # ตรวจสอบว่าชั้นเรียนนี้เป็นของผู้ใช้หรือไม่
    class_result = class_model.get_by_id(data['class_id'])
    if not class_result.data:
        return jsonify({"error": "ไม่พบชั้นเรียน"}), 404
    
    if class_result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์สร้างวิชาในชั้นเรียนนี้"}), 403
    
    # เพิ่ม user_id ลงในข้อมูล
    data['user_id'] = g.user_id
    
    result = subject_model.create(data)
    return jsonify(result.data[0]), 201

@bp.route('/<subject_id>', methods=['PUT'])
@login_required
def update_subject(subject_id):
    """
    อัปเดตข้อมูลวิชา
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบว่าวิชานี้เป็นของผู้ใช้หรือไม่
    result = subject_model.get_by_id(subject_id)
    if not result.data:
        return jsonify({"error": "ไม่พบวิชา"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์แก้ไขวิชานี้"}), 403
    
    # ถ้ามีการเปลี่ยนชั้นเรียน ตรวจสอบว่าชั้นเรียนใหม่เป็นของผู้ใช้หรือไม่
    if 'class_id' in data and data['class_id'] != result.data[0]['class_id']:
        class_result = class_model.get_by_id(data['class_id'])
        if not class_result.data:
            return jsonify({"error": "ไม่พบชั้นเรียน"}), 404
        
        if class_result.data[0]['user_id'] != g.user_id:
            return jsonify({"error": "ไม่มีสิทธิ์ย้ายวิชาไปยังชั้นเรียนนี้"}), 403
    
    result = subject_model.update(subject_id, data)
    return jsonify(result.data[0])

@bp.route('/<subject_id>', methods=['DELETE'])
@login_required
def delete_subject(subject_id):
    """
    ลบวิชา
    """
    # ตรวจสอบว่าวิชานี้เป็นของผู้ใช้หรือไม่
    result = subject_model.get_by_id(subject_id)
    if not result.data:
        return jsonify({"error": "ไม่พบวิชา"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์ลบวิชานี้"}), 403
    
    subject_model.delete(subject_id)
    return jsonify({"message": "ลบวิชาสำเร็จ"})