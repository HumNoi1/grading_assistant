# grading_assistant/config.py
import os
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

class Config:
    """
    คลาสสำหรับการกำหนดค่าแอปพลิเคชัน
    """
    # Flask config
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "your-secret-key")
    DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
    
    # Supabase config
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # LMStudio config
    LM_STUDIO_PATH = os.getenv("LM_STUDIO_PATH", "./models/llm-model.gguf")
    
    # Qdrant config
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    # Embedding model config
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    
    # ค่ากำหนดอื่นๆ
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB
    
    # สร้างโฟลเดอร์อัปโหลดถ้ายังไม่มี
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """
    ค่ากำหนดสำหรับสภาพแวดล้อมการพัฒนา
    """
    DEBUG = True

class ProductionConfig(Config):
    """
    ค่ากำหนดสำหรับสภาพแวดล้อมการใช้งานจริง
    """
    DEBUG = False

# เลือกค่ากำหนดตามสภาพแวดล้อม
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """
    ดึงค่ากำหนดตามสภาพแวดล้อม
    
    Returns:
        Config: คลาสค่ากำหนด
    """
    config_name = os.getenv('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])