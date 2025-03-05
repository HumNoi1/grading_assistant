# grading_assistant/models/database.py
import os
from supabase import create_client
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
load_dotenv()

# ข้อมูลการเชื่อมต่อ Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# สร้าง Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class SupabaseModel:
    """
    คลาสพื้นฐานสำหรับโมเดลที่ทำงานกับ Supabase
    """
    def __init__(self, table_name):
        self.table_name = table_name
        self.client = supabase
    
    def get_all(self, user_id=None):
        """ดึงข้อมูลทั้งหมดของตาราง"""
        query = self.client.table(self.table_name).select('*')
        if user_id:
            query = query.eq('user_id', user_id)
        return query.execute()
    
    def get_by_id(self, id):
        """ดึงข้อมูลตาม ID"""
        return self.client.table(self.table_name).select('*').eq('id', id).execute()
    
    def create(self, data):
        """สร้างข้อมูลใหม่"""
        return self.client.table(self.table_name).insert(data).execute()
    
    def update(self, id, data):
        """อัปเดตข้อมูลตาม ID"""
        return self.client.table(self.table_name).update(data).eq('id', id).execute()
    
    def delete(self, id):
        """ลบข้อมูลตาม ID"""
        return self.client.table(self.table_name).delete().eq('id', id).execute()

class SemesterModel(SupabaseModel):
    def __init__(self):
        super().__init__('semesters')
        
    def get_with_classes(self, user_id):
        """ดึงข้อมูลเทอมพร้อมกับชั้นเรียนที่เกี่ยวข้อง"""
        query = self.client.from_('semesters').select('*, classes(*)').eq('user_id', user_id)
        return query.execute()

class ClassModel(SupabaseModel):
    def __init__(self):
        super().__init__('classes')
        
    def get_by_semester(self, semester_id, user_id):
        """ดึงข้อมูลชั้นเรียนตามเทอม"""
        return self.client.table(self.table_name).select('*').eq('semester_id', semester_id).eq('user_id', user_id).execute()

class SubjectModel(SupabaseModel):
    def __init__(self):
        super().__init__('subjects')
        
    def get_by_class(self, class_id, user_id):
        """ดึงข้อมูลวิชาตามชั้นเรียน"""
        return self.client.table(self.table_name).select('*').eq('class_id', class_id).eq('user_id', user_id).execute()

class AssignmentModel(SupabaseModel):
    def __init__(self):
        super().__init__('assignments')
        
    def get_by_subject(self, subject_id, user_id):
        """ดึงข้อมูลงานตามวิชา"""
        return self.client.table(self.table_name).select('*').eq('subject_id', subject_id).eq('user_id', user_id).execute()

class SolutionModel(SupabaseModel):
    def __init__(self):
        super().__init__('solutions')
        
    def get_by_assignment(self, assignment_id, user_id):
        """ดึงข้อมูลเฉลยตามงาน"""
        return self.client.table(self.table_name).select('*').eq('assignment_id', assignment_id).eq('user_id', user_id).execute()

class SubmissionModel(SupabaseModel):
    def __init__(self):
        super().__init__('submissions')
        
    def get_by_assignment(self, assignment_id, user_id):
        """ดึงข้อมูลงานที่ส่งตามงาน"""
        return self.client.table(self.table_name).select('*').eq('assignment_id', assignment_id).eq('user_id', user_id).execute()
        
    def get_pending_submissions(self, user_id):
        """ดึงข้อมูลงานที่รอการตรวจ"""
        return self.client.table(self.table_name).select('*').eq('status', 'pending').eq('user_id', user_id).execute()

class GradeModel(SupabaseModel):
    def __init__(self):
        super().__init__('grades')
        
    def get_by_submission(self, submission_id, user_id):
        """ดึงข้อมูลคะแนนตามงานที่ส่ง"""
        return self.client.table(self.table_name).select('*').eq('submission_id', submission_id).eq('user_id', user_id).execute()