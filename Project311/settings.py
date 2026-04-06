from pathlib import Path
import os
from django.contrib.messages import constants as messages

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# 🛡️ SECURITY & DEBUG
# =========================================================
SECRET_KEY = 'django-insecure-papaya-shop-master-key-2026'
DEBUG = True
ALLOWED_HOSTS = ['*']

# =========================================================
# 📦 INSTALLED APPS
# =========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # ✅ เสริม: สำหรับจัดรูปแบบตัวเลข/เงิน (เช่น ฿1,000)

    # 🎮 PAPAYA GAME SHOP APPS
    'apps.users',      # ระบบสมาชิก
    'apps.store',      # คลังสินค้าและเกม
    'apps.orders',     # ระบบสั่งซื้อ
    'apps.wallets',    # กระเป๋าเงิน
    'apps.analytics',  # ระบบวิเคราะห์ข้อมูล
    'apps.cart',       # ตะกร้าสินค้า (ต้องอยู่ในโฟลเดอร์ apps/)
]

# =========================================================
# 🧠 AUTHENTICATION & USER MODEL
# =========================================================
AUTH_USER_MODEL = 'users.CustomUser' #

# =========================================================
# 🛠️ MIDDLEWARE
# =========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =========================================================
# 🔗 URL & WSGI CONFIG
# =========================================================
ROOT_URLCONF = 'Project311.urls' #
WSGI_APPLICATION = 'Project311.wsgi.application'

# =========================================================
# 🎨 TEMPLATES
# =========================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], #
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =========================================================
# 🗄️ DATABASE (SQLite)
# =========================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# =========================================================
# 🌍 INTERNATIONALIZATION (ภาษาและเวลาไทย)
# =========================================================
LANGUAGE_CODE = 'th-th'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True

# =========================================================
# 📁 STATIC & MEDIA FILES
# =========================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =========================================================
# 🔑 LOGIN/LOGOUT REDIRECTS
# =========================================================
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'

# =========================================================
# ✨ MESSAGE TAGS (เสริม: เพื่อให้ Alert แสดงผลสีตรงกับ Tailwind/CSS)
# =========================================================
MESSAGE_TAGS = {
    messages.DEBUG: 'bg-slate-500',
    messages.INFO: 'bg-blue-500',
    messages.SUCCESS: 'bg-green-500',
    messages.WARNING: 'bg-yellow-500',
    messages.ERROR: 'bg-red-500',
}

# =========================================================
# 📊 LOGGING (เสริม: รองรับโฟลเดอร์ logs ของคุณ)
# =========================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/app.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'