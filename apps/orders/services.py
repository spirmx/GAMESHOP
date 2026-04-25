from django.db import transaction
from django.core.exceptions import ValidationError
from apps.wallets.models import Wallet, WalletTransaction # ✅ เพิ่ม Import WalletTransaction
from apps.store.models import Product
from .models import Order, OrderItem

@transaction.atomic
def place_order_service(user, product_id):
    """
    🛒 ระบบสั่งซื้อสินค้าแบบ Direct (ซื้อชิ้นเดียว)
    """
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

    # ✅ 2. บันทึกประวัติการหักเงิน (เพื่อให้โชว์ในหน้า Wallet)
    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type='WITHDRAW',
        amount=product.price,
        note=f"Direct Purchase: {product.title}"
    )

    # 3. ลดสต็อกสินค้า
    product.stock -= 1
    product.save()

    # 4. สร้างข้อมูลใบสั่งซื้อ (ใช้ตัวพิมพ์ใหญ่ให้ตรงกับมาตรฐาน)
    order = Order.objects.create(
        buyer=user, 
        total_price=product.price,
        status='SUCCESS' # ✅ แก้เป็นตัวพิมพ์ใหญ่
    )

    # 5. บันทึกรายการสินค้าที่สั่งซื้อ
    OrderItem.objects.create(
        order=order, 
        product=product, 
        quantity=1, 
        price=product.price
    )

    return order


def process_refund(order):
    """
    🔄 ฟังก์ชันสำหรับคืนเงิน (Refund) เข้า Wallet อัตโนมัติในกรณีที่ออเดอร์ถูกยกเลิก
    ใช้ transaction.atomic() เพื่อป้องกันเงินหายระหว่างระบบขัดข้อง
    """
    # ✅ เช็คแบบไม่สนตัวพิมพ์เล็ก/ใหญ่ เพื่อความชัวร์
    if order.status.upper() in ['PAID', 'SUCCESS']:
        try:
            with transaction.atomic():
                # 1. ล็อค Wallet เพื่ออัปเดตยอดเงิน และคืนเงิน
                wallet = Wallet.objects.select_for_update().get(user=order.buyer)
                wallet.balance += order.total_price
                wallet.save()

                # 2. บันทึกประวัติว่าได้รับเงินคืน
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='DEPOSIT',
                    amount=order.total_price,
                    note=f"System Refund: Cancelled Order #{order.id}"
                )
                
                # ✅ 3. คืนสต็อกสินค้ากลับเข้าคลัง
                for item in order.items.all():
                    product = Product.objects.select_for_update().get(id=item.product.id)
                    product.stock += item.quantity
                    product.save()

                # 4. เปลี่ยนสถานะออเดอร์เป็น CANCELLED
                order.status = 'CANCELLED'
                order.save()
                
            return True, "Refund processed successfully."
        except Exception as e:
            return False, f"Refund Failed: {str(e)}"
    
    return False, "Order is not eligible for a refund."