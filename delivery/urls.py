from django.urls import path
from django.conf.urls import handler404, handler500
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import get_menu_items
from delivery.views import add_menu


urlpatterns = [
    path('', views.index, name="index"),
    path('home/', views.home, name='home'),  # Add this line for the home view
    path('admin_home/', views.admin_home, name='admin_home'),  # Admin home URL
    path('login/', views.handle_login, name='handle_login'),  # Login handler
    path('signup/', views.handle_signup, name='handle_signup'),  # Signup handler
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('login/', views.index, name='login'),  # Add this line for the login URL
    path('logout/', views.index, name='logout'),
    path('add_restaurant/', views.add_restaurant, name='add_restaurant'),
    path('add-menu/', add_menu, name='add_menu'),
    path('view_menu/<int:restaurant_id>/', views.view_menu, name='view_menu'),
    
    path('add-restaurant-menu/', views.add_restaurant_menu, name='add-restaurant-menu'),

    path('details/<str:type>/', views.admin_details, name='admin_details'),

    path('orders-summary/', views.orders_summary, name='orders_summary'),

    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('update_cart/', views.update_cart, name='update_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('payment-success/', views.payment_success, name='payment_success'),


    path('clear_cart/', views.clear_cart, name='clear_cart'),

    path('update_restaurant/<int:restaurant_id>/', views.update_restaurant, name='update_restaurant'),
    path('update_menu/<int:menu_id>/', views.update_menu, name='update_menu'),
    path('delete_restaurant/<int:restaurant_id>/', views.delete_restaurant, name='delete_restaurant'),
    path('delete_menu/<int:menu_id>/', views.delete_menu, name='delete_menu'),
    path('get_menu_items/<int:restaurant_id>/', get_menu_items, name='get_menu_items'),


    path('cuisine/<str:cuisine_type>/', views.filter_restaurants_by_cuisine, name='restaurants_by_cuisine'),
    

    path('search_restaurants/', views.search_restaurants, name='search_restaurants'),


    path('reorder/<int:order_id>/', views.reorder, name='reorder'),
    path('order-history/', views.order_history, name='order_history'),


    path("profile/", views.user_profile, name="user_profile"),
    path("update-profile/", views.user_profile, name="update_profile"),  # Profile Update


    path('order_details/<int:order_id>/', views.order_details_page, name='order_details_page'),

    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),

    # path('add_favorite/', views.add_to_favorites, name='add_favorite'),
    # path('remove_favorite/', views.remove_from_favorites, name='remove_favorite'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path("toggle_favorite/<int:restaurant_id>/", views.toggle_favorite, name="toggle_favorite"),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'delivery.views.custom_404_view'
handler500 = 'delivery.views.custom_500_view'

