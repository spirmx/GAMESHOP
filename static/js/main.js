document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 PAPAYA GAME SHOP: Systems Online');

    // ระบบแจ้งเตือน (Alert) ให้หายไปเองหลังจาก 5 วินาที
    const alerts = document.querySelectorAll('.alert-box');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // สำหรับจัดการปุ่ม Mobile Menu (ถ้ามี)
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
});