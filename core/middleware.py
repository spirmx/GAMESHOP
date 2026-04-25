import logging
import time

from django.utils import timezone


logger = logging.getLogger(__name__)


class RequestTimeMiddleware:
    """Middleware สำหรับบันทึกเวลาในการประมวลผลแต่ละหน้า"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        print(f"--- PATH: {request.path} | PROCESS TIME: {duration:.2f}s ---")
        return response


class UpdateLastSeenMiddleware:
    """อัปเดตเวลาใช้งานล่าสุดของผู้ใช้ที่ล็อกอินอยู่"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = timezone.now()
            last_seen = getattr(request.user, "last_seen", None)

            if not last_seen or (current_time - last_seen).total_seconds() >= 60:
                request.user.__class__.objects.filter(pk=request.user.pk).update(last_seen=current_time)
                request.user.last_seen = current_time

        return self.get_response(request)
