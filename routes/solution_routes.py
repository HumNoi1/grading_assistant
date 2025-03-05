# grading_assistant/routes/solution_routes.py
from flask import Blueprint, request, jsonify, g
from models.database import SolutionModel, AssignmentModel
from services.auth_service import login_required
from services.storage_service import StorageService
from services.embedding_service import EmbeddingService
from models.database import supabase

bp = Blueprint('solutions', __name__, url_prefix='/api/solutions')
solution_model = SolutionModel()
assignment_model = AssignmentModel()
storage_service = StorageService(supabase)
embedding_service = EmbeddingService()

@bp.route('/', methods=['GET'])
@login_required
def get_solutions():
    """
    ดึงข้อมูลเฉลยทั้งหมดของผู้ใช้
    """
    assignment_id = request.args.get('assignment_id')
    
    if assignment_id:
        result = solution_model.get_by_assignment(assignment_id, g.user_id)
    else:
        result = solution_model.get_all(g.user_id)
        
    return jsonify(result.data)

@bp.route('/<solution_id>', methods=['GET'])
@login_required
def get_solution(solution_id):
    """
    ดึงข้อมูลเฉลยตาม ID
    """
    result = solution_model.get_by_id(solution_id)
    if not result.data:
        return jsonify({"error": "ไม่พบเฉลย"}), 404
    return jsonify(result.data[0])

@bp.route('/', methods=['POST'])
@login_required
def create_solution():
    """
    อัปโหลดเฉลย
    """
    assignment_id = request.form.get('assignment_id')
    
    if not assignment_id:
        return jsonify({"error": "กรุณาระบุงานที่ต้องการอัปโหลดเฉลย"}), 400
    
    # ตรวจสอบว่างานนี้เป็นของผู้ใช้หรือไม่
    assignment_result = assignment_model.get_by_id(assignment_id)
    if not assignment_result.data:
        return jsonify({"error": "ไม่พบงานที่ต้องการ"}), 404
    
    if assignment_result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์อัปโหลดเฉลยในงานนี้"}), 403
    
    # ตรวจสอบว่ามีไฟล์หรือไม่
    if 'file' not in request.files:
        return jsonify({"error": "ไม่พบไฟล์"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "ไม่ได้เลือกไฟล์"}), 400
    
    # อัปโหลดไฟล์
    folder_path = assignment_result.data[0].get('folder_path', 'solutions')
    upload_result = storage_service.upload_file(file, f"{folder_path}/solutions", g.user_id)
    
    if "error" in upload_result:
        return jsonify(upload_result), 500
    
    # ดึงข้อความจากไฟล์
    file_data = storage_service.download_file(upload_result['path'])
    content_text = storage_service.extract_text_from_file(file_data, upload_result['type'])
    
    # สร้างข้อมูลเฉลย
    solution_data = {
        "file_path": upload_result['path'],
        "file_name": upload_result['name'],
        "content_type": upload_result['type'],
        "file_size": upload_result['size'],
        "content_text": content_text,
        "user_id": g.user_id,
        "assignment_id": assignment_id
    }
    
    # บันทึกเฉลยลงฐานข้อมูล
    result = solution_model.create(solution_data)
    solution_id = result.data[0]['id']
    
    # สร้างและบันทึก embedding ของเฉลย
    if content_text:
        vector_id = embedding_service.store_solution_embedding(
            solution_id,
            content_text,
            {
                "assignment_id": assignment_id,
                "file_name": upload_result['name']
            }
        )
        
        # อัปเดต vector_id ในฐานข้อมูล
        solution_model.update(solution_id, {"vector_id": vector_id})
    
    return jsonify(result.data[0]), 201

@bp.route('/<solution_id>', methods=['DELETE'])
@login_required
def delete_solution(solution_id):
    """
    ลบเฉลย
    """
    # ตรวจสอบว่าเฉลยนี้เป็นของผู้ใช้หรือไม่
    result = solution_model.get_by_id(solution_id)
    if not result.data:
        return jsonify({"error": "ไม่พบเฉลย"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์ลบเฉลยนี้"}), 403
    
    # ลบไฟล์ที่เก็บไว้ (ถ้ามี)
    file_path = result.data[0].get('file_path')
    if file_path:
        storage_service.delete_file(file_path)
    
    # ลบ vector embedding (ถ้ามี)
    vector_id = result.data[0].get('vector_id')
    if vector_id:
        embedding_service.vector_db.delete_embedding(vector_id)
    
    solution_model.delete(solution_id)
    return jsonify({"message": "ลบเฉลยสำเร็จ"})