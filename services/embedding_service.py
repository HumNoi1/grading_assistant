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
    
    def delete_embedding(self, vector_id):
        """
        ลบ embedding ตาม ID
        
        Args:
            vector_id (str): ID ของ vector ที่ต้องการลบ
            
        Returns:
            bool: True ถ้าลบสำเร็จ, False ถ้าไม่สำเร็จ
        """
        try:
            self.vector_db.delete_embedding(vector_id)
            return True
        except Exception:
            return False
    
    def create_embeddings_from_text_chunks(self, text, chunk_size=1000, overlap=200, metadata=None):
        """
        แบ่งข้อความเป็นชิ้นเล็กๆ และสร้าง embeddings
        
        Args:
            text (str): ข้อความที่ต้องการแบ่ง
            chunk_size (int): ขนาดของแต่ละชิ้น
            overlap (int): จำนวนตัวอักษรที่ซ้อนทับกัน
            metadata (dict, optional): ข้อมูลเพิ่มเติม
            
        Returns:
            list: รายการ vector IDs ที่บันทึก
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        if metadata is None:
            metadata = {}
            
        # สร้าง text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap
        )
        
        # แบ่งข้อความ
        chunks = text_splitter.split_text(text)
        
        # สร้างและบันทึก embeddings
        vector_ids = []
        for i, chunk in enumerate(chunks):
            # สร้าง metadata สำหรับแต่ละชิ้น
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
            
            # สร้าง vector ID
            vector_id = f"chunk_{uuid.uuid4()}"
            
            # สร้างและบันทึก embedding
            embedding = self.create_embedding(chunk)
            self.vector_db.store_embedding(vector_id, embedding, chunk_metadata)
            
            vector_ids.append(vector_id)
            
        return vector_ids