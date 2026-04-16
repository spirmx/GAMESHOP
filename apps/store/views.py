from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Game, Product, Category

def home(request):
    """ 🏠 หน้าแรก: Dashboard ข่าวสาร และรายการเลือกเกม """
    query = request.GET.get('q', '') 
    cat_name = request.GET.get('cat', '') 
    
    games = Game.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    
    # 🔍 ค้นหาเกมและไอเท็มจากช่อง Search
    if query:
        games = games.filter(name__icontains=query)
        products = products.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    
    # 🗂️ กรองตามหมวดหมู่ (เช่น PC FPS, Mobile MOBA)
    if cat_name:
        products = products.filter(category__name__icontains=cat_name).distinct()
        games = games.filter(categories__name__icontains=cat_name).distinct()

    context = {
        'games': games,
        'products': products[:4],  # แสดงเฉพาะ 4 ชิ้นแรกที่เป็นสินค้าแนะนำ
        'categories': Category.objects.all(), 
        'query': query,
        'selected_cat': cat_name
    }
    return render(request, 'store/home.html', context)

def product_list(request):
    """ 🛒 หน้า Store รวม: ระบบค้นหา, กรองหมวดหมู่ และกรองราคา """
    products = Product.objects.filter(is_active=True)
    
    # 🔍 1. ค้นหาจากช่อง Search
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(title__icontains=query) | 
            Q(category__name__icontains=query) |
            Q(category__game__name__icontains=query)
        )

    # 🗂️ 2. กรองตามหมวดหมู่ (PC/Mobile/Game Type)
    cat = request.GET.get('cat')
    if cat:
        products = products.filter(
            Q(category__name__icontains=cat) | 
            Q(category__parent__name__icontains=cat)
        ).distinct()

    # 💰 3. กรองตามช่วงราคา
    min_p = request.GET.get('min_price')
    max_p = request.GET.get('max_price')
    if min_p: products = products.filter(price__gte=min_p)
    if max_p: products = products.filter(price__lte=max_p)

    # 📉 4. ระบบเรียงลำดับราคา
    sort = request.GET.get('sort')
    if sort == 'price_asc': products = products.order_by('price')
    elif sort == 'price_desc': products = products.order_by('-price')
    else: products = products.order_by('-id')

    context = {
        'products': products,
        'categories': Category.objects.filter(parent=None), 
    }
    return render(request, 'store/product_list.html', context)

def game_detail(request, slug):
    """ 🎮 หน้ารายละเอียดเกม: แสดงรายการไอเท็มทั้งหมดในเกมนั้นๆ """
    game = get_object_or_404(Game, slug=slug)
    # แสดงสินค้าที่มีสต็อกก่อน และเรียงตามราคาจากน้อยไปมาก
    products = Product.objects.filter(
        category__game=game, 
        is_active=True
    ).order_by('-stock', 'price')
    
    context = {
        'game': game,
        'products': products
    }
    return render(request, 'store/game_detail.html', context)

def product_detail(request, product_id):
    """ 🔍 ✅ ฟังก์ชันใหม่: ดึงข้อมูลไอเท็มชิ้นเดียวมาแสดงในหน้า Authorization """
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})