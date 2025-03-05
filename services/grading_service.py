# grading_assistant/services/grading_service.py
import os
import json
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from models.database import SolutionModel, SubmissionModel, GradeModel, AssignmentModel
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

class GradingService:
    """
    คลาสสำหรับระบบการตรวจข้อสอบอัตโนมัติโดยใช้ LLM และ RAG
    """
    def __init__(self):
        self.llm_service = LLMService()
        self.embedding_service = EmbeddingService()
        self.solution_model = SolutionModel()
        self.submission_model = SubmissionModel()
        self.grade_model = GradeModel()
        self.assignment_model = AssignmentModel()
    
    def extract_grading_results(self, llm_response):
        """
        แยกข้อมูลคะแนนและข้อเสนอแนะจากการตอบกลับของ LLM
        
        Args:
            llm_response (str): ข้อความตอบกลับจาก LLM
            
        Returns:
            dict: คะแนนและข้อเสนอแนะ
        """
        lines = llm_response.strip().split('\n')
        
        score = 0
        reasons = ""
        feedback = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if "คะแนนที่ได้" in line:
                # ดึงคะแนนจากบรรทัด
                try:
                    score_text = line.split(":")[-1].strip()
                    # แปลงเป็นตัวเลข
                    score = float(score_text)
                except Exception:
                    # ถ้าแปลงเป็นตัวเลขไม่ได้ ให้ใช้ค่าเริ่มต้น
                    score = 0
                current_section = "score"
            elif "เหตุผลในการให้คะแนน" in line:
                current_section = "reasons"
            elif "ข้อเสนอแนะ" in line:
                current_section = "feedback"
            else:
                if current_section == "reasons" and not "คะแนนที่ได้" in line and not "ข้อเสนอแนะ" in line:
                    reasons += line + "\n"
                elif current_section == "feedback":
                    feedback += line + "\n"
        
        return {
            "score": score,
            "reasons": reasons.strip(),
            "feedback": feedback.strip()
        }
        
    def grade_submission_with_llm(self, submission_id):
        """
        ตรวจคำตอบของนักเรียนโดยใช้ LLM
        
        Args:
            submission_id (str): ID ของคำตอบที่ต้องการตรวจ
            
        Returns:
            dict: ผลการตรวจและให้คะแนน
        """
        # ดึงข้อมูลคำตอบ
        submission_data = self.submission_model.get_by_id(submission_id).data[0]
        assignment_id = submission_data['assignment_id']
        
        # ดึงข้อมูลงานและเฉลย
        assignment_data = self.assignment_model.get_by_id(assignment_id).data[0]
        solution_data = self.solution_model.get_by_assignment(assignment_id, submission_data['user_id']).data
        
        if not solution_data:
            return {"error": "ไม่พบเฉลยสำหรับงานนี้"}
        
        # ใช้เฉลยแรกที่พบ
        solution_text = solution_data[0]['content_text']
        submission_text = submission_data['content_text']
        total_score = assignment_data['total_score']
        
        # ใช้ LLM ตรวจคำตอบ
        llm_response = self.llm_service.grade_submission(
            solution_text=solution_text,
            submission_text=submission_text,
            total_score=total_score
        )
        
        # แยกข้อมูลคะแนนและข้อเสนอแนะ
        grading_results = self.extract_grading_results(llm_response)
        
        # บันทึกผลการตรวจลงฐานข้อมูล
        grade_data = {
            "score": grading_results['score'],
            "feedback": grading_results['reasons'] + "\n\n" + grading_results['feedback'],
            "approved": False,  # ต้องได้รับการอนุมัติจากอาจารย์
            "user_id": submission_data['user_id'],
            "submission_id": submission_id
        }
        
        grade_result = self.grade_model.create(grade_data)
        
        # อัปเดตสถานะของคำตอบ
        self.submission_model.update(submission_id, {"status": "graded"})
        
        return {
            "grade_id": grade_result.data[0]['id'],
            "score": grading_results['score'],
            "feedback": grading_results['reasons'] + "\n\n" + grading_results['feedback'],
            "total_score": total_score,
            "raw_llm_response": llm_response
        }
    
    def grade_with_rag(self, submission_id):
        """
        ตรวจคำตอบโดยใช้เทคนิค RAG (Retrieval-Augmented Generation)
        
        Args:
            submission_id (str): ID ของคำตอบที่ต้องการตรวจ
            
        Returns:
            dict: ผลการตรวจและให้คะแนน
        """
        # ดึงข้อมูลคำตอบ
        submission_data = self.submission_model.get_by_id(submission_id).data[0]
        assignment_id = submission_data['assignment_id']
        
        # ดึงข้อมูลงานและเฉลย
        assignment_data = self.assignment_model.get_by_id(assignment_id).data[0]
        
        # ดึงข้อมูลคำตอบของนักเรียน
        submission_text = submission_data['content_text']
        
        # ค้นหาเฉลยที่เกี่ยวข้องโดยใช้ vector search
        similar_solutions = self.embedding_service.find_similar_solutions(submission_text)
        
        if not similar_solutions:
            # ถ้าไม่พบเฉลยที่เกี่ยวข้อง ให้ใช้การตรวจแบบปกติ
            return self.grade_submission_with_llm(submission_id)
        
        # ดึงข้อมูลเฉลยทั้งหมดที่เกี่ยวข้อง
        relevant_solutions = []
        for solution in similar_solutions:
            solution_id = solution.payload.get('solution_id')
            if solution_id:
                solution_data = self.solution_model.get_by_id(solution_id).data
                if solution_data:
                    relevant_solutions.append(solution_data[0])
        
        # รวมเนื้อหาเฉลยทั้งหมด
        combined_solution_text = ""
        for solution in relevant_solutions:
            if solution['content_text']:
                combined_solution_text += solution['content_text'] + "\n\n"
        
        # ถ้าไม่มีเฉลยที่เกี่ยวข้อง ให้ใช้การตรวจแบบปกติ
        if not combined_solution_text:
            return self.grade_submission_with_llm(submission_id)
        
        try:
            # เรียกใช้ LLM service กับเฉลยที่รวมแล้ว
            llm_response = self.llm_service.grade_submission(
                solution_text=combined_solution_text,
                submission_text=submission_text,
                total_score=assignment_data['total_score']
            )
            
            # แยกข้อมูลคะแนนและข้อเสนอแนะ
            grading_results = self.extract_grading_results(llm_response)
            
            # บันทึกผลการตรวจลงฐานข้อมูล
            grade_data = {
                "score": grading_results['score'],
                "feedback": grading_results['reasons'] + "\n\n" + grading_results['feedback'],
                "approved": False,  # ต้องได้รับการอนุมัติจากอาจารย์
                "user_id": submission_data['user_id'],
                "submission_id": submission_id
            }
            
            grade_result = self.grade_model.create(grade_data)
            
            # อัปเดตสถานะของคำตอบ
            self.submission_model.update(submission_id, {"status": "graded"})
            
            return {
                "grade_id": grade_result.data[0]['id'],
                "score": grading_results['score'],
                "feedback": grading_results['reasons'] + "\n\n" + grading_results['feedback'],
                "total_score": assignment_data['total_score'],
                "raw_llm_response": llm_response,
                "method": "rag",
                "relevant_solutions_count": len(relevant_solutions)
            }
        except Exception as e:
            print(f"Exception in RAG grading: {str(e)}")
            # กรณีที่มีข้อผิดพลาด ให้ใช้การตรวจแบบปกติ
            return self.grade_submission_with_llm(submission_id)