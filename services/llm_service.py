# services/llm_service.py
import os
import requests
import json
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

# กำหนดค่าพื้นฐาน
LMSTUDIO_URL = os.getenv("LMSTUDIO_URL", "http://127.0.0.1:1234")

class LLMService:
    """
    คลาสสำหรับการเชื่อมต่อและใช้งาน LLM ผ่าน LMStudio
    """
    def __init__(self):
        self.api_url = f"{LMSTUDIO_URL}/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def grade_submission(self, solution_text, submission_text, total_score):
        """
        ตรวจคำตอบของนักเรียนโดยเปรียบเทียบกับเฉลย
        
        Args:
            solution_text (str): ข้อความเฉลยของอาจารย์
            submission_text (str): ข้อความคำตอบของนักเรียน
            total_score (float): คะแนนเต็ม
            
        Returns:
            str: ผลการตรวจและให้คะแนน
        """
        prompt = self._create_grading_prompt(solution_text, submission_text, total_score)
        
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": "คุณเป็นผู้ช่วยตรวจข้อสอบอัตนัยที่มีความเชี่ยวชาญในการตรวจข้อสอบและให้คะแนน"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2048,
                "top_p": 0.95,
                "stream": False
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"Error calling LLM API: {response.text}")
                return "เกิดข้อผิดพลาดในการตรวจข้อสอบ โปรดลองอีกครั้ง"
        except Exception as e:
            print(f"Exception in LLM service: {str(e)}")
            return "เกิดข้อผิดพลาดในการเชื่อมต่อกับ LLM โปรดตรวจสอบการเชื่อมต่อ"
    
    def _create_grading_prompt(self, solution_text, submission_text, total_score):
        """
        สร้าง prompt สำหรับการตรวจข้อสอบ
        
        Args:
            solution_text (str): ข้อความเฉลยของอาจารย์
            submission_text (str): ข้อความคำตอบของนักเรียน
            total_score (float): คะแนนเต็ม
            
        Returns:
            str: prompt สำหรับการตรวจข้อสอบ
        """
        return f"""
        คุณเป็นผู้ช่วยตรวจข้อสอบอัตนัย เปรียบเทียบคำตอบของนักเรียนกับเฉลยและให้คะแนน
        
        # เฉลยของอาจารย์:
        {solution_text}
        
        # คำตอบของนักเรียน:
        {submission_text}
        
        # คะแนนเต็ม: {total_score}
        
        โปรดวิเคราะห์คำตอบของนักเรียนเทียบกับเฉลย แล้วให้คะแนนตามเกณฑ์ต่อไปนี้:
        1. ความถูกต้องของแนวคิดหลัก (60%)
        2. ความสมบูรณ์ของคำตอบ (30%)
        3. การใช้ศัพท์เทคนิคที่ถูกต้อง (10%)
        
        ผลลัพธ์ที่ต้องการ:
        1. คะแนนที่ได้ (เป็นตัวเลข): 
        2. เหตุผลในการให้คะแนน:
        3. ข้อเสนอแนะสำหรับนักเรียน:
        """