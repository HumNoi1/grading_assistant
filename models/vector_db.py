# grading_assistant/models/vector_db.py
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

# ข้อมูลการเชื่อมต่อ Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "solution_embeddings"

class VectorDB:
    """
    คลาสสำหรับจัดการ Vector Database (Qdrant)
    """
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """ตรวจสอบว่า collection มีอยู่หรือไม่ ถ้าไม่มีให้สร้าง"""
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=1536,  # ขนาด vector สำหรับ embedding model
                    distance=models.Distance.COSINE
                )
            )
    
    def store_embedding(self, vector_id, embedding, metadata=None):
        """
        บันทึก embedding ลงใน vector database
        
        Args:
            vector_id (str): ID ของ vector
            embedding (list): vector embedding
            metadata (dict, optional): ข้อมูลเพิ่มเติมเกี่ยวกับ vector
        
        Returns:
            dict: ผลการบันทึก
        """
        if metadata is None:
            metadata = {}
            
        return self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload=metadata
                )
            ]
        )
    
    def search_similar(self, embedding, limit=5):
        """
        ค้นหา vectors ที่คล้ายกับ embedding ที่ให้มา
        
        Args:
            embedding (list): vector embedding ที่ต้องการค้นหา
            limit (int, optional): จำนวนผลลัพธ์สูงสุดที่ต้องการ
            
        Returns:
            list: รายการผลลัพธ์ที่คล้ายกัน
        """
        return self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            limit=limit
        )
    
    def delete_embedding(self, vector_id):
        """
        ลบ embedding ตาม ID
        
        Args:
            vector_id (str): ID ของ vector ที่ต้องการลบ
            
        Returns:
            dict: ผลการลบ
        """
        return self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.PointIdsList(
                points=[vector_id]
            )
        )