// static/js/auth.js
document.addEventListener('DOMContentLoaded', function() {
    // เพิ่มตรวจสอบว่าอยู่ที่หน้าใด
    const currentPath = window.location.pathname;
    const token = localStorage.getItem('token');
    
    // ถ้าอยู่ในหน้า login/register แล้วมี token ให้ redirect ไปหน้า dashboard
    if ((currentPath === '/login' || currentPath === '/register') && token) {
        window.location.href = '/dashboard';
        return; // ยุติการทำงานที่เหลือ
    }
    
    // ถ้าอยู่ในหน้า dashboard แล้วไม่มี token ให้ redirect ไปหน้า login
    if (currentPath === '/dashboard' && !token) {
        window.location.href = '/login';
        return; // ยุติการทำงานที่เหลือ
    }
    
    // เพิ่ม event listener สำหรับฟอร์มเข้าสู่ระบบ
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
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
                    const errorEl = document.getElementById('login-error');
                    errorEl.textContent = result.error;
                    errorEl.classList.remove('d-none');
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
                const errorEl = document.getElementById('login-error');
                errorEl.textContent = 'เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์';
                errorEl.classList.remove('d-none');
            });
        });
    }
    
    // เพิ่ม event listener สำหรับฟอร์มลงทะเบียน
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // ตรวจสอบว่ารหัสผ่านและยืนยันรหัสผ่านตรงกันหรือไม่
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            const errorEl = document.getElementById('register-error');
            errorEl.classList.add('d-none');
            
            if (password !== confirmPassword) {
                errorEl.textContent = 'รหัสผ่านและยืนยันรหัสผ่านไม่ตรงกัน';
                errorEl.classList.remove('d-none');
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
                    errorEl.textContent = result.error;
                    errorEl.classList.remove('d-none');
                } else if (result.success) {
                    // เปลี่ยนเส้นทางไปยังหน้าเข้าสู่ระบบพร้อมข้อความสำเร็จ
                    window.location.href = '/login?registered=true';
                }
            })
            .catch(error => {
                console.error('เกิดข้อผิดพลาดในการลงทะเบียน:', error);
                errorEl.textContent = 'เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์';
                errorEl.classList.remove('d-none');
            });
        });
    }
});