# grading_assistant/routes/submission_routes.py
from flask import Blueprint, request, jsonify, g
from models.database import SubmissionModel, AssignmentModel
from services.auth_service import login_required
from services.storage_service import StorageService
from services.grading_service import GradingService
from models.database import supabase

bp = Blueprint('submissions', __name__, url_prefix='/api/submissions')
submission_model = SubmissionModel()
assignment_model = AssignmentModel()
storage_service = StorageService(supabase)
grading_service = GradingService()

@bp.route('/', methods=['GET'])
@login_required
def get_submissions():
    """
    ดึงข้อมูลงานที่นักเรียนส่งทั้งหมดของผู้ใช้
    """
    assignment_id = request.args.get('assignment_id')
    status = request.args.get('status')
    
    if assignment_id:
        result = submission_model.get_by_assignment(assignment_id, g.user_id)
    elif status == 'pending':
        result = submission_model.get_pending_submissions(g.user_id)
    else:
        result = submission_model.get_all(g.user_id)
        
    return jsonify(result.data)

@bp.route('/<submission_id>', methods=['GET'])
@login_required
def get_submission(submission_id):
    """
    ดึงข้อมูลงานที่นักเรียนส่งตาม ID
    """
    result = submission_model.get_by_id(submission_id)
    if not result.data:
        return jsonify({"error": "ไม่พบงานที่นักเรียนส่ง"}), 404
    return jsonify(result.data[0])

@bp.route('/', methods=['POST'])
@login_required
def create_submission():
    """
    อัปโหลดงานที่นักเรียนส่ง
    """
    assignment_id = request.form.get('assignment_id')
    student_name = request.form.get('student_name')
    student_id = request.form.get('student_id')
    
    if not assignment_id or not student_name or not student_id:
        return jsonify({"error": "กรุณากรอกข้อมูลให้ครบถ้วน"}), 400
    
    # ตรวจสอบว่างานนี้เป็นของผู้ใช้หรือไม่
    assignment_result = assignment_model.get_by_id(assignment_id)
    if not assignment_result.data:
        return jsonify({"error": "ไม่พบงานที่ต้องการ"}), 404
    
    if assignment_result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์อัปโหลดงานในงานนี้"}), 403
    
    # ตรวจสอบว่ามีไฟล์หรือไม่
    if 'file' not in request.files:
        return jsonify({"error": "ไม่พบไฟล์"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "ไม่ได้เลือกไฟล์"}), 400
    
    # อัปโหลดไฟล์
    folder_path = assignment_result.data[0].get('folder_path', 'submissions')
    upload_result = storage_service.upload_file(file, f"{folder_path}/submissions", g.user_id)
    
    if "error" in upload_result:
        return jsonify(upload_result), 500
    
    # ดึงข้อความจากไฟล์
    file_data = storage_service.download_file(upload_result['path'])
    content_text = storage_service.extract_text_from_file(file_data, upload_result['type'])
    
    # สร้างข้อมูลการส่งงาน
    submission_data = {
        "student_name": student_name,
        "student_id": student_id,
        "file_path": upload_result['path'],
        "file_name": upload_result['name'],
        "content_type": upload_result['type'],
        "file_size": upload_result['size'],
        "content_text": content_text,
        "status": "pending",
        "user_id": g.user_id,
        "assignment_id": assignment_id
    }
    
    result = submission_model.create(submission_data)
    return jsonify(result.data[0]), 201

@bp.route('/<submission_id>/grade', methods=['POST'])
@login_required
def grade_submission(submission_id):
    """
    ตรวจงานที่นักเรียนส่ง
    """
    # ตรวจสอบว่างานนี้เป็นของผู้ใช้หรือไม่
    result = submission_model.get_by_id(submission_id)
    if not result.data:
        return jsonify({"error": "ไม่พบงานที่นักเรียนส่ง"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์ตรวจงานนี้"}), 403
    
    # ตรวจสอบสถานะ
    if result.data[0]['status'] != 'pending':
        return jsonify({"error": "งานนี้ถูกตรวจแล้ว"}), 400
    
    # เลือกวิธีการตรวจ
    use_rag = request.args.get('use_rag', 'true').lower() == 'true'
    
    if use_rag:
        # ตรวจโดยใช้ RAG
        grading_result = grading_service.grade_with_rag(submission_id)
    else:
        # ตรวจโดยใช้ LLM โดยตรง
        grading_result = grading_service.grade_submission_with_llm(submission_id)
    
    if "error" in grading_result:
        return jsonify(grading_result), 500
    
    return jsonify(grading_result)

@bp.route('/<submission_id>', methods=['DELETE'])
@login_required
def delete_submission(submission_id):
    """
    ลบงานที่นักเรียนส่ง
    """
    # ตรวจสอบว่างานนี้เป็นของผู้ใช้หรือไม่
    result = submission_model.get_by_id(submission_id)
    if not result.data:
        return jsonify({"error": "ไม่พบงานที่นักเรียนส่ง"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์ลบงานนี้"}), 403
    
    # ลบไฟล์ที่เก็บไว้ (ถ้ามี)
    file_path = result.data[0].get('file_path')
    if file_path:
        storage_service.delete_file(file_path)
    
    submission_model.delete(submission_id)
    return jsonify({"message": "ลบงานที่นักเรียนส่งสำเร็จ"})