# grading_assistant/routes/assignment_routes.py
from flask import Blueprint, request, jsonify, g
from models.database import AssignmentModel, SubjectModel
from services.auth_service import login_required
from services.storage_service import StorageService
from models.database import supabase
import uuid

bp = Blueprint('assignments', __name__, url_prefix='/api/assignments')
assignment_model = AssignmentModel()
subject_model = SubjectModel()
storage_service = StorageService(supabase)

@bp.route('/', methods=['GET'])
@login_required
def get_assignments():
    """
    ดึงข้อมูลงานทั้งหมดของผู้ใช้
    """
    subject_id = request.args.get('subject_id')
    
    if subject_id:
        result = assignment_model.get_by_subject(subject_id, g.user_id)
    else:
        result = assignment_model.get_all(g.user_id)
        
    return jsonify(result.data)

@bp.route('/<assignment_id>', methods=['GET'])
@login_required
def get_assignment(assignment_id):
    """
    ดึงข้อมูลงานตาม ID
    """
    result = assignment_model.get_by_id(assignment_id)
    if not result.data:
        return jsonify({"error": "ไม่พบงานที่ต้องการ"}), 404
    return jsonify(result.data[0])

@bp.route('/', methods=['POST'])
@login_required
def create_assignment():
    """
    สร้างงานใหม่
    """
    data = request.form.to_dict()
    
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบข้อมูลที่จำเป็น
    if 'title' not in data or 'subject_id' not in data:
        return jsonify({"error": "กรุณากรอกชื่องานและรหัสวิชา"}), 400
    
    # ตรวจสอบว่าวิชานี้เป็นของผู้ใช้หรือไม่
    subject_result = subject_model.get_by_id(data['subject_id'])
    if not subject_result.data:
        return jsonify({"error": "ไม่พบวิชาที่ต้องการ"}), 404
    
    if subject_result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์สร้างงานในวิชานี้"}), 403
    
    # สร้างโฟลเดอร์สำหรับเก็บไฟล์งาน
    folder_name = f"assignments/{uuid.uuid4()}"
    folder_result = storage_service.create_folder(folder_name)
    
    if "error" in folder_result:
        return jsonify(folder_result), 500
    
    # เพิ่มข้อมูลพื้นฐาน
    data['user_id'] = g.user_id
    data['folder_path'] = folder_name
    
    # แปลงคะแนนเป็นตัวเลข
    if 'total_score' in data:
        try:
            data['total_score'] = float(data['total_score'])
        except ValueError:
            data['total_score'] = 0
    
    result = assignment_model.create(data)
    return jsonify(result.data[0]), 201

@bp.route('/<assignment_id>', methods=['PUT'])
@login_required
def update_assignment(assignment_id):
    """
    อัปเดตข้อมูลงาน
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบว่างานนี้เป็นของผู้ใช้หรือไม่
    result = assignment_model.get_by_id(assignment_id)
    if not result.data:
        return jsonify({"error": "ไม่พบงานที่ต้องการ"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์แก้ไขงานนี้"}), 403
    
    # แปลงคะแนนเป็นตัวเลข
    if 'total_score' in data:
        try:
            data['total_score'] = float(data['total_score'])
        except ValueError:
            data['total_score'] = 0
    
    result = assignment_model.update(assignment_id, data)
    return jsonify(result.data[0])

@bp.route('/<assignment_id>', methods=['DELETE'])
@login_required
def delete_assignment(assignment_id):
    """
    ลบงาน
    """
    # ตรวจสอบว่างานนี้เป็นของผู้ใช้หรือไม่
    result = assignment_model.get_by_id(assignment_id)
    if not result.data:
        return jsonify({"error": "ไม่พบงานที่ต้องการ"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์ลบงานนี้"}), 403
    
    # ลบโฟลเดอร์ที่เก็บไฟล์งาน (หากมี)
    folder_path = result.data[0].get('folder_path')
    if folder_path:
        # หมายเหตุ: การลบโฟลเดอร์ใน Supabase จะต้องลบไฟล์ทั้งหมดในโฟลเดอร์ก่อน
        # ตรงนี้ควรมีการลบไฟล์ทั้งหมดในโฟลเดอร์ แต่เพื่อความเรียบง่ายจะไม่ทำในตัวอย่างนี้
        pass
    
    assignment_model.delete(assignment_id)
    return jsonify({"message": "ลบงานสำเร็จ"})