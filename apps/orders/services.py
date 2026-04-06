# apps/orders/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.wallets.models import Wallet
from apps.store.models import Product
from .models import Order, OrderItem

@transaction.atomic
def place_order_service(user, product_id):
    # ดึงข้อมูลพร้อมล็อกแถวใน SQL เพื่อป้องกันการซื้อซ้ำซ้อนพร้อมกัน
    product = Product.objects.select_for_update().get(id=product_id)
    wallet = Wallet.objects.select_for_update().get(user=user)

    if product.stock < 1: 
        raise ValidationError("ขออภัย สินค้าชิ้นนี้หมดจากคลังแล้ว")
    if wallet.balance < product.price: 
        raise ValidationError("ยอดเครดิตในกระเป๋าของคุณไม่เพียงพอ")

    # 1. ทำการหักเงิน
    wallet.balance -= product.price
    wallet.save()

    # 2. ลดสต็อกสินค้า
    product.stock -= 1
    product.save()

    # 3. สร้างข้อมูลใบสั่งซื้อ
    order = Order.objects.create(
        buyer=user, 
        total_price=product.price,
        status='success'
    )

    # 4. บันทึกรายการสินค้าที่สั่งซื้อ
    OrderItem.objects.create(
        order=order, 
        product=product, 
        quantity=1, 
        price=product.price
    )

    return order