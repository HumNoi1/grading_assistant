# services/embedding_service.py
import os
import uuid
import requests
import json
from models.vector_db import VectorDB
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

# ตั้งค่าพื้นฐาน
LMSTUDIO_URL = os.getenv("LMSTUDIO_URL", "http://127.0.0.1:1234")

class EmbeddingService:
    """
    คลาสสำหรับการสร้าง Vector Embeddings และจัดการกับคลังข้อมูล Vector
    """
    def __init__(self):
        self.vector_db = VectorDB()
    
    def create_embedding(self, text):
        """
        สร้าง embedding จากข้อความ โดยใช้ LMStudio
        
        Args:
            text (str): ข้อความที่ต้องการสร้าง embedding
            
        Returns:
            list: vector embedding
        """
        try:
            # ใช้ API ของ LMStudio เพื่อสร้าง embedding
            response = requests.post(
                f"{LMSTUDIO_URL}/v1/embeddings",
                headers={"Content-Type": "application/json"},
                json={"input": text}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['data'][0]['embedding']
            else:
                # กรณีไม่สามารถเชื่อมต่อได้ หรือมีข้อผิดพลาด ให้ส่งค่า embedding ว่าง
                print(f"Error creating embedding: {response.text}")
                return [0] * 1536  # ใช้ค่าว่างขนาด 1536 (ขนาดทั่วไปของ embedding)
        except Exception as e:
            print(f"Error connecting to LMStudio: {str(e)}")
            return [0] * 1536
    
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
        if metadata is None:
            metadata = {}
            
        # แบ่งข้อความ
        chunks = self._split_text(text, chunk_size, overlap)
        
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
        
    def _split_text(self, text, chunk_size=1000, overlap=200):
        """
        แบ่งข้อความเป็นชิ้นเล็กๆ
        
        Args:
            text (str): ข้อความที่ต้องการแบ่ง
            chunk_size (int): ขนาดของแต่ละชิ้น
            overlap (int): จำนวนตัวอักษรที่ซ้อนทับกัน
            
        Returns:
            list: รายการชิ้นข้อความ
        """
        chunks = []
        
        if not text:
            return chunks
            
        i = 0
        text_length = len(text)
        
        while i < text_length:
            # กำหนดจุดสิ้นสุดของชิ้นปัจจุบัน
            end = min(i + chunk_size, text_length)
            
            # ตรวจสอบว่าควรขยายชิ้นเพื่อไม่ให้ตัดคำกลาง
            if end < text_length:
                # หาจุดสิ้นสุดที่เป็นช่องว่างหรือเครื่องหมายวรรคตอน
                while end > i and not text[end].isspace() and not text[end] in ",.!?;:":
                    end -= 1
                
                # ถ้าไม่พบช่องว่างหรือเครื่องหมายวรรคตอน ใช้ขนาดเต็ม
                if end == i:
                    end = min(i + chunk_size, text_length)
            
            # เพิ่มชิ้นข้อความลงในรายการ
            chunks.append(text[i:end])
            
            # เลื่อนไปยังจุดเริ่มต้นของชิ้นถัดไป โดยคำนึงถึงการซ้อนทับ
            i = end - overlap if end - overlap > i else end
            
        return chunks