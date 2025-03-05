// grading_assistant/static/js/auth.js
// สคริปต์สำหรับหน้าเข้าสู่ระบบและลงทะเบียน

// ตัวแปรเพื่อป้องกันการเรียกซ้ำ
let authInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    if (authInitialized) return; // ป้องกันการเรียกซ้ำ
    authInitialized = true;
    
    // ตรวจสอบว่ากำลังอยู่ที่หน้า login หรือ register หรือไม่
    const currentPath = window.location.pathname;
    if (currentPath !== '/login' && currentPath !== '/register') {
        return; // ถ้าไม่ใช่หน้าที่เกี่ยวข้อง ให้ออกจากฟังก์ชัน
    }
    
    // ตรวจสอบว่าผู้ใช้เข้าสู่ระบบอยู่แล้วหรือไม่
    const token = localStorage.getItem('token');
    if (token) {
        // ถ้าผู้ใช้เข้าสู่ระบบอยู่แล้ว ให้เปลี่ยนเส้นทางไปยังหน้าแผงควบคุม
        window.location.href = '/dashboard';
        return;
    }
    
    // เพิ่ม event listener สำหรับฟอร์มเข้าสู่ระบบ
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // ซ่อนข้อความข้อผิดพลาด
            hideError('login-error');
            
            // รวบรวมข้อมูลจากฟอร์ม
            const data = {
                email: document.getElementById('email').value,
                password: document.getElementById('password').value
            };
            
            // ส่งคำขอเข้าสู่ระบบไปยังเซิร์ฟเวอร์
            fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.error) {
                    // แสดงข้อความข้อผิดพลาด
                    showError('login-error', result.error);
                } else if (result.success && result.token) {
                    // บันทึก token และข้อมูลผู้ใช้ใน localStorage
                    localStorage.setItem('token', result.token);
                    localStorage.setItem('user', JSON.stringify(result.user));
                    
                    // เปลี่ยนเส้นทางไปยังหน้าแผงควบคุม
                    window.location.href = '/dashboard';
                }
            })
            .catch(error => {
                console.error('เกิดข้อผิดพลาดในการเข้าสู่ระบบ:', error);
                showError('login-error', 'เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์');
            });
        });
    }
    
    // เพิ่ม event listener สำหรับฟอร์มลงทะเบียน
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // ซ่อนข้อความข้อผิดพลาด
            hideError('register-error');
            
            // ตรวจสอบว่ารหัสผ่านและยืนยันรหัสผ่านตรงกันหรือไม่
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            if (password !== confirmPassword) {
                showError('register-error', 'รหัสผ่านและยืนยันรหัสผ่านไม่ตรงกัน');
                return;
            }
            
            // รวบรวมข้อมูลจากฟอร์ม
            const data = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                password: password
            };
            
            // ส่งคำขอลงทะเบียนไปยังเซิร์ฟเวอร์
            fetch('/api/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.error) {
                    // แสดงข้อความข้อผิดพลาด
                    showError('register-error', result.error);
                } else if (result.success) {
                    // เปลี่ยนเส้นทางไปยังหน้าเข้าสู่ระบบพร้อมข้อความสำเร็จ
                    window.location.href = '/login?registered=true';
                }
            })
            .catch(error => {
                console.error('เกิดข้อผิดพลาดในการลงทะเบียน:', error);
                showError('register-error', 'เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์');
            });
        });
    }
    
    // ตรวจสอบพารามิเตอร์ URL
    const urlParams = new URLSearchParams(window.location.search);
    
    // แสดงข้อความสำเร็จหลังจากลงทะเบียน
    if (urlParams.get('registered') === 'true') {
        const loginError = document.getElementById('login-error');
        if (loginError) {
            loginError.textContent = 'ลงทะเบียนสำเร็จ! โปรดเข้าสู่ระบบด้วยบัญชีของคุณ';
            loginError.classList.remove('alert-danger');
            loginError.classList.add('alert-success');
            loginError.classList.remove('d-none');
        }
    }
    
    // แสดงข้อความหมดเวลาเซสชัน
    if (urlParams.get('error') === 'session_expired') {
        const loginError = document.getElementById('login-error');
        if (loginError) {
            loginError.textContent = 'เซสชันหมดอายุ โปรดเข้าสู่ระบบอีกครั้ง';
            loginError.classList.remove('d-none');
        }
    }
});