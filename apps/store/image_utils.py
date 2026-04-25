from __future__ import annotations

import os
from io import BytesIO
from uuid import uuid4

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


RGBA_MODES = {"RGBA", "LA"}


def optimize_uploaded_image(image_field, *, max_size=(1600, 1600), quality=84, force=False):
    if not image_field or getattr(image_field, "_papaya_optimized", False):
        return image_field

    if getattr(image_field, "_committed", True) and not force:
        return image_field

    try:
        image_field.open("rb")
        image = Image.open(image_field)
        image = ImageOps.exif_transpose(image)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        has_alpha = image.mode in RGBA_MODES
        if not has_alpha and image.mode == "P":
            has_alpha = "transparency" in image.info

        buffer = BytesIO()
        root_name, original_ext = os.path.splitext(os.path.basename(image_field.name or "image"))
        safe_root = root_name or f"image-{uuid4().hex[:8]}"

        if has_alpha:
            image = image.convert("RGBA")
            output_format = "PNG"
            extension = ".png"
            save_kwargs = {"optimize": True}
        else:
            image = image.convert("RGB")
            if (image.format or "").upper() == "WEBP" or original_ext.lower() == ".webp":
                output_format = "WEBP"
                extension = ".webp"
                save_kwargs = {"quality": quality, "method": 6}
            else:
                output_format = "JPEG"
                extension = ".jpg"
                save_kwargs = {"quality": quality, "optimize": True, "progressive": True}

        image.save(buffer, format=output_format, **save_kwargs)
        image_field.save(
            f"{safe_root}{extension}",
            ContentFile(buffer.getvalue()),
            save=False,
        )
        image_field._papaya_optimized = True
    except Exception:
        return image_field

    return image_field
