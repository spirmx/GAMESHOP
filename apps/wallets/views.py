from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Wallet, WalletTransaction
from apps.orders.models import Order
from django.http import HttpResponse

@login_required
def wallet_home_view(request):
    """ 🏠 หน้าหลักของกระเป๋าเงิน (แสดงยอดเงินและประวัติ) """
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')[:10]
    
    return render(request, 'wallet/wallet_home.html', {
        'wallet': wallet,
        'transactions': transactions
    })

@login_required
def top_up(request):
    """ 💳 หน้าเลือกแพ็กเกจเติมเงิน """
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    context = {
        'price_list': [100, 300, 500, 1000, 3000, 5000],
        'wallet': wallet
    }
    return render(request, 'wallet/top_up.html', context)

@login_required
def process_topup(request):
    """ 🔄 หน้าแสดง QR Code/ยืนยันการเติมเงิน """
    if request.method == "POST":
        amount = request.POST.get('amount')
        context = {
            'amount': amount, 
            'transaction_id': f"PY-{request.user.id}-RCG"
        }
        return render(request, 'wallet/payment_confirmation.html', context)
    
    return redirect('wallets:top_up')

@login_required
def payment_page(request, order_id):
    """ 💰 ฟังก์ชันหักเงินจริงออกจาก Wallet """
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST" and request.POST.get('method') == 'wallet':
        try:
            with transaction.atomic():
                # ป้องกัน Race Condition
                curr_wallet = Wallet.objects.select_for_update().get(id=wallet.id)
                
                if curr_wallet.balance >= order.total_price:
                    # 1. หักเงิน
                    curr_wallet.balance -= order.total_price
                    curr_wallet.save()
                    
                    # 2. บันทึกประวัติ (ใช้ฟิลด์ timestamp อัตโนมัติ)
                    WalletTransaction.objects.create(
                        wallet=curr_wallet, 
                        transaction_type='WITHDRAW', 
                        amount=order.total_price
                    )
                    
                    # 3. จบ Order
                    order.status = 'SUCCESS'
                    order.save()
                    
                    messages.success(request, "✨ AUTHORIZATION GRANTED: ชำระเงินสำเร็จแล้ว!")
                    return redirect('orders:order_detail', order_id=order.id)
                else:
                    messages.error(request, "❌ INSUFFICIENT CREDITS: ยอดเงินไม่เพียงพอ")
                    return redirect('wallets:top_up')
                    
        except Exception as e:
            messages.error(request, f"⚠️ SYSTEM ERROR: {str(e)}")
            
    return render(request, 'wallet/payment.html', {'order': order, 'wallet': wallet})