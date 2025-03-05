# grading_assistant/utils/file_utils.py
import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import io

# ประเภทไฟล์ที่อนุญาต
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """
    ตรวจสอบว่าไฟล์มีนามสกุลที่อนุญาตหรือไม่
    
    Args:
        filename (str): ชื่อไฟล์ที่ต้องการตรวจสอบ
        
    Returns:
        bool: True ถ้าไฟล์มีนามสกุลที่อนุญาต, False ถ้าไม่ใช่
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """
    สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
    
    Args:
        filename (str): ชื่อไฟล์เดิม
        
    Returns:
        str: ชื่อไฟล์ใหม่ที่ไม่ซ้ำกัน
    """
    # สร้างชื่อไฟล์ที่ปลอดภัย
    secure_name = secure_filename(filename)
    # ดึงนามสกุลไฟล์
    ext = secure_name.rsplit('.', 1)[1].lower() if '.' in secure_name else ''
    # สร้างชื่อไฟล์ใหม่ด้วย UUID
    new_filename = f"{uuid.uuid4()}.{ext}" if ext else f"{uuid.uuid4()}"
    
    return new_filename

def save_file(file, folder_path):
    """
    บันทึกไฟล์ลงในโฟลเดอร์
    
    Args:
        file: ไฟล์ที่ต้องการบันทึก
        folder_path (str): พาธของโฟลเดอร์
        
    Returns:
        dict: ข้อมูลของไฟล์ที่บันทึก หรือข้อความข้อผิดพลาด
    """
    try:
        if not file or file.filename == '':
            return {"error": "ไม่พบไฟล์"}
        
        if not allowed_file(file.filename):
            return {"error": "นามสกุลไฟล์ไม่ได้รับอนุญาต"}
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        os.makedirs(folder_path, exist_ok=True)
        
        # สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
        new_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(folder_path, new_filename)
        
        # บันทึกไฟล์
        file.save(file_path)
        
        return {
            "path": file_path,
            "name": new_filename,
            "original_name": file.filename,
            "size": os.path.getsize(file_path),
            "type": file.content_type
        }
    except Exception as e:
        return {"error": f"เกิดข้อผิดพลาดในการบันทึกไฟล์: {str(e)}"}

def delete_file(file_path):
    """
    ลบไฟล์
    
    Args:
        file_path (str): พาธของไฟล์ที่ต้องการลบ
        
    Returns:
        dict: สถานะการลบไฟล์
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"success": True, "message": "ลบไฟล์สำเร็จ"}
        else:
            return {"error": "ไม่พบไฟล์"}
    except Exception as e:
        return {"error": f"เกิดข้อผิดพลาดในการลบไฟล์: {str(e)}"}

def resize_image(file_path, max_width=800, max_height=600):
    """
    ปรับขนาดรูปภาพ
    
    Args:
        file_path (str): พาธของไฟล์รูปภาพ
        max_width (int): ความกว้างสูงสุด
        max_height (int): ความสูงสูงสุด
        
    Returns:
        bool: True ถ้าปรับขนาดสำเร็จ, False ถ้าไม่สำเร็จ
    """
    try:
        # ตรวจสอบว่าเป็นไฟล์รูปภาพหรือไม่
        if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return False
        
        # เปิดรูปภาพ
        img = Image.open(file_path)
        
        # ตรวจสอบว่าต้องปรับขนาดหรือไม่
        if img.width <= max_width and img.height <= max_height:
            return True
        
        # คำนวณอัตราส่วนการย่อขนาด
        ratio = min(max_width / img.width, max_height / img.height)
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        
        # ปรับขนาดรูปภาพ
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # บันทึกรูปภาพทับไฟล์เดิม
        img.save(file_path, quality=95, optimize=True)
        
        return True
    except Exception:
        return False

def get_file_extension(filename):
    """
    ดึงนามสกุลไฟล์
    
    Args:
        filename (str): ชื่อไฟล์
        
    Returns:
        str: นามสกุลไฟล์ หรือข้อความว่างถ้าไม่มีนามสกุล
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def get_mime_type(file_extension):
    """
    แปลงนามสกุลไฟล์เป็น MIME type
    
    Args:
        file_extension (str): นามสกุลไฟล์
        
    Returns:
        str: MIME type
    """
    mime_types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg'
    }
    
    return mime_types.get(file_extension.lower(), 'application/octet-stream')