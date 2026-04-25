from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay
from django.contrib.auth.decorators import user_passes_test

from apps.orders.models import Order
from apps.store.models import Category, Product


@user_passes_test(lambda u: u.is_staff, login_url='users:login')
def dashboard(request):

    # 💰 Total Sales (เฉพาะ success)
    total_sales = (
        Order.objects
        .filter(status='success')
        .aggregate(total=Sum('total_price'))['total'] or 0
    )

    # 📦 Category Summary
    category_summary = Category.objects.annotate(
        product_count=Count('products')
    )

    # 🧾 Recent Orders
    recent_orders = (
        Order.objects
        .select_related('buyer')
        .order_by('-created_at')[:10]
    )

    # 📊 Stats
    stats = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
    }

    # 📈 Chart (Sales per day)
    sales = (
        Order.objects
        .filter(status='success')
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total=Sum('total_price'))
        .order_by('day')
    )

    chart_labels = [s['day'].strftime('%d %b') for s in sales]
    chart_data = [float(s['total'] or 0) for s in sales]

    context = {
        'total_sales': total_sales,
        'category_summary': category_summary,
        'recent_orders': recent_orders,
        'stats': stats,

        # 🔥 สำคัญ
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }

    return render(request, 'analytics/dashboard.html', context)