import time
import logging

logger = logging.getLogger(__name__)

class RequestTimeMiddleware:
    """Middleware สำหรับบันทึกเวลาที่ใช้ในการประมวลผลแต่ละหน้า"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        # แสดงผลเวลาที่ใช้ใน Console (โหมดพัฒนา)
        print(f"--- PATH: {request.path} | PROCESS TIME: {duration:.2f}s ---")
        return response