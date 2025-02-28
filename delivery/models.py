# Django Admin 
# username: Ganesh
# password: ganesh007

from django.db import models
from django.db.models import Sum
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )
    
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    password = models.CharField(max_length=128)
    address = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    user_id = models.CharField(max_length=10, unique=True)  # Unique user ID for both admin and user

    # Add these fields
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def has_perm(self, perm, obj=None):
        return self.is_superuser  # Superusers have all permissions

    def has_module_perms(self, app_label):
        return self.is_superuser  # Superusers have access to all modules

    def save(self, *args, **kwargs):
        if not self.user_id:
            if self.role == 'admin':
                self.user_id = 'MMA' + str(User.objects.filter(role='admin').count() + 1).zfill(3)
            else:
                self.user_id = 'MMU' + str(User.objects.filter(role='customer').count() + 1).zfill(3)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


    
class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image_url = models.URLField(max_length=1024, blank=True, null=True)  # Online image URL
    location = models.CharField(max_length=255)
    cuisine_type = models.CharField(max_length=255, default='General')  # New field for cuisine type
    rating = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)  # New field for restaurant rating
    
    def __str__(self):
        return self.name

class Menu(models.Model):
    RESTAURANT_TYPE_CHOICES = [
        ('Veg', 'Vegetarian'),
        ('Non-Veg', 'Non-Vegetarian'),
    ]
    
    restaurant = models.ForeignKey(Restaurant, related_name="menus", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    image_url = models.URLField(max_length=1024, blank=True, null=True)  # Online image URL
    price = models.DecimalField(max_digits=10, decimal_places=2)
    veg_or_non_veg = models.CharField(max_length=7, choices=RESTAURANT_TYPE_CHOICES, default='Veg')  # New field for veg or non-veg
    rating = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)  # New field for dish rating
    
    def __str__(self):
        return f'{self.name} - {self.restaurant.name}'
    
    @staticmethod
    def top_selling_items():
        return (
            Order.objects.values('menu_item__name')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')[:5]
        )

from django.conf import settings

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    menu_item = models.ForeignKey('Menu', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.menu_item.name} - {self.quantity}"
    
from django.db.models import Count
from django.utils.timezone import now

class Order(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ✅ Corrected reference
    items = models.ManyToManyField('Menu', through='OrderItem')
    ordered_at = models.DateTimeField(default=now)

class OrderItem(models.Model):  # ✅ Link orders and items with quantity
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'restaurant')  # Prevent duplicate favorites