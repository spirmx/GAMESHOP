from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.cart.models import Cart
from .models import Order, OrderItem

@login_required
def checkout(request):
    """ แสดงหน้าสรุปรายการสินค้าก่อนชำระเงิน """
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return redirect('cart:cart_detail')
    return render(request, 'orders/checkout.html', {'cart': cart})

@login_required
def place_order(request):
    """ รับค่าจากฟอร์ม Checkout เพื่อสร้าง Order จริง และหักสต็อก """
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        
        # 1. เช็กสต็อกอีกรอบก่อนให้ซื้อ
        for item in cart.items.all():
            if item.product.stock < item.quantity:
                messages.error(request, f"สั่งซื้อล้มเหลว! ไอเท็ม '{item.product.title}' มีสต็อกไม่พอ (เหลือ {item.product.stock} ชิ้น)")
                return redirect('cart:cart_detail')
        
        # 2. สร้าง Order หลัก
        order = Order.objects.create(
            buyer=request.user, 
            total_price=cart.total_price, 
            status='PENDING'
        )
        
        # 3. ย้ายสินค้าจาก CartItem ไป OrderItem และ "ตัดสต็อก"
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price, 
                quantity=item.quantity
            )
            # 4. หักลบจำนวนสินค้าคงคลัง
            item.product.stock -= item.quantity
            item.product.save()
        
        # 5. ล้างตะกร้า
        cart.items.all().delete()
        
        # ✅ แก้ไขจาก 'wallet:' เป็น 'wallets:' ให้ตรงกับ Namespace ในไฟล์หลัก
        return redirect('wallets:payment_page', order_id=order.id)
    
    return redirect('cart:cart_detail')

@login_required
def order_detail(request, order_id):
    """ แสดงรายละเอียดใบเสร็จ """
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def order_list(request):
    """ รายการประวัติสั่งซื้อ """
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def all_transactions(request):
    """ ศูนย์รวมประวัติการสั่งซื้อ (สำหรับ Commander) """
    if not request.user.is_staff:
        return redirect('home')
        
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'orders/all_transactions.html', {'orders': orders, 'page_title': "Global Transaction History"})