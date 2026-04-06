def is_seller(user):
    """เช็คสิทธิ์การเป็นผู้ขายแบบ Function-based"""
    return user.is_authenticated and user.is_seller

def is_admin_or_staff(user):
    """เช็คสิทธิ์ผู้ดูแลระบบ"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)