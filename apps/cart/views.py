from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.store.models import Product  
from .models import Cart, CartItem

@login_required
def cart_detail(request):
    """ 🛒 แสดงหน้าตะกร้าสินค้าหลัก """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart/cart_detail.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    """ ➕ Action: เพิ่มสินค้าลงตะกร้า (รองรับการเลือกจำนวน และปุ่ม BUY NOW) """
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    # 1. ดึงค่าจำนวนจากหน้าเว็บ (รับจาก input name="quantity")
    qty_input = request.POST.get('quantity', '1')
    qty = int(qty_input) if qty_input.isdigit() else 1
    
    if product.stock >= qty:
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if created:
            # ถ้าเพิ่งเพิ่มชิ้นนี้ครั้งแรก ให้ใส่จำนวนตามที่เลือกมา
            cart_item.quantity = qty
        else:
            # ✅ ถ้ามีในตะกร้าอยู่แล้ว ให้ "บวกเพิ่ม" ตามจำนวนที่ส่งมา
            cart_item.quantity += qty
            
        cart_item.save()
        
        # 2. ระบบ AJAX: สำหรับการกดบวก/ลบในหน้าตะกร้าแบบลื่นๆ
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'quantity': cart_item.quantity,
                'item_total': float(cart_item.subtotal), # ใช้ฟิลด์ subtotal จากโมเดล
                'cart_total': float(cart.total_price)
            })
            
        # 3. 🚀 ตรวจสอบปุ่ม "BUY NOW": ถ้ากดให้ข้ามไปหน้า Checkout ทันที
        if 'buy_now' in request.POST:
            return redirect('orders:checkout')

        # สำหรับการกด Add to Cart ปกติจากหน้าอื่น
        messages.success(request, f"เพิ่ม {product.title} จำนวน {qty} ชิ้นลงในตะกร้าแล้ว")
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'สต็อกไม่พอ'}, status=400)
        messages.error(request, f"ขออภัย สต็อกไม่พอ (เหลือ {product.stock} ชิ้น)")
        
    return redirect('cart:cart_detail')

@login_required
def decrease_quantity(request, product_id):
    """ ➖ Action: ลดจำนวนสินค้า (AJAX Support) """
    if request.method == 'POST':
        cart = request.user.cart
        product = get_object_or_404(Product, id=product_id)
        cart_item = cart.items.filter(product=product).first()
        
        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'quantity': cart_item.quantity,
                        'item_total': float(cart_item.subtotal),
                        'cart_total': float(cart.total_price)
                    })
            else:
                cart_item.delete()
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'removed'})
                messages.info(request, f"ลบ {product.title} ออกจากตะกร้าแล้ว")
                
    return redirect('cart:cart_detail')

@login_required
def remove_from_cart(request, product_id):
    """ 🗑️ Action: ลบสินค้าออกจากตะกร้าทัังหมด (ปุ่มถังขยะ) """
    if request.method == 'POST':
        cart = request.user.cart
        product = get_object_or_404(Product, id=product_id)
        cart_item = cart.items.filter(product=product).first()
        
        if cart_item:
            cart_item.delete()
            messages.info(request, "ลบสินค้าออกจากตะกร้าแล้ว")
            
    return redirect('cart:cart_detail')

@login_required
def add_to_cart_direct(request):
    """ 🚀 Action: ระบบ Fast Checkout (ล้างตะกร้าเก่าแล้วซื้อชิ้นใหม่ทันที) """
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        player_uid = request.POST.get('player_uid')
        
        if not product_id:
            messages.error(request, "กรุณาเลือกแพ็กเกจที่ต้องการ")
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        product = get_object_or_404(Product, id=product_id)
        
        if product.stock > 0:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart.items.all().delete() # ล้างตะกร้าก่อน
            CartItem.objects.create(cart=cart, product=product, quantity=1)
            
            if player_uid:
                request.session['player_uid'] = player_uid
                
            return redirect('orders:checkout')
        else:
            messages.error(request, "สินค้าหมดสต็อก")
            
    return redirect('home')