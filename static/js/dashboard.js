// grading_assistant/static/js/dashboard.js
// สคริปต์สำหรับหน้าแผงควบคุม

// ตัวแปรเพื่อป้องกันการเรียกซ้ำ
let dashboardInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    if (dashboardInitialized) return; // ป้องกันการเรียกซ้ำ
    dashboardInitialized = true;
    
    // ตรวจสอบว่ากำลังอยู่ที่หน้า dashboard หรือไม่
    const currentPath = window.location.pathname;
    if (currentPath !== '/dashboard') {
        return; // ถ้าไม่ใช่หน้า dashboard ให้ออกจากฟังก์ชัน
    }
    
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
                        เกิดข้อผิดพลาดในการโหลดข้อมูล: ${data?.error || 'ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้'}
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

// ฟังก์ชันแสดงข้อมูลในตาราง (สตับฟังก์ชัน)
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
            tableHTML = `<div class="alert alert-info">เลือกเมนูเพื่อดูข้อมูล</div>`;
    }
    
    contentContainer.innerHTML = tableHTML || `<div class="alert alert-info">ไม่พบข้อมูล</div>`;
    
    // เพิ่ม event listener สำหรับปุ่มในตาราง
    if (typeof addTableButtonListeners === 'function') {
        addTableButtonListeners(menuId);
    }
}

// สตับฟังก์ชัน - ต้องมีการสร้างฟังก์ชันเหล่านี้ต่อไป
function createSemestersTable(data) {
    return `<div class="alert alert-info">ฟังก์ชันสร้างตารางเทอมเรียนยังไม่ได้ถูกสร้าง</div>`;
}

function createClassesTable(data) {
    return `<div class="alert alert-info">ฟังก์ชันสร้างตารางชั้นเรียนยังไม่ได้ถูกสร้าง</div>`;
}

function createSubjectsTable(data) {
    return `<div class="alert alert-info">ฟังก์ชันสร้างตารางวิชายังไม่ได้ถูกสร้าง</div>`;
}

function createAssignmentsTable(data) {
    return `<div class="alert alert-info">ฟังก์ชันสร้างตารางงานยังไม่ได้ถูกสร้าง</div>`;
}

function createSubmissionsTable(data) {
    return `<div class="alert alert-info">ฟังก์ชันสร้างตารางการส่งงานยังไม่ได้ถูกสร้าง</div>`;
}

function createGradesTable(data) {
    return `<div class="alert alert-info">ฟังก์ชันสร้างตารางคะแนนยังไม่ได้ถูกสร้าง</div>`;
}

function showAddModal(menuId) {
    // สตับฟังก์ชัน
    console.log('แสดง modal สำหรับเพิ่มข้อมูล:', menuId);
}

function saveData() {
    // สตับฟังก์ชัน
    console.log('บันทึกข้อมูล');
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