import uuid
import os
from django.utils.text import slugify

def generate_unique_slug(model_class, name):
    """สร้าง Slug ที่ไม่ซ้ำกับข้อมูลเดิมในฐานข้อมูล SQL"""
    slug = slugify(name)
    unique_slug = slug
    number = 1
    while model_class.objects.filter(slug=unique_slug).exists():
        unique_slug = f'{slug}-{number}'
        number += 1
    return unique_slug

def rename_upload_file(instance, filename):
    """เปลี่ยนชื่อไฟล์ที่อัปโหลดเป็น UUID ป้องกันชื่อซ้ำและไฟล์เอ๋อ"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads/', filename)