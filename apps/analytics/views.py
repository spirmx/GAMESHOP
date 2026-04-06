from django.shortcuts import render
from django.db.models import Sum, Count
from django.contrib.auth.decorators import user_passes_test
from apps.orders.models import Order
from apps.store.models import Category, Product

@user_passes_test(lambda u: u.is_staff, login_url='login')
def dashboard(request):
    total_sales = Order.objects.filter(status='success').aggregate(Sum('total_price'))['total_price__sum'] or 0
    category_summary = Category.objects.annotate(product_count=Count('products'))
    recent_orders = Order.objects.select_related('buyer').order_by('-created_at')[:10]
    stats = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
    }
    
    context = {
        'total_sales': total_sales,
        'category_summary': category_summary,
        'recent_orders': recent_orders,
        'stats': stats,
    }
    
    return render(request, 'analytics/dashboard.html', context)