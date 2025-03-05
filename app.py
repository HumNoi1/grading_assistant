# grading_assistant/app.py
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
import os
from routes import auth_routes, semester_routes, class_routes, subject_routes, assignment_routes, solution_routes, submission_routes, grade_routes
from models.database import supabase
from config import get_config

# โหลดค่ากำหนด
config = get_config()

# สร้าง Flask application
app = Flask(__name__)

# ตั้งค่า Secret Key
app.secret_key = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

# ลงทะเบียน Blueprints
app.register_blueprint(auth_routes.bp)
app.register_blueprint(semester_routes.bp)
app.register_blueprint(class_routes.bp)
app.register_blueprint(subject_routes.bp)
app.register_blueprint(assignment_routes.bp)
app.register_blueprint(solution_routes.bp)
app.register_blueprint(submission_routes.bp)
app.register_blueprint(grade_routes.bp)

# หน้าหลัก
@app.route('/')
def index():
    return render_template('index.html')

# หน้า Dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# หน้า Login
@app.route('/login')
def login_page():
    return render_template('login.html')

# หน้า Register
@app.route('/register')
def register_page():
    return render_template('register.html')

# ตัวจัดการข้อผิดพลาด
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": "ไฟล์มีขนาดใหญ่เกินไป (สูงสุด 16MB)"}), 413

if __name__ == '__main__':
    app.run(debug=config.DEBUG, 
            host=os.getenv("FLASK_HOST", "0.0.0.0"),
            port=int(os.getenv("FLASK_PORT", 5000)))