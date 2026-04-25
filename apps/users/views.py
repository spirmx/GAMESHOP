from datetime import timedelta
import json
import random

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LogoutView
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.orders.models import Order
from apps.store.models import Game, Product
from .forms import ForgotPasswordForm, LoginForm, SignUpForm, UserProfileForm
from .models import CustomUser


PAID_STATUSES = ["SUCCESS", "PAID"]
SIGNUP_CAPTCHA_KEY = "signup_captcha"
PROFILE_CAPTCHA_KEY = "profile_captcha"
RESET_CAPTCHA_KEY = "reset_captcha"
RESET_VERIFIED_USER_KEY = "reset_verified_user"


def staff_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url="users:login",
    )(view_func)


def get_missing_identity_fields(user):
    field_labels = {
        "first_name": "ชื่อจริง",
        "last_name": "นามสกุล",
        "email": "อีเมล",
        "phone_number": "เบอร์โทรศัพท์",
    }
    missing_fields = []
    for field_name, label in field_labels.items():
        if not str(getattr(user, field_name, "") or "").strip():
            missing_fields.append(label)
    return missing_fields


def profile_has_required_identity(user):
    return not get_missing_identity_fields(user)


def get_missing_identity_fields_from_post(post_data):
    field_labels = {
        "first_name": "ชื่อจริง",
        "last_name": "นามสกุล",
        "email": "อีเมล",
        "phone_number": "เบอร์โทรศัพท์",
    }
    missing_fields = []
    for field_name, label in field_labels.items():
        if not str(post_data.get(field_name, "") or "").strip():
            missing_fields.append(label)
    return missing_fields


def build_captcha(request, session_key):
    left = random.randint(1, 9)
    right = random.randint(1, 9)
    captcha_payload = {
        "question": f"{left} + {right} = ?",
        "answer": str(left + right),
    }
    request.session[session_key] = captcha_payload
    request.session.modified = True
    return {
        "question": captcha_payload["question"],
        "placeholder": "กรอกคำตอบตัวเลข",
    }


def get_captcha_context(request, session_key):
    payload = request.session.get(session_key, {})
    if not payload or "question" not in payload or "answer" not in payload:
        return build_captcha(request, session_key)
    return {
        "question": payload["question"],
        "placeholder": "กรอกคำตอบตัวเลข",
    }


def captcha_is_valid(request, session_key, submitted_value):
    payload = request.session.get(session_key, {})
    expected = str(payload.get("answer", "")).strip()
    return bool(expected and str(submitted_value or "").strip() == expected)


def clear_captcha(request, session_key):
    request.session.pop(session_key, None)


def apply_full_verification_state(user):
    user.is_verified = bool(
        user.has_identity_profile and user.email_verified and user.phone_verified
    )


def reset_login_security(user):
    user.failed_login_attempts = 0
    user.lockout_until = None


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("users:profile")

    captcha = build_captcha(request, SIGNUP_CAPTCHA_KEY) if request.method != "POST" else get_captcha_context(request, SIGNUP_CAPTCHA_KEY)

    if request.method == "POST":
        form = SignUpForm(request.POST)
        captcha_answer = request.POST.get("captcha_answer")

        if not captcha_is_valid(request, SIGNUP_CAPTCHA_KEY, captcha_answer):
            form.add_error(None, "Captcha ไม่ถูกต้อง กรุณาตรวจสอบและลองใหม่อีกครั้ง")
        elif form.is_valid():
            user = form.save(commit=False)
            user.email_verified = True
            user.phone_verified = False
            apply_full_verification_state(user)
            user.save()
            login(request, user)
            clear_captcha(request, SIGNUP_CAPTCHA_KEY)
            messages.success(request, "สมัครสมาชิกเรียบร้อยแล้ว ระบบตรวจสอบว่าเป็นผู้ใช้งานจริงผ่าน Captcha เรียบร้อย")
            return redirect("users:profile")
        else:
            messages.error(request, "กรุณาตรวจสอบข้อมูลสมัครสมาชิกให้ถูกต้องอีกครั้ง")
    else:
        form = SignUpForm()

    return render(
        request,
        "auth/signup.html",
        {
            "form": form,
            "captcha_question": captcha["question"],
            "captcha_placeholder": captcha["placeholder"],
            "captcha_reason": "ใช้ป้องกันการสมัครบัญชีปลอมและการปั๊มยูสแบบอัตโนมัติ",
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("users:profile")

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = CustomUser.objects.filter(username__iexact=username).first()

        if user and user.lockout_until and user.lockout_until > timezone.now():
            remaining = user.active_lockout_seconds
            form.add_error(
                "password",
                f"คุณกรอกรหัสผิดเกินกำหนด กรุณารออีก {remaining} วินาที หรือกดลืมรหัสผ่านหากจำรหัสไม่ได้",
            )
        elif user and user.failed_login_attempts >= 30:
            messages.warning(request, "ระบบบังคับให้เปลี่ยนรหัสผ่านแล้ว กรุณายืนยันตัวตนผ่านหน้ารีเซ็ตรหัสผ่าน")
            return redirect(f"{redirect('users:forgot_password').url}?identifier={username}")
        else:
            authenticated_user = authenticate(request, username=username, password=password)

            if authenticated_user is not None:
                reset_login_security(authenticated_user)
                authenticated_user.save(update_fields=["failed_login_attempts", "lockout_until"])
                login(request, authenticated_user)
                messages.success(request, "เข้าสู่ระบบเรียบร้อยแล้ว")
                return redirect("users:profile")

            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 30:
                    user.lockout_until = timezone.now()
                    user.save(update_fields=["failed_login_attempts", "lockout_until"])
                    messages.error(request, "กรอกรหัสผ่านผิดครบ 30 ครั้งแล้ว กรุณาเปลี่ยนรหัสผ่านก่อนเข้าใช้งานต่อ")
                    return redirect(f"{redirect('users:forgot_password').url}?identifier={username}")

                if user.failed_login_attempts % 3 == 0:
                    cooldown_step = (user.failed_login_attempts // 3) - 1
                    cooldown_seconds = 10 + (cooldown_step * 5)
                    user.lockout_until = timezone.now() + timedelta(seconds=cooldown_seconds)
                else:
                    cooldown_seconds = 0
                    user.lockout_until = None

                user.save(update_fields=["failed_login_attempts", "lockout_until"])

                if cooldown_seconds:
                    form.add_error(
                        "password",
                        f"กรอกรหัสผ่านผิด {user.failed_login_attempts} ครั้ง ระบบพักการเข้าสู่ระบบ {cooldown_seconds} วินาที หากลืมรหัสผ่านให้กดลืมรหัสผ่านได้ทันที",
                    )
                else:
                    attempts_left = 3 - (user.failed_login_attempts % 3)
                    form.add_error(
                        "password",
                        f"รหัสผ่านไม่ถูกต้อง หากลืมรหัสผ่านให้กดลืมรหัสผ่านได้เลย เหลืออีก {attempts_left} ครั้งก่อนระบบจะพักการเข้าสู่ระบบ",
                    )
            else:
                form.add_error("password", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    return render(
        request,
        "auth/login.html",
        {
            "form": form,
        },
    )


def forgot_password_view(request):
    initial_identifier = request.GET.get("identifier", "")
    verified_username = request.session.get(RESET_VERIFIED_USER_KEY, "")
    if verified_username and not initial_identifier:
        initial_identifier = verified_username

    form = ForgotPasswordForm(request.POST or None, initial={"identifier": initial_identifier})
    captcha = build_captcha(request, RESET_CAPTCHA_KEY) if request.method != "POST" else get_captcha_context(request, RESET_CAPTCHA_KEY)
    reset_verified = bool(verified_username and initial_identifier and verified_username.lower() == initial_identifier.lower())

    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        reset_action = request.POST.get("reset_action") or "verify_identity"
        captcha_answer = request.POST.get("captcha_answer")
        user = CustomUser.objects.filter(username__iexact=identifier).first()

        if reset_action == "verify_identity":
            if not identifier:
                form.add_error("identifier", "กรุณากรอก Username")
            elif not user:
                form.add_error("identifier", "ไม่พบ Username นี้ในระบบ")
            elif not captcha_is_valid(request, RESET_CAPTCHA_KEY, captcha_answer):
                form.add_error(None, "Captcha ไม่ถูกต้อง กรุณาตรวจสอบคำตอบแล้วลองใหม่อีกครั้ง")
            else:
                request.session[RESET_VERIFIED_USER_KEY] = user.username
                request.session.modified = True
                clear_captcha(request, RESET_CAPTCHA_KEY)
                messages.success(request, "ยืนยัน Username สำเร็จแล้ว สามารถตั้งรหัสผ่านใหม่ได้ทันที")
                return redirect(f"{redirect('users:forgot_password').url}?identifier={user.username}")

        elif reset_action == "change_password":
            if not identifier:
                form.add_error("identifier", "กรุณากรอก Username")
            elif not user:
                form.add_error("identifier", "ไม่พบ Username นี้ในระบบ")
                request.session.pop(RESET_VERIFIED_USER_KEY, None)
                reset_verified = False
            elif not verified_username or verified_username.lower() != user.username.lower():
                form.add_error(None, "กรุณาตรวจสอบ Username และยืนยัน Captcha ก่อนเปลี่ยนรหัสผ่าน")
                reset_verified = False
            elif form.is_valid():
                user.set_password(form.cleaned_data["new_password1"])
                user.password_change_count += 1
                reset_login_security(user)
                user.save(update_fields=["password", "password_change_count", "failed_login_attempts", "lockout_until"])
                clear_captcha(request, RESET_CAPTCHA_KEY)
                request.session.pop(RESET_VERIFIED_USER_KEY, None)
                request.session.modified = True
                messages.success(request, "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว กรุณาเข้าสู่ระบบด้วยรหัสผ่านใหม่")
                return redirect("users:login")

        verified_username = request.session.get(RESET_VERIFIED_USER_KEY, "")
        reset_verified = bool(verified_username and identifier and verified_username.lower() == identifier.lower())
        captcha = build_captcha(request, RESET_CAPTCHA_KEY) if not reset_verified else get_captcha_context(request, RESET_CAPTCHA_KEY)

    return render(
        request,
        "auth/forgot_password.html",
        {
            "form": form,
            "captcha_question": captcha["question"],
            "captcha_placeholder": captcha["placeholder"],
            "captcha_reason": "ยืนยันว่าเจ้าของบัญชีเป็นผู้ขอเปลี่ยนรหัสผ่านจริงก่อนเปิดการตั้งรหัสผ่านใหม่",
            "reset_verified": reset_verified,
        },
    )


def _legacy_forgot_password_view(request):
    if request.user.is_authenticated:
        initial_identifier = ""
    else:
        initial_identifier = request.GET.get("identifier", "")

    form = ForgotPasswordForm(request.POST or None, initial={"identifier": initial_identifier})
    captcha = build_captcha(request, RESET_CAPTCHA_KEY) if request.method != "POST" else get_captcha_context(request, RESET_CAPTCHA_KEY)

    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        user = CustomUser.objects.filter(Q(email__iexact=identifier) | Q(phone_number=identifier)).first()
        captcha_answer = request.POST.get("captcha_answer")

        if not captcha_is_valid(request, RESET_CAPTCHA_KEY, captcha_answer):
            form.add_error(None, "Captcha ไม่ถูกต้อง กรุณาตรวจสอบคำตอบแล้วลองใหม่")
        elif not user:
            form.add_error("identifier", "ไม่พบผู้ใช้งานจากอีเมลหรือเบอร์โทรศัพท์ที่กรอก")
        elif form.is_valid():
            user.set_password(form.cleaned_data["new_password1"])
            user.password_change_count += 1
            reset_login_security(user)
            user.save(update_fields=["password", "password_change_count", "failed_login_attempts", "lockout_until"])
            clear_captcha(request, RESET_CAPTCHA_KEY)
            messages.success(request, "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว กรุณาเข้าสู่ระบบด้วยรหัสผ่านใหม่")
            return redirect("users:login")

    return render(
        request,
        "auth/forgot_password.html",
        {
            "form": form,
            "captcha_question": captcha["question"],
            "captcha_placeholder": captcha["placeholder"],
            "captcha_reason": "ใช้ยืนยันว่าผู้ขอเปลี่ยนรหัสผ่านเป็นผู้ใช้งานจริงของระบบเดโม่",
        },
    )


def forgot_password_view(request):
    initial_identifier = request.GET.get("identifier", "")
    verified_username = request.session.get(RESET_VERIFIED_USER_KEY, "")
    if verified_username and not initial_identifier:
        initial_identifier = verified_username

    form = ForgotPasswordForm(request.POST or None, initial={"identifier": initial_identifier})
    captcha = (
        build_captcha(request, RESET_CAPTCHA_KEY)
        if request.method != "POST"
        else get_captcha_context(request, RESET_CAPTCHA_KEY)
    )
    reset_verified = bool(
        verified_username
        and initial_identifier
        and verified_username.lower() == initial_identifier.lower()
    )

    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        reset_action = request.POST.get("reset_action") or "verify_identity"
        captcha_answer = request.POST.get("captcha_answer")
        user = CustomUser.objects.filter(username__iexact=identifier).first()

        if reset_action == "verify_identity":
            if not identifier:
                form.add_error("identifier", "กรุณากรอก Username")
            elif not user:
                form.add_error("identifier", "ไม่พบ Username นี้ในระบบ")
            elif not captcha_is_valid(request, RESET_CAPTCHA_KEY, captcha_answer):
                form.add_error(None, "Captcha ไม่ถูกต้อง กรุณาตรวจสอบคำตอบแล้วลองใหม่อีกครั้ง")
            else:
                request.session[RESET_VERIFIED_USER_KEY] = user.username
                request.session.modified = True
                clear_captcha(request, RESET_CAPTCHA_KEY)
                messages.success(request, "ยืนยัน Username สำเร็จแล้ว สามารถตั้งรหัสผ่านใหม่ได้ทันที")
                return redirect(f"{redirect('users:forgot_password').url}?identifier={user.username}")

        elif reset_action == "change_password":
            verified_user = (
                CustomUser.objects.filter(username__iexact=verified_username).first()
                if verified_username
                else None
            )

            if not verified_username or not verified_user:
                form.add_error(None, "กรุณาตรวจสอบ Username และยืนยัน Captcha ก่อนเปลี่ยนรหัสผ่าน")
                request.session.pop(RESET_VERIFIED_USER_KEY, None)
                request.session.modified = True
                reset_verified = False
            elif not identifier:
                form.add_error("identifier", "กรุณากรอก Username")
            elif identifier.lower() != verified_user.username.lower():
                form.add_error("identifier", "Username ต้องตรงกับบัญชีที่ยืนยันแล้ว")
                reset_verified = False
            elif not user:
                form.add_error("identifier", "ไม่พบ Username นี้ในระบบ")
                request.session.pop(RESET_VERIFIED_USER_KEY, None)
                request.session.modified = True
                reset_verified = False
            elif form.is_valid():
                verified_user.set_password(form.cleaned_data["new_password1"])
                verified_user.password_change_count += 1
                reset_login_security(verified_user)
                verified_user.save(
                    update_fields=[
                        "password",
                        "password_change_count",
                        "failed_login_attempts",
                        "lockout_until",
                    ]
                )
                clear_captcha(request, RESET_CAPTCHA_KEY)
                request.session.pop(RESET_VERIFIED_USER_KEY, None)
                request.session.modified = True
                messages.success(request, "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว กรุณาเข้าสู่ระบบด้วยรหัสผ่านใหม่")
                return redirect("users:login")

        verified_username = request.session.get(RESET_VERIFIED_USER_KEY, "")
        reset_verified = bool(
            verified_username
            and identifier
            and verified_username.lower() == identifier.lower()
        )
        captcha = (
            build_captcha(request, RESET_CAPTCHA_KEY)
            if not reset_verified
            else get_captcha_context(request, RESET_CAPTCHA_KEY)
        )

    return render(
        request,
        "auth/forgot_password.html",
        {
            "form": form,
            "captcha_question": captcha["question"],
            "captcha_placeholder": captcha["placeholder"],
            "captcha_reason": "ยืนยันว่าเจ้าของบัญชีเป็นผู้ขอเปลี่ยนรหัสผ่านจริงก่อนเปิดการตั้งรหัสผ่านใหม่",
            "reset_verified": reset_verified,
        },
    )


@login_required
def profile_view(request):
    wallet = getattr(request.user, "wallet", None)
    return render(
        request,
        "profile.html",
        {
            "profile_user": request.user,
            "wallet": wallet,
        },
    )


@login_required
def profile_edit(request):
    user = request.user
    captcha = None

    if user.verification_complete and user.has_identity_profile:
        captcha = None
    else:
        captcha = build_captcha(request, PROFILE_CAPTCHA_KEY) if request.method != "POST" else get_captcha_context(request, PROFILE_CAPTCHA_KEY)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        previous_email = (user.email or "").strip().lower()
        previous_phone = (user.phone_number or "").strip()

        if form.is_valid():
            saved_user = form.save(commit=False)
            new_email = (saved_user.email or "").strip().lower()
            new_phone = (saved_user.phone_number or "").strip()

            email_changed = previous_email != new_email
            phone_changed = previous_phone != new_phone

            if email_changed:
                saved_user.email_verified = False
            if phone_changed:
                saved_user.phone_verified = False
            if email_changed or phone_changed:
                saved_user.is_verified = False

            missing_fields = get_missing_identity_fields(saved_user)
            if missing_fields:
                saved_user.is_verified = False
            else:
                submitted_captcha = request.POST.get("captcha_answer")
                if not saved_user.verification_complete:
                    if not captcha_is_valid(request, PROFILE_CAPTCHA_KEY, submitted_captcha):
                        form.add_error(None, "Captcha สำหรับยืนยันข้อมูลไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
                        return render(
                            request,
                            "users/profile_edit.html",
                            {
                                "form": form,
                                "profile_user": user,
                                "missing_identity_fields": get_missing_identity_fields_from_post(request.POST),
                                "captcha_question": build_captcha(request, PROFILE_CAPTCHA_KEY)["question"],
                                "verification_required": True,
                            },
                        )

                    saved_user.email_verified = True
                    saved_user.phone_verified = True

                apply_full_verification_state(saved_user)

            saved_user.save()
            clear_captcha(request, PROFILE_CAPTCHA_KEY)

            if saved_user.verification_complete:
                messages.success(request, "บันทึกข้อมูลโปรไฟล์เรียบร้อย และยืนยันข้อมูลติดต่อสำเร็จแล้ว")
            else:
                messages.info(request, "บันทึกข้อมูลแล้ว แต่ยังต้องกรอกข้อมูลให้ครบเพื่อเปิดสถานะยืนยันตัวตน")
            return redirect("users:profile")

        messages.error(request, "ไม่สามารถบันทึกข้อมูลได้ กรุณาตรวจสอบความถูกต้องอีกครั้ง")
    else:
        form = UserProfileForm(instance=user)

    current_missing_fields = (
        get_missing_identity_fields_from_post(request.POST)
        if request.method == "POST"
        else get_missing_identity_fields(user)
    )

    return render(
        request,
        "users/profile_edit.html",
        {
            "form": form,
            "profile_user": user,
            "missing_identity_fields": current_missing_fields,
            "captcha_question": captcha["question"] if captcha else "",
            "verification_required": not user.verification_complete or not user.has_identity_profile,
        },
    )


@staff_required
def admin_dashboard(request):
    now = timezone.now()
    online_since = now - timedelta(minutes=5)
    paid_orders = Order.objects.filter(status__in=PAID_STATUSES)

    total_revenue = paid_orders.aggregate(total=Sum("total_price"))["total"] or 0
    total_orders = Order.objects.count()
    paid_order_count = paid_orders.count()
    pending_orders = Order.objects.exclude(status__in=PAID_STATUSES).count()
    total_products = Product.objects.count()
    total_games = Game.objects.count()
    total_customers = CustomUser.objects.filter(is_staff=False).count()
    total_admins = CustomUser.objects.filter(is_staff=True).count()
    online_customers = CustomUser.objects.filter(is_staff=False, last_seen__gte=online_since).count()

    products = list(
        Product.objects.select_related("game", "category").annotate(
            sold_units=Count(
                "orderitem",
                filter=Q(orderitem__order__status__in=PAID_STATUSES),
            )
        ).order_by("title")
    )
    games = list(
        Game.objects.select_related("platform", "genre").annotate(
            total_items=Count("products", distinct=True),
            total_stock=Sum("products__stock"),
        ).order_by("-is_active", "name")
    )

    ready_products = sum(1 for product in products if product.is_available_for_sale)
    low_stock_products = [
        product for product in products
        if product.is_available_for_sale and 0 < product.stock <= 10
    ]
    out_of_stock_products = [product for product in products if product.stock <= 0]
    blocked_products = [
        product for product in products
        if not product.is_available_for_sale and product.stock > 0
    ]
    unavailable_games = [game for game in games if not game.is_available_for_sale]
    total_stock_units = sum(max(product.stock, 0) for product in products)

    top_products = sorted(
        products,
        key=lambda item: (item.sold_units or 0, item.stock, item.title.lower()),
        reverse=True,
    )[:5]

    player_users_preview = CustomUser.objects.filter(is_staff=False).order_by(
        "-last_seen",
        "-last_login",
        "-date_joined",
    )[:5]
    admin_users_preview = CustomUser.objects.filter(is_staff=True).order_by(
        "-last_seen",
        "-last_login",
        "-date_joined",
    )[:5]

    today = timezone.localdate()
    chart_labels = []
    revenue_chart_data = []
    order_chart_data = []

    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        chart_labels.append(target_date.strftime("%d %b"))
        daily_sales = (
            paid_orders.filter(created_at__date=target_date).aggregate(total=Sum("total_price"))["total"]
            or 0
        )
        daily_orders = paid_orders.filter(created_at__date=target_date).count()
        revenue_chart_data.append(float(daily_sales))
        order_chart_data.append(daily_orders)

    product_status_labels = ["พร้อมขาย", "สต็อกต่ำ", "สินค้าหมด", "ถูกปิดขาย"]
    product_status_data = [
        max(ready_products - len(low_stock_products), 0),
        len(low_stock_products),
        len(out_of_stock_products),
        len(blocked_products),
    ]

    operations_alerts = [
        {
            "title": "สินค้าสต็อกต่ำ",
            "value": len(low_stock_products),
            "description": "สินค้าที่เหลือน้อยกว่า 10 ชิ้นและยังเปิดขายอยู่",
            "tone": "amber",
        },
        {
            "title": "สินค้าหมดสต็อก",
            "value": len(out_of_stock_products),
            "description": "สินค้าที่ควรเติมสต็อกหรือตรวจสอบหน้าแสดงผล",
            "tone": "red",
        },
        {
            "title": "เกมไม่พร้อมขาย",
            "value": len(unavailable_games),
            "description": "เกมยังแสดงบนหน้าร้านแต่ระบบจะบล็อกการสั่งซื้อ",
            "tone": "slate",
        },
        {
            "title": "คำสั่งซื้อรอตรวจสอบ",
            "value": pending_orders,
            "description": "รายการที่ยังไม่อยู่ในสถานะชำระเงินสำเร็จ",
            "tone": "blue",
        },
    ]

    context = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "paid_order_count": paid_order_count,
        "pending_orders": pending_orders,
        "total_products": total_products,
        "total_games": total_games,
        "ready_products": ready_products,
        "total_stock_units": total_stock_units,
        "total_customers": total_customers,
        "online_customers": online_customers,
        "total_admins": total_admins,
        "game_list": games,
        "categories": games,
        "player_users": player_users_preview,
        "admin_users": admin_users_preview,
        "top_products": top_products,
        "operations_alerts": operations_alerts,
        "low_stock_products": low_stock_products[:6],
        "unavailable_games": unavailable_games[:6],
        "chart_labels": json.dumps(chart_labels),
        "revenue_chart_data": json.dumps(revenue_chart_data),
        "order_chart_data": json.dumps(order_chart_data),
        "product_status_labels": json.dumps(product_status_labels),
        "product_status_data": json.dumps(product_status_data),
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@staff_required
def admin_category_stock(request, category_id):
    game = get_object_or_404(Game, id=category_id)
    products = (
        Product.objects.filter(game=game).annotate(
            total_sales=Count(
                "orderitem",
                filter=Q(orderitem__order__status__in=PAID_STATUSES),
            )
        ).order_by("stock", "title")
    )
    total_sold_units = products.aggregate(total=Sum("total_sales"))["total"] or 0
    total_game_revenue = (
        Order.objects.filter(items__product__game=game, status__in=PAID_STATUSES)
        .distinct()
        .aggregate(total=Sum("total_price"))["total"]
        or 0
    )
    available_products = sum(1 for item in products if item.is_available_for_sale)
    low_stock_count = sum(
        1 for item in products if item.is_available_for_sale and 0 < item.stock <= 10
    )
    return render(
        request,
        "dashboard/admin_category_stock.html",
        {
            "category": game,
            "game": game,
            "products": products,
            "total_sold_units": total_sold_units,
            "total_game_revenue": total_game_revenue,
            "available_products": available_products,
            "low_stock_count": low_stock_count,
        },
    )


@staff_required
def admin_user_list(request):
    admin_users = CustomUser.objects.filter(is_staff=True).order_by(
        "-last_seen",
        "-last_login",
        "-date_joined",
    )
    player_users = CustomUser.objects.filter(is_staff=False).order_by(
        "-last_seen",
        "-last_login",
        "-date_joined",
    )
    return render(
        request,
        "dashboard/admin_user_list.html",
        {
            "admin_users": admin_users,
            "player_users": player_users,
        },
    )


class CustomLogoutView(LogoutView):
    next_page = "users:login"
