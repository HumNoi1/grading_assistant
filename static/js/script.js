// grading_assistant/static/js/script.js
// สคริปต์ทั่วไปที่ใช้ในทุกหน้า

// ตรวจสอบว่าผู้ใช้เข้าสู่ระบบหรือไม่
function checkAuth() {
    const token = localStorage.getItem('token');
    
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
    .then(response => {
        // ลบ token และข้อมูลผู้ใช้จาก localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // เปลี่ยนเส้นทางไปยังหน้าหลัก
        window.location.href = '/';
    })
    .catch(error => {
        console.error('เกิดข้อผิดพลาดในการออกจากระบบ:', error);
        // ลบ token และข้อมูลผู้ใช้จาก localStorage ในกรณีที่มีข้อผิดพลาด
        localStorage.removeItem('token');
        localStorage.removeItem('user');
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


// grading_assistant/static/js/auth.js
// สคริปต์สำหรับหน้าเข้าสู่ระบบและลงทะเบียน

document.addEventListener('DOMContentLoaded', function() {
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


// grading_assistant/static/js/dashboard.js
// สคริปต์สำหรับหน้าแผงควบคุม

document.addEventListener('DOMContentLoaded', function() {
    // ตรวจสอบว่าผู้ใช้เข้าสู่ระบบหรือไม่
    const token = localStorage.getItem('token');
    if (!token) {
        // ถ้าผู้ใช้ยังไม่เข้าสู่ระบบ ให้เปลี่ยนเส้นทางไปยังหน้าเข้าสู่ระบบ
        window.location.href = '/login';
        return;
    }
    
    // เพิ่ม event listener สำหรับปุ่มออกจากระบบ
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // เพิ่ม event listener สำหรับเมนู
    const menuItems = document.querySelectorAll('.list-group-item');
    menuItems.forEach(item => {
        item.addEventListener('click', function(event) {
            event.preventDefault();
            
            // ลบคลาส active จากทุกรายการ
            menuItems.forEach(menuItem => {
                menuItem.classList.remove('active');
            });
            
            // เพิ่มคลาส active ให้กับรายการที่คลิก
            this.classList.add('active');
            
            // แสดงเนื้อหาตามเมนูที่เลือก
            const contentTitle = document.getElementById('content-title');
            if (contentTitle) {
                contentTitle.textContent = this.textContent;
            }
            
            // โหลดข้อมูลตามเมนูที่เลือก
            loadContent(this.id);
        });
    });
    
    // โหลดข้อมูลเริ่มต้น (เทอมเรียน)
    loadContent('nav-semesters');
    
    // เพิ่ม event listener สำหรับปุ่มเพิ่มข้อมูล
    const addBtn = document.getElementById('add-btn');
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            // แสดง modal สำหรับเพิ่มข้อมูล
            const activeMenu = document.querySelector('.list-group-item.active');
            if (activeMenu) {
                showAddModal(activeMenu.id);
            }
        });
    }
    
    // เพิ่ม event listener สำหรับปุ่มบันทึกใน modal
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            saveData();
        });
    }
});

// ฟังก์ชันโหลดข้อมูลตามเมนูที่เลือก
function loadContent(menuId) {
    const contentContainer = document.getElementById('content-container');
    if (!contentContainer) return;
    
    // แสดง loading spinner
    contentContainer.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">กำลังโหลด...</span>
            </div>
            <p class="mt-3">กำลังโหลดข้อมูล...</p>
        </div>
    `;
    
    // กำหนด endpoint ตามเมนูที่เลือก
    let endpoint = '';
    switch (menuId) {
        case 'nav-semesters':
            endpoint = '/api/semesters';
            break;
        case 'nav-classes':
            endpoint = '/api/classes';
            break;
        case 'nav-subjects':
            endpoint = '/api/subjects';
            break;
        case 'nav-assignments':
            endpoint = '/api/assignments';
            break;
        case 'nav-submissions':
            endpoint = '/api/submissions?status=pending';
            break;
        case 'nav-grades':
            endpoint = '/api/grades';
            break;
        case 'nav-profile':
            loadProfile();
            return;
        default:
            endpoint = '/api/semesters';
    }
    
    // ดึงข้อมูลจาก API
    apiRequest(endpoint)
        .then(data => {
            if (data && !data.error) {
                // แสดงข้อมูลในตาราง
                displayData(menuId, data);
            } else {
                contentContainer.innerHTML = `
                    <div class="alert alert-danger">
                        เกิดข้อผิดพลาดในการโหลดข้อมูล: ${data.error || 'ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้'}
                    </div>
                `;
            }
        })
        .catch(error => {
            contentContainer.innerHTML = `
                <div class="alert alert-danger">
                    เกิดข้อผิดพลาด: ${error.message}
                </div>
            `;
        });
}

// ฟังก์ชันแสดงข้อมูลในตาราง
function displayData(menuId, data) {
    const contentContainer = document.getElementById('content-container');
    if (!contentContainer) return;
    
    // สร้างตารางตามประเภทข้อมูล
    let tableHTML = '';
    switch (menuId) {
        case 'nav-semesters':
            tableHTML = createSemestersTable(data);
            break;
        case 'nav-classes':
            tableHTML = createClassesTable(data);
            break;
        case 'nav-subjects':
            tableHTML = createSubjectsTable(data);
            break;
        case 'nav-assignments':
            tableHTML = createAssignmentsTable(data);
            break;
        case 'nav-submissions':
            tableHTML = createSubmissionsTable(data);
            break;
        case 'nav-grades':
            tableHTML = createGradesTable(data);
            break;
        default:
            tableHTML = createSemestersTable(data);
    }
    
    contentContainer.innerHTML = tableHTML;
    
    // เพิ่ม event listener สำหรับปุ่มในตาราง
    addTableButtonListeners(menuId);
}

// ฟังก์ชันโหลดข้อมูลโปรไฟล์
function loadProfile() {
    const contentContainer = document.getElementById('content-container');
    if (!contentContainer) return;
    
    // ดึงข้อมูลผู้ใช้จาก localStorage
    const user = JSON.parse(localStorage.getItem('user'));
    
    if (user) {
        contentContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">ข้อมูลส่วนตัว</h5>
                    <div class="mb-3">
                        <label class="form-label">ชื่อ-นามสกุล</label>
                        <input type="text" class="form-control" value="${user.name}" readonly>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">อีเมล</label>
                        <input type="email" class="form-control" value="${user.email}" readonly>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">บทบาท</label>
                        <input type="text" class="form-control" value="${user.role}" readonly>
                    </div>
                </div>
            </div>
        `;
    } else {
        contentContainer.innerHTML = `
            <div class="alert alert-danger">
                ไม่สามารถโหลดข้อมูลโปรไฟล์ได้
            </div>
        `;
    }
}