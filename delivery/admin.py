from django.contrib import admin
from delivery.models import User

# Register your models here.
admin.site.register(User)


from django.contrib import admin
from .models import Order, Menu, Cart

# Admin site statistics
class DashboardStatsAdmin(admin.ModelAdmin):
    change_list_template = 'admin/dashboard_stats.html'

admin.site.register(Menu)
admin.site.register(Cart)


from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Allows adding multiple menu items in an order

class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'ordered_at')  # ✅ Removed 'menu_item' and 'quantity'
    inlines = [OrderItemInline]  # ✅ Show order items inline in admin panel

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)