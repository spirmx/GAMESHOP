from pathlib import Path
import os
from django.contrib.messages import constants as messages

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# 🛡️ SECURITY & DEBUG
# =========================================================
SECRET_KEY = 'django-insecure-papaya-shop-master-key-2026'
DEBUG = True

# ✅ อนุญาตให้เข้าถึงจาก ngrok และ localhost
ALLOWED_HOSTS = ['*'] 

# 🚀 NGROK & CSRF FIX: เพิ่มเพื่อให้ล็อกอินผ่านลิงก์ภายนอกได้
# ถ้า ngrok เปลี่ยนลิงก์ ให้เอาโดเมนใหม่มาอัปเดตตรงนี้ครับ
CSRF_TRUSTED_ORIGINS = [
    'https://6634-2001-44c8-4161-3987-ec46-3609-37a5-4296.ngrok-free.app',
]

# ✅ ตั้งค่า Session ให้ทำงานผ่าน HTTP ธรรมดาได้ (เหมาะสำหรับการทดสอบผ่าน Tunnel)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False # ช่วยให้บางเบราว์เซอร์จัดการ Cookie ได้ง่ายขึ้นขณะทดสอบ

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
    'django.contrib.humanize',

    # 🎮 PAPAYA GAME SHOP APPS
    'apps.users',      
    'apps.store',      
    'apps.orders',     
    'apps.wallets',    
    'apps.analytics',  
    'apps.cart',       
]

# =========================================================
# 🧠 AUTHENTICATION & USER MODEL
# =========================================================
AUTH_USER_MODEL = 'users.CustomUser'

# =========================================================
# 🛠️ MIDDLEWARE
# =========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # 🚨 ตัวควบคุมการล็อกอิน
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ... (ส่วนที่เหลือคงเดิมตามที่คุณส่งมา) ...
ROOT_URLCONF = 'Project311.urls'
WSGI_APPLICATION = 'Project311.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'th-th'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'

MESSAGE_TAGS = {
    messages.DEBUG: 'bg-slate-500',
    messages.INFO: 'bg-blue-500',
    messages.SUCCESS: 'bg-green-500',
    messages.WARNING: 'bg-yellow-500',
    messages.ERROR: 'bg-red-500',
}

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