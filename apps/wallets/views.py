from decimal import Decimal, InvalidOperation
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.orders.models import Order
from .models import Wallet, WalletTransaction


TOPUP_PRICE_LIST = [50, 90, 100, 200, 300, 400, 500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
SUCCESS_ORDER_STATUSES = ["SUCCESS", "PAID"]


def _ensure_identity_ready(request):
    user = request.user

    if not user.has_identity_profile:
        messages.warning(
            request,
            "กรุณากรอกชื่อจริง นามสกุล อีเมล และเบอร์โทรศัพท์ให้ครบในหน้าแก้ไขโปรไฟล์ก่อนเติมเงิน",
        )
        return redirect("users:profile_edit")

    if not user.verification_complete:
        messages.warning(
            request,
            "กรุณายืนยันข้อมูลติดต่อในหน้าแก้ไขโปรไฟล์ก่อนเติมเงิน",
        )
        return redirect("users:profile_edit")

    return None


@login_required
def wallet_home_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by("-timestamp")[:15]

    return render(
        request,
        "wallet/wallet_home.html",
        {
            "wallet": wallet,
            "transactions": transactions,
        },
    )


@login_required
def top_up(request):
    identity_block = _ensure_identity_ready(request)
    if identity_block:
        return identity_block

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    return render(
        request,
        "wallet/top_up.html",
        {
            "wallet": wallet,
            "price_list": TOPUP_PRICE_LIST,
        },
    )


@login_required
def process_topup(request):
    identity_block = _ensure_identity_ready(request)
    if identity_block:
        return identity_block

    if request.method != "POST":
        return redirect("wallets:top_up")

    amount_raw = (request.POST.get("amount") or "").strip()
    method = (request.POST.get("method") or "promptpay").strip().lower()
    allowed_methods = {"promptpay", "truemoney", "card", "crypto"}
    if method not in allowed_methods:
        method = "promptpay"

    try:
        amount = Decimal(amount_raw)
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        messages.error(request, "จำนวนเงินไม่ถูกต้อง")
        return redirect("wallets:top_up")

    if int(amount) not in TOPUP_PRICE_LIST:
        messages.error(request, "ไม่พบแพ็กเกจเติมเงินที่เลือก")
        return redirect("wallets:top_up")

    transaction_id = f"PY-{uuid.uuid4().hex[:8].upper()}-{request.user.id}"

    request.session["demo_topup"] = {
        "amount": str(amount),
        "method": method,
        "txn_id": transaction_id,
    }
    request.session.modified = True

    return render(
        request,
        "wallet/payment_confirmation.html",
        {
            "amount": amount,
            "method": method,
            "transaction_id": transaction_id,
        },
    )


@login_required
def confirm_topup(request):
    identity_block = _ensure_identity_ready(request)
    if identity_block:
        return identity_block

    if request.method != "POST":
        return redirect("wallets:wallet_home")

    data = request.session.get("demo_topup")
    if not data:
        messages.error(request, "รายการหมดอายุ กรุณาทำรายการใหม่อีกครั้ง")
        return redirect("wallets:top_up")

    try:
        amount = Decimal(data["amount"])
        method = str(data["method"]).upper()

        with transaction.atomic():
            wallet, _ = Wallet.objects.select_for_update().get_or_create(user=request.user)
            wallet.balance += amount
            wallet.save(update_fields=["balance"])

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="DEPOSIT",
                amount=amount,
                note=f"เติมเครดิตแบบเดโม่ ({method})",
            )

        request.session.pop("demo_topup", None)
        messages.success(request, f"เติมเครดิตสำเร็จ เพิ่ม ฿{amount:,.2f} เข้ากระเป๋าแล้ว")

    except (InvalidOperation, KeyError, TypeError, ValueError):
        messages.error(request, "ข้อมูลรายการไม่ถูกต้อง กรุณาทำรายการใหม่")
        request.session.pop("demo_topup", None)
    except Exception:
        messages.error(request, "ระบบไม่สามารถเติมเครดิตได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง")

    return redirect("wallets:wallet_home")


@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if order.status in SUCCESS_ORDER_STATUSES:
        messages.info(request, "คำสั่งซื้อนี้ชำระเงินเรียบร้อยแล้ว")
        return redirect("orders:order_detail", order_id=order.id)

    missing_amount = Decimal("0.00")
    if wallet.balance < order.total_price:
        missing_amount = order.total_price - wallet.balance

    if request.method == "POST":
        method = (request.POST.get("method") or "").strip()
        is_demo_override = method == "demo_override"

        if not is_demo_override and wallet.balance < order.total_price:
            messages.error(request, f"ยอดเครดิตไม่พอ ขาดอีก ฿{missing_amount:,.2f}")
            return redirect("wallets:top_up")

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=order.id, buyer=request.user)
                wallet = Wallet.objects.select_for_update().get(user=request.user)

                if order.status in SUCCESS_ORDER_STATUSES:
                    messages.info(request, "คำสั่งซื้อนี้ถูกชำระแล้ว")
                    return redirect("orders:order_detail", order_id=order.id)

                if not is_demo_override:
                    if wallet.balance < order.total_price:
                        messages.error(request, "ยอดเครดิตไม่เพียงพอสำหรับการชำระเงิน")
                        return redirect("wallets:top_up")

                    wallet.balance -= order.total_price
                    wallet.save(update_fields=["balance"])

                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type="WITHDRAW",
                    amount=order.total_price,
                    note=f"ชำระคำสั่งซื้อ #{order.id}{' (Demo Override)' if is_demo_override else ''}",
                )

                order.status = "SUCCESS"
                order.save(update_fields=["status"])

            messages.success(request, "ชำระเงินสำเร็จ")
            return redirect("orders:order_detail", order_id=order.id)

        except Exception:
            messages.error(request, "ไม่สามารถดำเนินการชำระเงินได้ กรุณาลองใหม่อีกครั้ง")

    return render(
        request,
        "wallet/payment.html",
        {
            "order": order,
            "wallet": wallet,
            "missing_amount": missing_amount,
        },
    )
