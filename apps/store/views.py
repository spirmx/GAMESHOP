from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Game, Product


def _parse_decimal(value):
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError):
        return None


def _resolve_game_id(product):
    if getattr(product, "game_id", None):
        return product.game_id

    category = getattr(product, "category", None)
    return getattr(category, "game_id", None)


def _product_queryset():
    return Product.objects.select_related(
        "category",
        "game",
        "game__platform",
        "game__genre",
        "category__game",
        "category__game__platform",
    )


def _get_popular_products(limit=8):
    return _product_queryset().order_by("-sold_count", "price", "-created_at")[:limit]


def _get_new_arrival_products(limit=8):
    return _product_queryset().order_by("-created_at", "-sold_count")[:limit]


def _get_value_products(limit=8):
    return _product_queryset().order_by("price", "-sold_count", "-created_at")[:limit]


def _get_recommended_products(product, limit=6):
    product_game_id = _resolve_game_id(product)
    candidates = _product_queryset().exclude(id=product.id)
    ranked_products = []

    for candidate in candidates:
        score = 0
        reasons = []
        candidate_game_id = _resolve_game_id(candidate)

        if product_game_id and candidate_game_id == product_game_id:
            score += 120
            reasons.append("เกมเดียวกัน")

        if product.category_id and candidate.category_id == product.category_id:
            score += 55
            reasons.append("หมวดเดียวกัน")

        if candidate.fulfillment_type == product.fulfillment_type:
            score += 20
            reasons.append("รูปแบบส่งมอบใกล้เคียง")

        if candidate.is_available_for_sale:
            score += 35
        else:
            score -= 40

        score += min(candidate.sold_count * 4, 160)

        if candidate.price <= product.price:
            score += 18
            reasons.append("ราคาจับต้องง่าย")
        elif candidate.price - product.price <= Decimal("100"):
            score += 8

        candidate.recommendation_score = score
        candidate.recommendation_reason = " • ".join(dict.fromkeys(reasons)) or "สินค้าขายดีของร้าน"
        ranked_products.append(candidate)

    ranked_products.sort(
        key=lambda item: (
            item.recommendation_score,
            item.sold_count,
            item.stock,
            item.created_at,
        ),
        reverse=True,
    )
    return ranked_products[:limit]


def home(request):
    query = request.GET.get("q", "").strip()
    platform_name = request.GET.get("platform", "").strip()

    games = Game.objects.select_related("platform").order_by("name")
    featured_products = _get_popular_products(limit=12)
    daily_products = _get_new_arrival_products(limit=12)
    value_products = _get_value_products(limit=12)

    if query:
        games = games.filter(name__icontains=query)

    if platform_name:
        games = games.filter(platform__name__icontains=platform_name).distinct()

    context = {
        "games": games,
        "products": featured_products[:6],
        "featured_products": featured_products,
        "daily_products": daily_products,
        "value_products": value_products,
        "query": query,
        "selected_platform": platform_name,
    }
    return render(request, "store/home.html", context)


def product_list(request):
    products = _product_queryset()
    all_games = Game.objects.select_related("platform").order_by("name")

    platform_model = Game._meta.get_field("platform").remote_field.model
    platform_ids = (
        all_games.exclude(platform_id__isnull=True)
        .values_list("platform_id", flat=True)
        .distinct()
    )
    all_platforms = platform_model.objects.filter(id__in=platform_ids).order_by("name")

    product_cat_ids = (
        Product.objects.all()
        .exclude(category_id__isnull=True)
        .values_list("category_id", flat=True)
        .distinct()
    )
    all_categories = Category.objects.filter(id__in=product_cat_ids, type="product").order_by("name")

    query = request.GET.get("q", "").strip()
    selected_games = request.GET.getlist("game")
    selected_cats = request.GET.getlist("category")
    selected_platforms = request.GET.getlist("platform")
    price_preset = request.GET.get("price_preset", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()

    if query:
        products = products.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(game__name__icontains=query)
            | Q(category__game__name__icontains=query)
            | Q(game__platform__name__icontains=query)
            | Q(category__game__platform__name__icontains=query)
        ).distinct()

    valid_game_ids = [int(i) for i in selected_games if str(i).isdigit()]
    if valid_game_ids:
        products = products.filter(
            Q(game__id__in=valid_game_ids) | Q(category__game__id__in=valid_game_ids)
        ).distinct()

    category_ids = [int(i) for i in selected_cats if str(i).isdigit()]
    category_keywords = [str(i).strip() for i in selected_cats if i and not str(i).isdigit()]

    if category_ids or category_keywords:
        category_filter = Q()

        if category_ids:
            category_filter |= Q(category__id__in=category_ids, category__type="product")

        for keyword in category_keywords:
            category_filter |= Q(category__name__icontains=keyword, category__type="product")

        products = products.filter(category_filter).distinct()

    if selected_platforms:
        products = products.filter(
            Q(game__platform__name__in=selected_platforms)
            | Q(category__game__platform__name__in=selected_platforms)
        ).distinct()

    if price_preset == "under_500":
        products = products.filter(price__lt=500)
    elif price_preset == "500_1000":
        products = products.filter(price__gte=500, price__lte=1000)
    elif price_preset == "over_1000":
        products = products.filter(price__gt=1000)

    min_price_value = _parse_decimal(min_price)
    max_price_value = _parse_decimal(max_price)

    if min_price_value is not None:
        products = products.filter(price__gte=min_price_value)
    if max_price_value is not None:
        products = products.filter(price__lte=max_price_value)

    products = products.order_by("-id")

    paginator = Paginator(products, 15)
    page_number = request.GET.get("page", 1)
    products_page = paginator.get_page(page_number)

    context = {
        "products": products_page,
        "games": all_games,
        "categories": all_categories,
        "platforms": all_platforms,
        "query": query,
        "selected_games": valid_game_ids,
        "selected_cats": category_ids,
        "selected_cat_keywords": category_keywords,
        "selected_platforms": selected_platforms,
        "price_preset": price_preset,
        "min_price": min_price,
        "max_price": max_price,
    }
    return render(request, "store/product_list.html", context)


def game_detail(request, slug):
    game = get_object_or_404(
        Game.objects.select_related("platform"),
        slug=slug,
    )

    products = (
        Product.objects.filter(Q(game=game) | Q(category__game=game))
        .select_related("category", "game", "game__platform")
        .distinct()
        .order_by("-stock", "price")
    )

    context = {
        "game": game,
        "products": products,
    }
    return render(request, "store/game_detail.html", context)


def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related(
            "game",
            "game__platform",
            "category",
            "category__game",
            "category__game__platform",
        ),
        id=product_id,
    )
    recommended_products = _get_recommended_products(product, limit=6)
    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "recommended_products": recommended_products,
        },
    )
