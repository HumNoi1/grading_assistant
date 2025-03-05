# grading_assistant/routes/grade_routes.py
from flask import Blueprint, request, jsonify, g
from models.database import GradeModel, SubmissionModel
from services.auth_service import login_required

bp = Blueprint('grades', __name__, url_prefix='/api/grades')
grade_model = GradeModel()
submission_model = SubmissionModel()

@bp.route('/', methods=['GET'])
@login_required
def get_grades():
    """
    ดึงข้อมูลคะแนนทั้งหมดของผู้ใช้
    """
    submission_id = request.args.get('submission_id')
    
    if submission_id:
        result = grade_model.get_by_submission(submission_id, g.user_id)
    else:
        result = grade_model.get_all(g.user_id)
        
    return jsonify(result.data)

@bp.route('/<grade_id>', methods=['GET'])
@login_required
def get_grade(grade_id):
    """
    ดึงข้อมูลคะแนนตาม ID
    """
    result = grade_model.get_by_id(grade_id)
    if not result.data:
        return jsonify({"error": "ไม่พบคะแนนที่ต้องการ"}), 404
    return jsonify(result.data[0])

@bp.route('/', methods=['POST'])
@login_required
def create_grade():
    """
    สร้างคะแนนใหม่ (กรณีที่อาจารย์ตรวจคะแนนเอง)
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบข้อมูลที่จำเป็น
    if 'submission_id' not in data or 'score' not in data:
        return jsonify({"error": "กรุณากรอกรหัสการส่งงานและคะแนน"}), 400
    
    # ตรวจสอบว่างานที่ส่งนี้เป็นของผู้ใช้หรือไม่
    submission_result = submission_model.get_by_id(data['submission_id'])
    if not submission_result.data:
        return jsonify({"error": "ไม่พบงานที่ส่ง"}), 404
    
    if submission_result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์ให้คะแนนงานนี้"}), 403
    
    # เพิ่ม user_id ลงในข้อมูล
    data['user_id'] = g.user_id
    
    # แปลงคะแนนเป็นตัวเลข
    try:
        data['score'] = float(data['score'])
    except ValueError:
        data['score'] = 0
    
    # ถ้ามีการอนุมัติ ตั้งค่าให้เป็น True
    data['approved'] = data.get('approved', True)
    
    result = grade_model.create(data)
    
    # อัปเดตสถานะการส่งงาน
    status = "approved" if data['approved'] else "graded"
    submission_model.update(data['submission_id'], {"status": status})
    
    return jsonify(result.data[0]), 201

@bp.route('/<grade_id>', methods=['PUT'])
@login_required
def update_grade(grade_id):
    """
    อัปเดตข้อมูลคะแนน
    """
    data = request.json
    if not data:
        return jsonify({"error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    # ตรวจสอบว่าคะแนนนี้เป็นของผู้ใช้หรือไม่
    result = grade_model.get_by_id(grade_id)
    if not result.data:
        return jsonify({"error": "ไม่พบคะแนนที่ต้องการ"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์แก้ไขคะแนนนี้"}), 403
    
    # แปลงคะแนนเป็นตัวเลข
    if 'score' in data:
        try:
            data['score'] = float(data['score'])
        except ValueError:
            data['score'] = 0
    
    result = grade_model.update(grade_id, data)
    
    # ถ้ามีการอนุมัติคะแนน ให้อัปเดตสถานะของการส่งงานเป็น 'approved'
    if data.get('approved') == True:
        submission_id = result.data[0]['submission_id']
        submission_model.update(submission_id, {"status": "approved"})
    
    return jsonify(result.data[0])

@bp.route('/<grade_id>', methods=['DELETE'])
@login_required
def delete_grade(grade_id):
    """
    ลบคะแนน
    """
    # ตรวจสอบว่าคะแนนนี้เป็นของผู้ใช้หรือไม่
    result = grade_model.get_by_id(grade_id)
    if not result.data:
        return jsonify({"error": "ไม่พบคะแนนที่ต้องการ"}), 404
    
    if result.data[0]['user_id'] != g.user_id:
        return jsonify({"error": "ไม่มีสิทธิ์ลบคะแนนนี้"}), 403
    
    # ดึงข้อมูลการส่งงานที่เกี่ยวข้อง
    submission_id = result.data[0]['submission_id']
    
    grade_model.delete(grade_id)
    
    # อัปเดตสถานะของการส่งงานกลับเป็น 'pending'
    submission_model.update(submission_id, {"status": "pending"})
    
    return jsonify({"message": "ลบคะแนนสำเร็จ"})

@bp.route('/statistics', methods=['GET'])
@login_required
def get_grade_statistics():
    """
    ดึงสถิติคะแนนตามงานหรือตามนักเรียน
    """
    assignment_id = request.args.get('assignment_id')
    student_id = request.args.get('student_id')
    
    if not assignment_id and not student_id:
        return jsonify({"error": "กรุณาระบุรหัสงานหรือรหัสนักเรียน"}), 400
    
    # ข้อมูลสำหรับส่งกลับ
    statistics = {
        "avg_score": 0,
        "max_score": 0,
        "min_score": 0,
        "total_submissions": 0,
        "graded_submissions": 0,
        "approved_submissions": 0
    }
    
    # ดึงข้อมูลการส่งงานตามงานหรือตามนักเรียน
    submissions_query = submission_model.client.table("submissions").select("*").eq("user_id", g.user_id)
    
    if assignment_id:
        submissions_query = submissions_query.eq("assignment_id", assignment_id)
    
    submissions_result = submissions_query.execute()
    
    if not submissions_result.data:
        return jsonify(statistics)
    
    # จำนวนการส่งงานทั้งหมด
    statistics["total_submissions"] = len(submissions_result.data)
    
    # จำนวนการส่งงานที่ตรวจแล้ว
    graded_submissions = [s for s in submissions_result.data if s["status"] in ["graded", "approved"]]
    statistics["graded_submissions"] = len(graded_submissions)
    
    # จำนวนการส่งงานที่อนุมัติแล้ว
    approved_submissions = [s for s in submissions_result.data if s["status"] == "approved"]
    statistics["approved_submissions"] = len(approved_submissions)
    
    # ดึงข้อมูลคะแนนของการส่งงานที่ตรวจแล้ว
    submission_ids = [s["id"] for s in graded_submissions]
    
    if not submission_ids:
        return jsonify(statistics)
    
    grades_result = grade_model.client.table("grades").select("*").in_("submission_id", submission_ids).execute()
    
    if not grades_result.data:
        return jsonify(statistics)
    
    # คำนวณสถิติคะแนน
    scores = [g["score"] for g in grades_result.data]
    
    if scores:
        statistics["avg_score"] = sum(scores) / len(scores)
        statistics["max_score"] = max(scores)
        statistics["min_score"] = min(scores)
    
    return jsonify(statistics)