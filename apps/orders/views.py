from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.cart.models import Cart
from apps.store.models import Product

from .models import Order, OrderItem


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return redirect("cart:cart_detail")
    for item in cart.items.select_related("product", "product__game", "product__category__game"):
        if not item.product.is_available_for_sale:
            messages.error(request, f"{item.product.title} ไม่พร้อมขายแล้ว กรุณาตรวจสอบตะกร้าอีกครั้ง")
            return redirect("cart:cart_detail")
    return render(request, "orders/checkout.html", {"cart": cart})


@login_required
def payment_confirmation(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return redirect("cart:cart_detail")

    for item in cart.items.select_related("product", "product__game", "product__category__game"):
        if not item.product.is_available_for_sale:
            messages.error(request, f"{item.product.title} ไม่พร้อมขายแล้ว กรุณาตรวจสอบตะกร้าอีกครั้ง")
            return redirect("cart:cart_detail")

    user_wallet = getattr(request.user, "wallet", None)
    if not user_wallet or user_wallet.balance < cart.total_price:
        messages.error(request, "ยอดเงินของคุณไม่เพียงพอ กรุณาเติมเงินก่อนทำรายการ")
        return redirect("orders:checkout")

    return render(request, "wallet/payment.html", {"cart": cart, "wallet": user_wallet})


@login_required
def place_order(request):
    if request.method != "POST":
        return redirect("cart:cart_detail")

    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return redirect("cart:cart_detail")

    with transaction.atomic():
        user_wallet = getattr(request.user, "wallet", None)
        if not user_wallet or user_wallet.balance < cart.total_price:
            messages.error(request, "ยอดเงินไม่พอ กรุณาเติมเงิน")
            return redirect("orders:checkout")

        locked_products = {}
        for item in cart.items.select_related("product").all():
            product = Product.objects.select_for_update().get(pk=item.product_id)
            locked_products[item.product_id] = product

            if not product.game_is_available_for_sale:
                messages.error(request, f"เกมของสินค้า '{product.title}' ไม่พร้อมขายชั่วคราว")
                return redirect("cart:cart_detail")

            if not product.is_active:
                messages.error(request, f"สินค้า '{product.title}' ไม่พร้อมขายชั่วคราว")
                return redirect("cart:cart_detail")

            if product.stock < item.quantity:
                messages.error(request, f"สินค้า '{product.title}' มีสต็อกไม่พอ")
                return redirect("cart:cart_detail")

            if product.is_account_product and not item.delivery_data.get("primary_value"):
                messages.error(
                    request,
                    f"กรุณากรอกข้อมูลสำหรับสินค้า '{product.title}' ให้ครบ",
                )
                return redirect("cart:cart_detail")

        user_wallet.balance -= cart.total_price
        user_wallet.save()

        order = Order.objects.create(
            buyer=request.user,
            total_price=cart.total_price,
            status="success",
        )

        for item in cart.items.select_related("product").all():
            product = locked_products[item.product_id]
            product.stock -= item.quantity
            product.sold_count += item.quantity
            product.save(update_fields=["stock", "sold_count"])

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price=product.price,
                fulfillment_type=product.fulfillment_type,
                delivery_data=item.delivery_data,
                delivered_codes="",
            )

        cart.items.all().delete()

    messages.success(request, "ชำระเงินสำเร็จ")
    return redirect("orders:order_detail", order_id=order.id)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def order_list(request):
    orders = (
        Order.objects.filter(buyer=request.user)
        .prefetch_related("items__product__category__game", "items__product__game")
        .order_by("-created_at")
    )
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def all_transactions(request):
    if not request.user.is_staff:
        return redirect("home")
    orders = (
        Order.objects.all()
        .prefetch_related("items__product__category__game", "items__product__game")
        .order_by("-created_at")
    )
    return render(request, "orders/all_transactions.html", {"orders": orders})
