from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.store.models import Product

from .models import Cart, CartItem


def _product_sale_guard_message(product):
    if not product.game_is_available_for_sale:
        game_name = product.related_game.name if product.related_game else "เกมนี้"
        return f"{game_name} อยู่ในสถานะไม่พร้อมขายชั่วคราว"
    if not product.is_active:
        return f"{product.title} อยู่ในสถานะไม่พร้อมขายชั่วคราว"
    if product.stock <= 0:
        return f"{product.title} สินค้าหมดชั่วคราว"
    return f"{product.title} ยังไม่พร้อมขาย"


def build_delivery_data(product, payload):
    if product.is_code_product:
        return {}

    primary_label = (product.account_input_label or "Player ID / UID").strip()
    primary_help = (product.account_input_help or "Use this info for in-game top up delivery.").strip()
    secondary_label = (product.account_input_secondary_label or "").strip()
    secondary_help = (product.account_input_secondary_help or "").strip()

    primary_value = (payload.get("account_input_value") or payload.get("player_uid") or "").strip()
    secondary_value = (payload.get("account_input_secondary_value") or "").strip()

    if not primary_value:
        raise ValidationError(f"Please enter {primary_label}")

    delivery_data = {
        "primary_label": primary_label,
        "primary_value": primary_value,
        "primary_help": primary_help,
    }

    if secondary_label:
        if not secondary_value:
            raise ValidationError(f"Please enter {secondary_label}")
        delivery_data.update(
            {
                "secondary_label": secondary_label,
                "secondary_value": secondary_value,
                "secondary_help": secondary_help,
            }
        )

    return delivery_data


@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, "cart/cart_detail.html", {"cart": cart})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    if not product.is_available_for_sale:
        message = _product_sale_guard_message(product)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": message}, status=400)
        messages.error(request, message)
        return redirect(request.META.get("HTTP_REFERER", "cart:cart_detail"))

    qty_input = request.POST.get("quantity", "1")
    qty = int(qty_input) if qty_input.isdigit() else 1

    try:
        delivery_data = build_delivery_data(product, request.POST)
    except ValidationError as exc:
        messages.error(request, str(exc))
        return redirect(request.META.get("HTTP_REFERER", "cart:cart_detail"))

    if product.stock >= qty:
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if created:
            cart_item.quantity = qty
        else:
            cart_item.quantity += qty

        if delivery_data:
            cart_item.delivery_data = delivery_data

        cart_item.save()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "status": "success",
                    "quantity": cart_item.quantity,
                    "item_total": float(cart_item.subtotal),
                    "cart_total": float(cart.total_price),
                }
            )

        if "buy_now" in request.POST:
            return redirect("orders:checkout")

        messages.success(request, f"เพิ่ม {product.title} จำนวน {qty} ชิ้นลงในตะกร้าแล้ว")
    else:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": "สต็อกไม่พอ"}, status=400)
        messages.error(request, f"ขออภัย สต็อกไม่พอ (เหลือ {product.stock} ชิ้น)")

    return redirect("cart:cart_detail")


@login_required
def decrease_quantity(request, product_id):
    if request.method == "POST":
        cart = request.user.cart
        product = get_object_or_404(Product, id=product_id)

        if not product.is_available_for_sale:
            messages.error(request, _product_sale_guard_message(product))
            return redirect(request.META.get("HTTP_REFERER", "home"))
        cart_item = cart.items.filter(product=product).first()

        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()

                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "status": "success",
                            "quantity": cart_item.quantity,
                            "item_total": float(cart_item.subtotal),
                            "cart_total": float(cart.total_price),
                        }
                    )
            else:
                cart_item.delete()
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"status": "removed"})
                messages.info(request, f"ลบ {product.title} ออกจากตะกร้าแล้ว")

    return redirect("cart:cart_detail")


@login_required
def remove_from_cart(request, product_id):
    if request.method == "POST":
        cart = request.user.cart
        product = get_object_or_404(Product, id=product_id)
        cart_item = cart.items.filter(product=product).first()

        if cart_item:
            cart_item.delete()
            messages.info(request, "ลบสินค้าออกจากตะกร้าแล้ว")

    return redirect("cart:cart_detail")


@login_required
def add_to_cart_direct(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")

        if not product_id:
            messages.error(request, "กรุณาเลือกแพ็กเกจที่ต้องการ")
            return redirect(request.META.get("HTTP_REFERER", "home"))

        product = get_object_or_404(Product, id=product_id)

        try:
            delivery_data = build_delivery_data(product, request.POST)
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect(request.META.get("HTTP_REFERER", "home"))

        if product.is_available_for_sale:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart.items.all().delete()
            CartItem.objects.create(cart=cart, product=product, quantity=1, delivery_data=delivery_data)
            return redirect("orders:checkout")

        messages.error(request, "สินค้าหมดสต็อก")

    return redirect("home")
