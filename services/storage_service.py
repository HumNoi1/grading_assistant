# grading_assistant/services/storage_service.py
import os
import uuid
import pathlib
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document
import pytesseract
from PIL import Image
import io

class StorageService:
    """
    คลาสสำหรับจัดการไฟล์และการจัดเก็บ
    """
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.allowed_extensions = {'pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'}
        
    def allowed_file(self, filename):
        """
        ตรวจสอบว่าไฟล์มีนามสกุลที่อนุญาตหรือไม่
        
        Args:
            filename (str): ชื่อไฟล์ที่ต้องการตรวจสอบ
            
        Returns:
            bool: True ถ้าไฟล์มีนามสกุลที่อนุญาต, False ถ้าไม่ใช่
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def upload_file(self, file, folder_path, user_id):
        """
        อัปโหลดไฟล์ไปยัง Supabase Storage
        
        Args:
            file (FileStorage): ไฟล์ที่ต้องการอัปโหลด
            folder_path (str): พาธของโฟลเดอร์
            user_id (str): ID ของผู้ใช้
            
        Returns:
            dict: ข้อมูลไฟล์ที่อัปโหลด
        """
        if not file or not self.allowed_file(file.filename):
            return {"error": "ไฟล์ไม่ถูกต้องหรือนามสกุลไม่ได้รับอนุญาต"}
        
        # สร้างชื่อไฟล์ที่ปลอดภัย
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        
        # สร้างชื่อไฟล์ใหม่ด้วย UUID เพื่อป้องกันการซ้ำกัน
        new_filename = f"{uuid.uuid4()}.{ext}"
        file_path = f"{folder_path}/{new_filename}"
        
        # อัปโหลดไฟล์ไปยัง Supabase Storage
        try:
            self.supabase.storage.from_("files").upload(file_path, file.read())
            
            # ดึง URL ของไฟล์
            file_url = self.supabase.storage.from_("files").get_public_url(file_path)
            
            return {
                "path": file_path,
                "name": filename,
                "original_name": file.filename,
                "url": file_url,
                "size": file.content_length,
                "type": file.content_type
            }
        except Exception as e:
            return {"error": f"เกิดข้อผิดพลาดในการอัปโหลดไฟล์: {str(e)}"}
    
    def download_file(self, file_path):
        """
        ดาวน์โหลดไฟล์จาก Supabase Storage
        
        Args:
            file_path (str): พาธของไฟล์
            
        Returns:
            bytes: ข้อมูลไฟล์
        """
        try:
            res = self.supabase.storage.from_("files").download(file_path)
            return res
        except Exception as e:
            return {"error": f"เกิดข้อผิดพลาดในการดาวน์โหลดไฟล์: {str(e)}"}
    
    def delete_file(self, file_path):
        """
        ลบไฟล์จาก Supabase Storage
        
        Args:
            file_path (str): พาธของไฟล์
            
        Returns:
            dict: สถานะการลบไฟล์
        """
        try:
            self.supabase.storage.from_("files").remove(file_path)
            return {"success": True, "message": "ลบไฟล์สำเร็จ"}
        except Exception as e:
            return {"error": f"เกิดข้อผิดพลาดในการลบไฟล์: {str(e)}"}
    
    def create_folder(self, folder_path):
        """
        สร้างโฟลเดอร์ใน Supabase Storage (ทำโดยการอัปโหลดไฟล์ว่างเปล่า)
        
        Args:
            folder_path (str): พาธของโฟลเดอร์ที่ต้องการสร้าง
            
        Returns:
            dict: สถานะการสร้างโฟลเดอร์
        """
        try:
            # ใน Supabase การสร้างโฟลเดอร์ทำโดยการอัปโหลดไฟล์ว่างเปล่าพร้อมกับพาธ
            placeholder_file = f"{folder_path}/.folder"
            self.supabase.storage.from_("files").upload(placeholder_file, b"")
            return {"success": True, "message": f"สร้างโฟลเดอร์ {folder_path} สำเร็จ"}
        except Exception as e:
            return {"error": f"เกิดข้อผิดพลาดในการสร้างโฟลเดอร์: {str(e)}"}
    
    def extract_text_from_file(self, file_data, file_type):
        """
        ดึงข้อความจากไฟล์
        
        Args:
            file_data (bytes): ข้อมูลไฟล์
            file_type (str): ประเภทของไฟล์
            
        Returns:
            str: ข้อความที่ดึงจากไฟล์
        """
        text = ""
        
        try:
            if file_type.endswith('pdf'):
                # ดึงข้อความจากไฟล์ PDF
                reader = PdfReader(io.BytesIO(file_data))
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                    
            elif file_type.endswith('docx'):
                # ดึงข้อความจากไฟล์ Word
                doc = Document(io.BytesIO(file_data))
                for para in doc.paragraphs:
                    text += para.text + "\n"
                    
            elif file_type.endswith(('png', 'jpg', 'jpeg')):
                # ดึงข้อความจากรูปภาพโดยใช้ OCR
                image = Image.open(io.BytesIO(file_data))
                text = pytesseract.image_to_string(image, lang='tha+eng')
                
            elif file_type.endswith('txt'):
                # ดึงข้อความจากไฟล์ข้อความ
                text = file_data.decode('utf-8')
            
            return text.strip()
        except Exception as e:
            return f"ไม่สามารถดึงข้อความจากไฟล์: {str(e)}"