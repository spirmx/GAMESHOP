from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Wallet, WalletTransaction
from apps.orders.models import Order

@login_required
def top_up(request):
    """ 💳 หน้าเลือกแพ็กเกจเติมเงิน (Midasbuy Style) """
    context = {
        'price_list': [100, 300, 500, 1000, 3000, 5000],
        'wallet': request.user.wallet
    }
    return render(request, 'wallet/top_up.html', context)

@login_required
def process_topup(request):
    """ 🔄 ประมวลผลการกดเติมเงินเพื่อไปหน้า QR Code """
    if request.method == "POST":
        amount = request.POST.get('amount')
        context = {
            'amount': amount, 
            'transaction_id': f"PY-{request.user.id}-RCG"
        }
        return render(request, 'wallet/payment_confirmation.html', context)
    return redirect('wallet:top_up')

@login_required
def payment_page(request, order_id):
    """ 💰 หักเงินจาก Wallet จริงสำหรับซื้อสินค้า """
    # 🚨 แก้ไขจุดที่ 1: เปลี่ยนจาก user= เป็น buyer= ตามที่ระบบแจ้ง Choices มาให้
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    # ดึงกระเป๋าเงิน (ใช้ get_or_create เพื่อความปลอดภัย)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST" and request.POST.get('method') == 'wallet':
        try:
            # ใช้ transaction.atomic เพื่อความปลอดภัยสูงสุดในการหักเงิน
            with transaction.atomic():
                # select_for_update() ป้องกันการหักเงินซ้ำซ้อนในเวลาเดียวกัน (Race Condition)
                curr_wallet = Wallet.objects.select_for_update().get(id=wallet.id)
                
                if curr_wallet.balance >= order.total_price:
                    # 1. หักเงินออกจากกระเป๋า
                    curr_wallet.balance -= order.total_price
                    curr_wallet.save()
                    
                    # 2. บันทึกประวัติการทำรายการ
                    WalletTransaction.objects.create(
                        wallet=curr_wallet, 
                        transaction_type='WITHDRAW', 
                        amount=order.total_price
                    )
                    
                    # 3. อัปเดตสถานะการสั่งซื้อ
                    order.status = 'SUCCESS'
                    order.save()
                    
                    messages.success(request, "✨ AUTHORIZATION GRANTED: ชำระเงินสำเร็จแล้ว!")
                    return redirect('orders:order_detail', order_id=order.id)
                else:
                    messages.error(request, "❌ INSUFFICIENT CREDITS: ยอดเงินไม่เพียงพอ")
                    return redirect('wallet:top_up')
                    
        except Exception as e:
            messages.error(request, f"⚠️ SYSTEM ERROR: {str(e)}")
            
    return render(request, 'wallet/payment.html', {'order': order, 'wallet': wallet})