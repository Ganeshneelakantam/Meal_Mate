# forms.py
from django import forms
from .models import Restaurant, Menu

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label="Enter your email", max_length=100)

class OTPForm(forms.Form):
    otp = forms.CharField(label="Enter OTP", max_length=6)

class NewPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'description', 'image_url', 'location', 'cuisine_type', 'rating']  # Updated fields list

class MenuForm(forms.ModelForm):
    restaurant = forms.ModelChoiceField(queryset=Restaurant.objects.all())  # Ensure the dropdown for restaurants is present

    class Meta:
        model = Menu
        fields = ['restaurant', 'name', 'description', 'image_url', 'price', 'veg_or_non_veg', 'rating']  # Updated fields list
