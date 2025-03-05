// grading_assistant/static/js/script.js
// สคริปต์ทั่วไปที่ใช้ในทุกหน้า

// ตัวแปรเพื่อป้องกันการเรียกซ้ำ
let authChecked = false;

// ตรวจสอบว่าผู้ใช้เข้าสู่ระบบหรือไม่
function checkAuth() {
    if (authChecked) return; // ป้องกันการเรียกซ้ำ
    authChecked = true;
    
    const token = localStorage.getItem('token');
    const currentPath = window.location.pathname;
    
    // ถ้าอยู่ในหน้า login/register แล้วมี token ให้ redirect ไปหน้า dashboard
    if ((currentPath === '/login' || currentPath === '/register') && token) {
        window.location.href = '/dashboard';
        return;
    }
    
    // ถ้าอยู่ในหน้า dashboard แล้วไม่มี token ให้ redirect ไปหน้า login
    if (currentPath === '/dashboard' && !token) {
        window.location.href = '/login';
        return;
    }
    
    if (token) {
        // แสดงเมนูสำหรับผู้ใช้ที่เข้าสู่ระบบ
        document.querySelectorAll('.navbar-nav').forEach(nav => {
            if (nav.querySelector('a[href="/login"]')) {
                nav.innerHTML = `
                    <li class="nav-item">
                        <a class="nav-link" href="/dashboard">แผงควบคุม</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" id="nav-logout">ออกจากระบบ</a>
                    </li>
                `;
            }
        });
        
        // เพิ่ม event listener สำหรับปุ่มออกจากระบบ
        const logoutBtn = document.getElementById('nav-logout');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', logout);
        }
    }
}

// ฟังก์ชันออกจากระบบ
function logout() {
    // ส่งคำขอ logout ไปยังเซิร์ฟเวอร์
    fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
    })
    .finally(() => {
        // ลบ token และข้อมูลผู้ใช้จาก localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // เปลี่ยนเส้นทางไปยังหน้าหลัก
        window.location.href = '/';
    });
}

// แสดงข้อความข้อผิดพลาด
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('d-none');
    }
}

// ซ่อนข้อความข้อผิดพลาด
function hideError(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.classList.add('d-none');
    }
}

// ฟังก์ชันสำหรับการส่งคำขอ API พร้อม token
async function apiRequest(url, method = 'GET', data = null) {
    const token = localStorage.getItem('token');
    
    const options = {
        method: method,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        
        if (response.status === 401) {
            // Token หมดอายุหรือไม่ถูกต้อง ให้ออกจากระบบ
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login?error=session_expired';
            return null;
        }
        
        return await response.json();
    } catch (error) {
        console.error('เกิดข้อผิดพลาดในการส่งคำขอ API:', error);
        return { error: 'เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์' };
    }
}

// รัน checkAuth เมื่อหน้าเว็บโหลดเสร็จ
document.addEventListener('DOMContentLoaded', checkAuth);