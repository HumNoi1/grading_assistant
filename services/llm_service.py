# grading_assistant/services/llm_service.py
import os
from langchain.llms import LlamaCpp
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

# กำหนดค่าพื้นฐาน
LM_STUDIO_PATH = os.getenv("LM_STUDIO_PATH", "./models/llm-model.gguf")

class LLMService:
    """
    คลาสสำหรับการเชื่อมต่อและใช้งาน LLM ผ่าน LMStudio
    """
    def __init__(self):
        # ตั้งค่า callback manager สำหรับ streaming output
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        
        # กำหนดค่า LLM
        self.llm = LlamaCpp(
            model_path=LM_STUDIO_PATH,
            temperature=0.1,
            max_tokens=2048,
            top_p=0.95,
            callback_manager=callback_manager,
            verbose=False,
            n_ctx=4096  # บริบทสูงสุดที่โมเดลสามารถรับได้
        )
    
    def create_grading_chain(self):
        """
        สร้าง LLMChain สำหรับการตรวจข้อสอบ
        
        Returns:
            LLMChain: chain สำหรับการตรวจข้อสอบ
        """
        grading_template = """
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
        
        prompt = PromptTemplate(
            template=grading_template,
            input_variables=["solution_text", "submission_text", "total_score"]
        )
        
        return LLMChain(llm=self.llm, prompt=prompt)
    
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
        chain = self.create_grading_chain()
        return chain.run(
            solution_text=solution_text,
            submission_text=submission_text,
            total_score=total_score
        )

# grading_assistant/services/embedding_service.py
import os
import uuid
from langchain.embeddings import HuggingFaceEmbeddings
from models.vector_db import VectorDB
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

# ตั้งค่าพื้นฐาน
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

class EmbeddingService:
    """
    คลาสสำหรับการสร้าง Vector Embeddings และจัดการกับคลังข้อมูล Vector
    """
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        self.vector_db = VectorDB()
    
    def create_embedding(self, text):
        """
        สร้าง embedding จากข้อความ
        
        Args:
            text (str): ข้อความที่ต้องการสร้าง embedding
            
        Returns:
            list: vector embedding
        """
        return self.embeddings.embed_query(text)
    
    def store_solution_embedding(self, solution_id, text, metadata=None):
        """
        สร้างและบันทึก embedding ของเฉลย
        
        Args:
            solution_id (str): ID ของเฉลย
            text (str): ข้อความเฉลย
            metadata (dict, optional): ข้อมูลเพิ่มเติมเกี่ยวกับเฉลย
            
        Returns:
            str: vector_id ที่บันทึก
        """
        if metadata is None:
            metadata = {}
            
        # เพิ่มข้อมูลพื้นฐาน
        metadata.update({
            "solution_id": solution_id,
            "type": "solution"
        })
        
        # สร้าง vector ID
        vector_id = f"sol_{uuid.uuid4()}"
        
        # สร้างและบันทึก embedding
        embedding = self.create_embedding(text)
        self.vector_db.store_embedding(vector_id, embedding, metadata)
        
        return vector_id
    
    def find_similar_solutions(self, text, limit=5):
        """
        ค้นหาเฉลยที่คล้ายกับข้อความที่ให้มา
        
        Args:
            text (str): ข้อความที่ต้องการค้นหาเฉลยที่คล้ายกัน
            limit (int, optional): จำนวนผลลัพธ์สูงสุดที่ต้องการ
            
        Returns:
            list: รายการเฉลยที่คล้ายกัน
        """
        embedding = self.create_embedding(text)
        return self.vector_db.search_similar(embedding, limit)