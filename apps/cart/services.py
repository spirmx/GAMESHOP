from django.db import transaction
from .models import Cart, CartItem

def add_to_cart_service(user, product, quantity=1):
    """ฟังก์ชันเพิ่มสินค้าลงตะกร้าแบบปลอดภัย"""
    # ตรวจสอบหรือสร้างตะกร้าสำหรับ User
    cart, _ = Cart.objects.get_or_create(user=user)
    
    # ตรวจสอบว่ามีสินค้านี้ในตะกร้าหรือยัง
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += int(quantity)
    else:
        cart_item.quantity = int(quantity)
        
    cart_item.save()
    return cart_item

def remove_from_cart_service(user, product_id):
    """ลบสินค้าออกจากตะกร้า"""
    CartItem.objects.filter(cart__user=user, product_id=product_id).delete()

def clear_cart_service(user):
    """ล้างตะกร้าหลังสั่งซื้อสำเร็จ"""
    CartItem.objects.filter(cart__user=user).delete()