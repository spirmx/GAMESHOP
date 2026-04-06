from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.store.models import Product  
from .models import Cart, CartItem

@login_required
def cart_detail(request):
    """ แสดงหน้าตะกร้าสินค้า """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart/cart_detail.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    """ Action: เพิ่มสินค้าลงตะกร้า (ปุ่ม +) """
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    if product.stock > 0:
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        messages.success(request, f"เพิ่ม {product.title} ลงในตะกร้าแล้ว")
    else:
        messages.error(request, "ขออภัย สินค้าชิ้นนี้หมดสต็อก")
        
    return redirect(request.META.get('HTTP_REFERER', 'cart:cart_detail'))

@login_required
def decrease_quantity(request, product_id):
    """ Action: ลดจำนวนสินค้าลง 1 ชิ้น (ปุ่ม -) """
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        product = get_object_or_404(Product, id=product_id)
        cart_item = cart.items.filter(product=product).first()
        
        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                messages.info(request, f"ลดจำนวน {product.title} เหลือ {cart_item.quantity} ชิ้น")
            else:
                cart_item.delete()
                messages.info(request, f"ลบ {product.title} ออกจากตะกร้าแล้ว")
                
    return redirect('cart:cart_detail')

@login_required
def remove_from_cart(request, product_id):
    """ Action: ลบสินค้าออกจากตะกร้าทั้งหมด (ปุ่มถังขยะ) """
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        product = get_object_or_404(Product, id=product_id)
        cart_item = cart.items.filter(product=product).first()
        
        if cart_item:
            cart_item.delete()
            messages.info(request, "ลบสินค้าออกจากตะกร้าแล้ว")
            
    return redirect('cart:cart_detail')

@login_required
def add_to_cart_direct(request):
    """ Action: กดซื้อแพ็กเกจทันทีแบบ Midasbuy """
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