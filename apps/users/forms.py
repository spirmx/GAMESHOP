import re

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


BASE_INPUT_CLASS = (
    "w-full rounded-2xl border border-white/10 bg-[#060B12] px-4 py-3.5 "
    "text-white placeholder-slate-500 outline-none transition-all "
    "focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
)

FILE_INPUT_CLASS = (
    "w-full text-slate-300 cursor-pointer "
    "file:mr-4 file:rounded-xl file:border-0 file:bg-blue-600/20 "
    "file:px-5 file:py-3 file:text-[11px] file:font-black "
    "file:uppercase file:tracking-[0.16em] file:text-blue-100 "
    "hover:file:bg-blue-600/30"
)

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9]+$")
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
)
PHONE_PATTERN = re.compile(r"^[0-9]{9,15}$")


class LoginForm(forms.Form):
    username = forms.CharField(label="ชื่อผู้ใช้", max_length=150)
    password = forms.CharField(label="รหัสผ่าน", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": BASE_INPUT_CLASS,
                "autocomplete": "username",
                "placeholder": "กรอกชื่อผู้ใช้ของคุณ",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": BASE_INPUT_CLASS,
                "autocomplete": "current-password",
                "placeholder": "กรอกรหัสผ่าน",
            }
        )


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="อีเมล")
    phone_number = forms.CharField(max_length=15, required=True, label="เบอร์โทรศัพท์")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "phone_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "ใช้ได้เฉพาะ A-Z และ 0-9",
            "email": "example@gmail.com",
            "phone_number": "กรอกเบอร์โทรศัพท์ที่ติดต่อได้",
            "password1": "รหัสผ่านอย่างน้อย 8 ตัวอักษร",
            "password2": "ยืนยันรหัสผ่านอีกครั้ง",
        }
        labels = {
            "username": "ชื่อผู้ใช้ (Username)",
            "password1": "รหัสผ่าน (Password)",
            "password2": "ยืนยันรหัสผ่าน",
        }
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = BASE_INPUT_CLASS
            field.widget.attrs["placeholder"] = placeholders.get(field_name, field.label)
            field.help_text = ""
            if field_name in labels:
                field.label = labels[field_name]

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError("กรุณากรอกชื่อผู้ใช้")
        if not USERNAME_PATTERN.fullmatch(username):
            raise forms.ValidationError("ชื่อผู้ใช้ใช้ได้เฉพาะภาษาอังกฤษและตัวเลข 0-9 เท่านั้น")
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("ชื่อผู้ใช้นี้ถูกใช้งานแล้ว")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("กรุณากรอกอีเมล")
        if not EMAIL_PATTERN.fullmatch(email):
            raise forms.ValidationError("กรุณากรอกอีเมลให้ถูกต้อง เช่น name@example.com")
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("อีเมลนี้ถูกใช้งานแล้ว")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number", "").strip()
        if not PHONE_PATTERN.fullmatch(phone_number):
            raise forms.ValidationError("กรุณากรอกเบอร์โทรศัพท์เป็นตัวเลข 9-15 หลัก")
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("เบอร์โทรศัพท์นี้ถูกใช้งานแล้ว")
        return phone_number

    def clean_password1(self):
        password = self.cleaned_data.get("password1", "")
        if len(password) < 8:
            raise forms.ValidationError("รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
        return password


class ForgotPasswordForm(forms.Form):
    identifier = forms.CharField(label="Username", max_length=150)
    new_password1 = forms.CharField(label="รหัสผ่านใหม่", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="ยืนยันรหัสผ่านใหม่", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["identifier"].widget.attrs.update(
            {
                "class": BASE_INPUT_CLASS,
                "placeholder": "กรอก Username ของบัญชีที่ต้องการกู้รหัสผ่าน",
            }
        )
        self.fields["new_password1"].widget.attrs.update(
            {
                "class": BASE_INPUT_CLASS,
                "placeholder": "ตั้งรหัสผ่านใหม่อย่างน้อย 8 ตัวอักษร",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "class": BASE_INPUT_CLASS,
                "placeholder": "ยืนยันรหัสผ่านใหม่อีกครั้ง",
            }
        )

    def clean_identifier(self):
        identifier = self.cleaned_data.get("identifier", "").strip()
        if not identifier:
            raise forms.ValidationError("กรุณากรอก Username")
        return identifier

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1", "")
        if len(password) < 8:
            raise forms.ValidationError("รหัสผ่านใหม่ต้องมีอย่างน้อย 8 ตัวอักษร")
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("new_password1") and cleaned_data.get("new_password2"):
            if cleaned_data["new_password1"] != cleaned_data["new_password2"]:
                self.add_error("new_password2", "รหัสผ่านยืนยันไม่ตรงกัน")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "phone_number", "profile_image"]
        widgets = {
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
            "email": forms.EmailInput(),
            "phone_number": forms.TextInput(),
            "profile_image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        labels = {
            "first_name": "ชื่อจริง",
            "last_name": "นามสกุล",
            "email": "อีเมล",
            "phone_number": "เบอร์โทรศัพท์",
            "profile_image": "รูปโปรไฟล์",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "first_name": "กรอกชื่อจริง",
            "last_name": "กรอกนามสกุล",
            "email": "กรอกอีเมล",
            "phone_number": "กรอกเบอร์โทรศัพท์",
        }
        for field_name, field in self.fields.items():
            field.help_text = ""
            if field_name == "profile_image":
                field.widget.attrs["class"] = FILE_INPUT_CLASS
            else:
                field.widget.attrs["class"] = BASE_INPUT_CLASS
                field.widget.attrs["placeholder"] = placeholders.get(field_name, field.label)

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not EMAIL_PATTERN.fullmatch(email):
            raise forms.ValidationError("กรุณากรอกอีเมลให้ถูกต้อง เช่น name@example.com")
        queryset = CustomUser.objects.filter(email__iexact=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("อีเมลนี้ถูกใช้งานแล้ว")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number", "").strip()
        if not PHONE_PATTERN.fullmatch(phone_number):
            raise forms.ValidationError("กรุณากรอกเบอร์โทรศัพท์เป็นตัวเลข 9-15 หลัก")
        queryset = CustomUser.objects.filter(phone_number=phone_number)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("เบอร์โทรศัพท์นี้ถูกใช้งานแล้ว")
        return phone_number
