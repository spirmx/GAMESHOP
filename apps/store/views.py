from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Game, Product, Category

def home(request):
    """ หน้าแรก: Dashboard ข่าวสาร และรายการเลือกเกม """
    query = request.GET.get('q', '') 
    cat_name = request.GET.get('cat', '') 
    
    games = Game.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    
    # 🔍 ค้นหาเกมและไอเท็ม
    if query:
        games = games.filter(name__icontains=query)
        products = products.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    
    # 🗂️ กรองตามหมวดหมู่ (สำหรับหน้า Home)
    if cat_name:
        products = products.filter(category__name__icontains=cat_name).distinct()
        # ✅ ใช้ categories__name ตามโครงสร้างโมเดล Game
        games = games.filter(categories__name__icontains=cat_name).distinct()

    context = {
        'games': games,
        'products': products[:4],  # โชว์แค่ 4 ชิ้นยอดฮิตในหน้า Home
        'categories': Category.objects.all(), 
        'query': query,
        'selected_cat': cat_name
    }
    return render(request, 'store/home.html', context)

def product_list(request):
    """ หน้า Store รวม: ระบบค้นหา, กรองหมวดหมู่หลัก (PC/Mobile) และกรองราคา """
    products = Product.objects.filter(is_active=True)
    
    # 🔍 1. ค้นหาจากช่อง Search (q)
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(title__icontains=query) | 
            Q(category__name__icontains=query) |
            Q(category__game__name__icontains=query)
        )

    # 🗂️ 2. กรองตามหมวดหมู่ (cat) - รองรับทั้งหมวดหลัก PC/Mobile และหมวดย่อย
    cat = request.GET.get('cat')
    if cat:
        products = products.filter(
            Q(category__name__icontains=cat) | 
            Q(category__parent__name__icontains=cat) # กรองผ่านหมวดหลัก
        ).distinct()

    # 💰 3. กรองตามราคา (min_price, max_price)
    min_p = request.GET.get('min_price')
    max_p = request.GET.get('max_price')
    if min_p: products = products.filter(price__gte=min_p)
    if max_p: products = products.filter(price__lte=max_p)

    # 📉 4. ระบบเรียงลำดับ (sort)
    sort = request.GET.get('sort')
    if sort == 'price_asc': products = products.order_by('price')
    elif sort == 'price_desc': products = products.order_by('-price')
    else: products = products.order_by('-id')

    context = {
        'products': products,
        'categories': Category.objects.filter(parent=None), # ส่งเฉพาะหมวดหลักไปทำ Sidebar
    }
    return render(request, 'store/product_list.html', context)

def game_detail(request, slug):
    """ หน้ารายละเอียดเกม: แสดงไอเท็มในเกมนั้นๆ โดยเอาของที่มีสต็อกขึ้นก่อน """
    game = get_object_or_404(Game, slug=slug)
    # 🚨 เรียงลำดับสต็อก: ของไม่หมด (-stock) อยู่บน, ราคาถูกอยู่หน้า
    products = Product.objects.filter(
        category__game=game, 
        is_active=True
    ).order_by('-stock', 'price')
    
    context = {
        'game': game,
        'products': products
    }
    return render(request, 'store/game_detail.html', context)