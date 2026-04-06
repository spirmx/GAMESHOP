from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="อีเมล")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # รวมฟิลด์พื้นฐานและฟิลด์ใหม่ที่เราสร้าง
        fields = UserCreationForm.Meta.fields + (
            'email', 'phone_number', 'address', 'city', 'postal_code'
        )