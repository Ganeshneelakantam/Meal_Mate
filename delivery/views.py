from urllib import request
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from delivery.models import User  # Use your custom User model
from django.views.decorators.cache import cache_control
from django.core.mail import send_mail
from django.conf import settings
from random import randint
from .forms import ForgotPasswordForm, OTPForm, NewPasswordForm
from django.utils.timezone import now  # Import the timezone module
from .models import Restaurant, Menu, Cart, OrderItem
from django.contrib import messages
from .forms import RestaurantForm, MenuForm
from django.http import JsonResponse

# Create your views here.
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    return render(request, 'delivery/index.html')


from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now

User = get_user_model()

def handle_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            request.session['username'] = user.username
            request.session['role'] = user.role

            user.last_login = now()
            user.save()

            # Check if it's an admin and the username follows the correct pattern
            if user.role == 'admin' and user.username.endswith('_mm@admin'):
                return redirect('admin_home')
            elif user.role == 'customer':
                return redirect('home')
            else:
                return redirect('home')  # If username doesn't match, redirect to customer home
        else:
            error_message = "Invalid username or password!"
            return render(request, 'delivery/index.html', {'error_message': error_message})
    else:
        return render(request, 'delivery/index.html')


def handle_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        password = make_password(request.POST.get('password'))
        address = request.POST.get('address')

        # Set role based on username
        role = 'admin' if username.endswith('mm@admin') else 'customer'

        user = User(
            username=username,
            email=email,
            mobile=mobile,
            password=password,
            address=address,
            role=role
        )
        user.save()

        # Send a welcome email
        subject = "Welcome to Meal-Mate!"
        message = f"""
        Hi {username},

        Thank you for registering with Meal-Mate! We're thrilled to have you on board.

        Explore delicious meals and enjoy the best service we offer.

        If you have any questions, feel free to reach out to us at {settings.EMAIL_HOST_USER}.

        Happy dining,
        The Meal-Mate Team
        """
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        
        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}")
        
        return render(request, 'delivery/index.html', {'success_message': "Account created successfully!"})
    else:
        return render(request, 'delivery/404.html')

    

from django.db.models import Count

from django.contrib.auth import get_user_model
User = get_user_model()  # ✅ This ensures the correct user model is used

def admin_home(request):
    username = request.session.get('username', 'Admin')

    # Fetch restaurant order counts and rank them correctly
    restaurant_rankings = (
        OrderItem.objects.values('menu_item__restaurant__id', 'menu_item__restaurant__name')
        .annotate(order_count=Count('id'))
        .order_by('-order_count')
    )

    customer_count = User.objects.filter(role='customer').count()  # ✅ Use `User` from `get_user_model()`
    admin_count = User.objects.filter(role='admin').count()  # ✅ Fix AttributeError
    restaurant_count = Restaurant.objects.count()
    orders_count = Order.objects.count()

    context = {
        'username': username,
        'customer_count': customer_count,
        'admin_count': admin_count,
        'restaurant_count': restaurant_count,
        'orders_count': orders_count,
        'restaurant_rankings': restaurant_rankings,
    }

    return render(request, 'delivery/admin_home.html', context)



def home(request):
    username = request.session.get('username', 'Customer')
    menu_items = Menu.objects.all()
    restaurants = Restaurant.objects.all()  # Fetch all restaurants from the database
    if request.user.is_authenticated:
        recent_orders = Order.objects.filter(customer=request.user).order_by('-ordered_at')[:5]  
    else:
        recent_orders = []  # Or handle it differently (e.g., redirect to login)


    order_history = []
    for order in recent_orders:
        items = OrderItem.objects.filter(order=order).select_related('menu_item')
        order_history.append({
            'order': order,
            'items': items,
        })

    return render(request, 'delivery/home.html', {'username': username, 'restaurants': restaurants, 'menu_items': menu_items, 'order_history': order_history})


from django.http import JsonResponse
from .models import Restaurant

def get_restaurants(request):
    # Assuming you want to return a list of restaurants as JSON
    restaurants = Restaurant.objects.all()
    restaurant_data = [{"id": r.id, "name": r.name, "address": r.address} for r in restaurants]
    return JsonResponse({"restaurants": restaurant_data})


from django.shortcuts import redirect, get_object_or_404
from .models import Order, OrderItem, Cart

def reorder(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    order_items = OrderItem.objects.filter(order=order)

    for item in order_items:
        # Add each item to the cart
        Cart.objects.create(user=request.user, menu_item=item.menu_item, quantity=item.quantity)

    return redirect('delivery/view_cart.html')  # Redirect to cart page after reordering


def order_history(request):
    # Fetch the user's past orders
    past_orders = Order.objects.filter(customer=request.user).order_by('-ordered_at')

    # Prepare the order history data
    order_history = []
    for order in past_orders:
        items = OrderItem.objects.filter(order=order).select_related('menu_item')
        total_cost = sum(item.menu_item.price * item.quantity for item in items)
        order_history.append({
            'order': order,
            'items': items,
            'total_cost': total_cost,
        })

    return render(request, 'delivery/order_history.html', {'order_history': order_history})



# Store OTP temporarily in a global variable (you can use session for production)
otp_store = {}

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate OTP
                otp = str(randint(100000, 999999))
                otp_store[email] = otp  # Store OTP temporarily
                send_mail(
                    'Your OTP for Meal-Mate Password Reset',
                    f'Your OTP is: {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                request.session['email'] = email  # Store the email in the session
                return redirect('verify_otp')
            except User.DoesNotExist:
                form.add_error('email', 'Email not found')
    else:
        form = ForgotPasswordForm()
    return render(request, 'delivery/forgot_password.html', {'form': form})

def verify_otp(request):
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            email = request.session.get('email')  # Get the email from session
            if email and otp_store.get(email) == entered_otp:
                return redirect('reset_password')
            else:
                form.add_error('otp', 'Invalid OTP')
    else:
        form = OTPForm()
    return render(request, 'delivery/verify_otp.html', {'form': form})

def reset_password(request):
    if request.method == 'POST':
        form = NewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']
            if new_password == confirm_password:
                email = request.session.get('email')
                if email:
                    try:
                        user = User.objects.get(email=email)
                        user.password = make_password(new_password)  # Hash the new password
                        user.save()
                        del request.session['email']
                        return redirect('login')
                    except User.DoesNotExist:
                        form.add_error(None, 'User not found')
                else:
                    form.add_error(None, 'No email found in session')
            else:
                form.add_error('confirm_password', 'Passwords do not match')
    else:
        form = NewPasswordForm()
    return render(request, 'delivery/reset_password.html', {'form': form})

def handle_logout(request):
    request.session.flush()
    return redirect('login')

from django.core.cache import cache

def send_otp(email):
    otp = str(randint(100000, 999999))
    cache.set(email, otp, timeout=300)  # 5 minutes


from django.contrib.auth import logout

def handle_logout(request):
    """
    Logs out the user and redirects them to the login page.
    """
    logout(request)  # This logs out the current user
    return redirect('login')  # Redirect to the login page


def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)

# Add Restaurant
def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        location = request.POST.get('location')
        cuisine_type = request.POST.get('cuisine_type')  # Added field for cuisine_type
        rating = request.POST.get('rating')  # Added field for rating
        image_url = request.POST.get('image_url')

        # Create the restaurant with new fields
        restaurant = Restaurant(
            name=name,
            description=description,
            location=location,
            cuisine_type=cuisine_type,
            rating=rating,
            image_url=image_url
        )
        restaurant.save()
        messages.success(request, f'Restaurant "{restaurant.name}" successfully added!')  # Add success message
        return redirect('add-restaurant-menu')  # Redirect to admin dashboard after adding restaurant
    
    return render(request, 'delivery/admin_home.html')  # Show the form to add restaurant


# View for adding restaurant and menu
def add_restaurant_menu(request):
    # Pass the list of restaurants to the template
    restaurants = Restaurant.objects.all()
    return render(request, 'delivery/add_restaurant_menu.html', {'restaurants': restaurants})


# Add New Menu Item
def add_menu(request):
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant')
        if not restaurant_id:
            return render(request, 'delivery/add_restaurant_menu.html', {
                'error_message': "Please select a restaurant.",
            })

        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            veg_or_non_veg = request.POST.get('veg_or_non_veg')
            rating = request.POST.get('rating')
            image_url = request.POST.get('image_url')

            # Validate required fields
            if not name or not description or not price:
                restaurants = Restaurant.objects.all()
                return render(request, 'delivery/add_restaurant_menu.html', {
                    'error_message': "All fields are required.",
                    'restaurants': restaurants
                })

            menu_item = Menu(
                restaurant=restaurant,
                name=name,
                description=description,
                price=price,
                veg_or_non_veg=veg_or_non_veg,
                rating=rating,
                image_url=image_url
            )
            menu_item.save()
            messages.success(request, f'Menu item "{menu_item.name}" successfully added!')
            return redirect('add_menu')

        except Restaurant.DoesNotExist:
            return render(request, 'delivery/add_restaurant_menu.html', {
                'error_message': "Selected restaurant does not exist.",
            })

    return render(request, 'delivery/add_restaurant_menu.html')


# View menu for a restaurant
def view_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menus = Menu.objects.filter(restaurant=restaurant)
    
    # Get cart quantities for current user
    cart_items = Cart.objects.filter(user=request.user, menu_item__in=menus)
    cart_quantity_dict = {item.menu_item_id: item.quantity for item in cart_items}
    
    for menu in menus:
        menu.cart_quantity = cart_quantity_dict.get(menu.id, 0)
    
    return render(request, 'delivery/view_menu.html', {
        'restaurant': restaurant,
        'menus': menus
    })

# Get all restaurants (for JSON API)
def get_restaurants(request):
    restaurants = Restaurant.objects.values('id', 'name', 'description', 'location', 'cuisine_type', 'rating', 'image_url')
    return JsonResponse({'restaurants': list(restaurants)})


from django.contrib import messages  # Import messages framework

# Update Restaurant
def update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)

    if request.method == "POST":
        form = RestaurantForm(request.POST, request.FILES, instance=restaurant)
        
        # Handle the image URL if provided
        image_url = request.POST.get("image_url", None)
        if image_url:
            restaurant.image = None  # Nullify local image if URL is provided
            restaurant.image_url = image_url  # Assuming you have a `image_url` field in your model
            
        if form.is_valid():
            form.save()
            messages.success(request, f'Restaurant "{restaurant.name}" successfully updated!')  # Add success message
            return redirect('admin_home')  # Redirect to some success page
    else:
        form = RestaurantForm(instance=restaurant)

    return render(request, 'delivery/update_restaurant.html', {'form': form, 'restaurant': restaurant})

# Update Menu
def update_menu(request, menu_id):
    menu = get_object_or_404(Menu, pk=menu_id)

    if request.method == "POST":
        form = MenuForm(request.POST, request.FILES, instance=menu)
        
        # Handle the image URL if provided
        image_url = request.POST.get("image_url", None)
        if image_url:
            menu.image = None  # Nullify local image if URL is provided
            menu.image_url = image_url  # Assuming you have a `image_url` field in your model
            
        if form.is_valid():
            form.save()
            messages.success(request, f'Menu "{menu.name}" successfully updated!')  # Add success message
            return redirect('admin_home')  # Redirect to some success page
    else:
        form = MenuForm(instance=menu)

    return render(request, 'delivery/update_menu.html', {'form': form, 'menu': menu})

# Delete Restaurant
def delete_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    restaurant.delete()
    messages.success(request, 'Restaurant deleted successfully!')
    return redirect('admin_home')

# Delete Menu item
def delete_menu(request, menu_id):
    menu_item = get_object_or_404(Menu, id=menu_id)
    menu_item.delete()
    messages.success(request, 'Menu item deleted successfully!')
    return redirect('admin_home')

# Get menu items for a specific restaurant (JSON API)
def get_menu_items(request, restaurant_id):
    # Get menu items for the selected restaurant
    menu_items = Menu.objects.filter(restaurant_id=restaurant_id)
    items_data = []

    for item in menu_items:
        items_data.append({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'restaurant': item.restaurant.name,
            'veg_or_non_veg': item.veg_or_non_veg,  # Added veg_or_non_veg field
            'rating': item.rating,  # Added rating field
        })

    return JsonResponse({'menu_items': items_data})

def admin_details(request, type):
    context = {}
    if type == 'customer':
        context['data'] = User.objects.filter(role='customer')
        context['header'] = 'Customer Details'
    elif type == 'admin':
        context['data'] = User.objects.filter(role='admin')
        context['header'] = 'Admin Details'
    elif type == 'restaurant':
        context['data'] = Restaurant.objects.all()
        context['header'] = 'Restaurant Details'
    else:
        context['data'] = []
        context['header'] = 'Invalid Selection'
    return render(request, 'delivery/admin_details.html', context)


from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from .models import Cart, Menu

@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            menu_id = data.get('menu_id')
            
            # Check if menu_id is provided
            if not menu_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Menu ID is required.'
                })

            # Fetch the menu item
            try:
                menu_item = Menu.objects.get(id=menu_id)
            except Menu.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Menu item not found.'
                })

            restaurant_id = menu_item.restaurant.id

            # Check for existing cart items from different restaurants
            cart_items = Cart.objects.filter(user=request.user)
            if cart_items.exists():
                first_restaurant_id = cart_items.first().menu_item.restaurant.id
                if first_restaurant_id != restaurant_id:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Your cart contains items from another restaurant. Clear cart first.'
                    })

            # Add item to cart
            cart_item, created = Cart.objects.get_or_create(
                user=request.user,
                menu_item=menu_item,
                defaults={'quantity': 1}
            )

            if not created:
                cart_item.quantity += 1
                cart_item.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Item added to cart',
                'quantity': cart_item.quantity
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    })


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def update_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            menu_item_id = data.get('menu_item_id')
            quantity_change = int(data.get('quantity_change'))

            cart_item = Cart.objects.get(user=request.user, menu_item_id=menu_item_id)
            cart_item.quantity += quantity_change

            if cart_item.quantity <= 0:
                cart_item.delete()
                quantity = 0
            else:
                cart_item.save()
                quantity = cart_item.quantity

            cart_items = Cart.objects.filter(user=request.user)
            total = sum(item.quantity * item.menu_item.price for item in cart_items)

            return JsonResponse({
                'success': True,
                'quantity': quantity,
                'subtotal': quantity * cart_item.menu_item.price,
                'total': total,
            })
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Item not in cart.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


import razorpay
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Menu, Cart

@login_required(login_url='/')
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    cart_data = []
    total_amount = 0

    # Process each cart item
    for item in cart_items:
        subtotal = item.quantity * item.menu_item.price
        total_amount += subtotal
        cart_data.append({
            'id': item.menu_item.id,
            'name': item.menu_item.name,
            'price': item.menu_item.price,
            'quantity': item.quantity,
            'subtotal': subtotal,
            'image_url': item.menu_item.image_url,
        })

    total_amount = float(total_amount)  # Convert total amount to float

    # Initialize Razorpay client if cart has items
    if total_amount > 0:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create a Razorpay order
        order_amount = total_amount * 100  # Convert to paise (smallest unit of currency)
        order_currency = 'INR'
        order_receipt = f'order_{request.user.id}_{int(total_amount)}'

        order = client.order.create(dict(
            amount=order_amount,
            currency=order_currency,
            receipt=order_receipt,
            notes={'description': 'Order for food delivery'}
        ))

        razorpay_order_id = order['id']
        razorpay_key_id = settings.RAZORPAY_KEY_ID

        return render(request, 'delivery/cart.html', {
            'cart_items': cart_data,
            'total_amount': total_amount,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_key_id': razorpay_key_id,
        })

    else:
        return render(request, 'delivery/cart.html', {
            'cart_items': cart_data,
            'total_amount': total_amount,
            'error_message': 'Your cart is empty. Go add some delicious items!',
        })

from django.http import JsonResponse
from .models import Cart

def clear_cart(request):
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)

        if not cart_items.exists():
            return JsonResponse({'status': 'error', 'message': "Your cart is empty."})

        # Get restaurant from cart (all items will be from the same restaurant)
        restaurant = cart_items.first().menu_item.restaurant

        # Create a single order for all items in the cart
        new_order = Order.objects.create(
            customer=request.user,
            ordered_at=now()
        )

        # Save each cart item as part of the single order
        for item in cart_items:
            new_order.items.add(item.menu_item, through_defaults={'quantity': item.quantity})

        cart_items.delete()  # Clear cart after placing order

        return redirect('payment_success')
    
from django.shortcuts import render
from .models import Order

def payment_success(request):
    orders = Order.objects.all()  # Fetch all orders
    print(f"Total Orders: {orders.count()}")  # Debug: Print total orders
    return render(request, 'delivery/payment_success.html', {'orders': orders})

from django.utils import timezone
from django.db.models import Count
from django.contrib.sessions.models import Session
from django.shortcuts import render
from .models import OrderItem, Order, Restaurant

def orders_summary(request):
    today = timezone.now().date()
    one_month_ago = today - timezone.timedelta(days=30)
    three_months_ago = today - timezone.timedelta(days=90)
    six_months_ago = today - timezone.timedelta(days=180)
    one_year_ago = today - timezone.timedelta(days=365)

    # Orders Stats
    orders_today = Order.objects.filter(ordered_at__date=today).count()
    orders_this_week = Order.objects.filter(ordered_at__gte=today - timezone.timedelta(days=7)).count()
    orders_this_month = Order.objects.filter(ordered_at__gte=one_month_ago).count()

    # Orders Trends
    monthly_orders = Order.objects.filter(ordered_at__gte=one_month_ago).count()
    quarterly_orders = Order.objects.filter(ordered_at__gte=three_months_ago).count()
    half_yearly_orders = Order.objects.filter(ordered_at__gte=six_months_ago).count()
    yearly_orders = Order.objects.filter(ordered_at__gte=one_year_ago).count()

    # Active Users
    active_users = Session.objects.filter(expire_date__gte=timezone.now()).count()

    # 🛠️ Fetch Most Ordered Item
    most_ordered_item_data = (
        OrderItem.objects.values('menu_item__name', 'menu_item__restaurant__name')
        .annotate(order_count=Count('id'))
        .order_by('-order_count')
        .first()
    )
    most_ordered_item_name = most_ordered_item_data['menu_item__name'] if most_ordered_item_data else 'N/A'
    most_ordered_item_restaurant = most_ordered_item_data['menu_item__restaurant__name'] if most_ordered_item_data else 'N/A'

    # 🛠️ Fetch Top 5 Restaurants by Orders
    top_restaurants = (
        OrderItem.objects.values('menu_item__restaurant__name')
        .annotate(order_count=Count('id'))
        .order_by('-order_count')[:5]
    )
    restaurant_names = [r['menu_item__restaurant__name'] for r in top_restaurants]
    restaurant_orders = [r['order_count'] for r in top_restaurants]

    # 🥗 Fetch Food Category Popularity
    food_category_popularity = (
        Restaurant.objects.annotate(total_orders=Count('menus__orderitem'))
        .values('cuisine_type', 'total_orders')
        .order_by('-total_orders')
    )
    cuisine_names = [c['cuisine_type'] for c in food_category_popularity]
    cuisine_orders = [c['total_orders'] for c in food_category_popularity]

    return render(
        request,
        'delivery/orders_summary.html',
        {
            "orders_today": orders_today,
            "orders_this_week": orders_this_week,
            "orders_this_month": orders_this_month,
            "active_users": active_users,
            "most_ordered_item_name": most_ordered_item_name,
            "most_ordered_item_restaurant": most_ordered_item_restaurant,
            "monthly_orders": monthly_orders,
            "quarterly_orders": quarterly_orders,
            "half_yearly_orders": half_yearly_orders,
            "yearly_orders": yearly_orders,
            "restaurant_names": restaurant_names,
            "restaurant_orders": restaurant_orders,
            "cuisine_names": cuisine_names,
            "cuisine_orders": cuisine_orders,
        },
    )


# views.py
from django.shortcuts import render
from .models import Restaurant

from django.shortcuts import render
from django.db.models import Q
from .models import Restaurant

def filter_restaurants_by_cuisine(request, cuisine_type):
    # Convert the string into a list of cuisines
    cuisine_list = [c.strip() for c in cuisine_type.split(",")]  

    # Create a Q object to filter restaurants matching any of the cuisines
    query = Q()
    for cuisine in cuisine_list:
        query |= Q(menus__name__icontains=cuisine)

    # Query the database using the dynamically built Q object
    restaurants = Restaurant.objects.filter(query).distinct()  # Avoid duplicates

    return render(
        request, 
        'delivery/restaurants_by_cuisine.html', 
        {'restaurants': restaurants, 'cuisine_type': cuisine_type, 'cuisine_list': cuisine_list}
    )



from django.http import JsonResponse
from django.db.models import Q
from .models import Restaurant, Menu  # Import MenuItem if applicable

def search_restaurants(request):
    query = request.GET.get('query', '').strip()
    if query:
        # Search in Restaurant name, cuisine type, and location
        restaurant_results = Restaurant.objects.filter(
            Q(name__icontains=query) |
            Q(cuisine_type__icontains=query) |
            Q(location__icontains=query)
        )

        # Search in MenuItem name and associate with the restaurant
        menu_item_results = Menu.objects.filter(name__icontains=query).select_related('restaurant')

        # Combine restaurant and menu item results
        results = [
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "description": restaurant.cuisine_type,
                "type": "Restaurant",
                "image_url": restaurant.image_url  # Include restaurant image URL
            }
            for restaurant in restaurant_results
        ] + [
            {
                "id": menu_item.restaurant.id,
                "name": menu_item.restaurant.name,
                "description": f"Menu Item: {menu_item.name}",
                "type": "Menu Item",
                "image_url": menu_item.image_url  # Include menu item image URL
            }
            for menu_item in menu_item_results
        ]

    else:
        results = []

    return JsonResponse(results, safe=False)




from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import User

@login_required
def user_profile(request):
    if request.method == "POST":
        user = request.user
        user.username = request.POST.get("username", user.username)
        user.email = request.POST.get("email", user.email)
        user.mobile = request.POST.get("phone", user.mobile)
        user.address = request.POST.get("address", user.address)
        user.save()
        # return redirect("user_profile")
    
        # Add success message
        messages.success(request, "Profile updated successfully!")

    return render(request, "delivery/user_profile.html", {"user": request.user})


from django.shortcuts import render, get_object_or_404
from .models import Order, OrderItem

def order_details_page(request, order_id):
    try:
        # Fetch the order
        order = Order.objects.get(id=order_id, customer=request.user)
        
        # Fetch the order items
        items = OrderItem.objects.filter(order=order).values(
            'menu_item__name', 
            'quantity', 
            'menu_item__price'
        )

        # Get restaurant details
        first_item = OrderItem.objects.filter(order=order).first()
        restaurant_name = first_item.menu_item.restaurant.name if first_item else "Unknown Restaurant"
        restaurant_image_url = first_item.menu_item.restaurant.image_url if first_item else ""

        # Calculate total cost
        total_cost = sum(item['menu_item__price'] * item['quantity'] for item in items)

        # Prepare the context data
        context = {
            'order': {
                'restaurant_name': restaurant_name,
                'restaurant_image_url': restaurant_image_url,
                'order_number': order.id,
                'ordered_at': order.ordered_at.strftime('%d %b %Y at %I:%M %p'),
                'total_cost': total_cost,
                'items': [
                    {
                        'name': item['menu_item__name'],
                        'quantity': item['quantity'],
                        'price': item['menu_item__price'],
                    }
                    for item in items
                ],
            }
        }
        return render(request, 'delivery/order_details.html', context)

    except Order.DoesNotExist:
        return render(request, 'delivery/404.html', {'message': 'Order not found.'})

    

from django.http import JsonResponse
from .models import Order

def delete_order(request, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id, customer=request.user)
            order.delete()
            return JsonResponse({'status': 'success', 'message': 'Order deleted successfully.'})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


# from django.shortcuts import get_object_or_404
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.contrib.auth.decorators import login_required
# from .models import Favorite, Restaurant

# @csrf_exempt  # Temporarily disable CSRF (remove this later and use AJAX with CSRF token)
# @login_required
# def add_to_favorites(request):
#     if request.method == "POST":
#         restaurant_id = request.POST.get("restaurant_id")
#         restaurant = get_object_or_404(Restaurant, id=restaurant_id)
#         favorite, created = Favorite.objects.get_or_create(user=request.user, restaurant=restaurant)
#         if created:
#             return JsonResponse({"status": "added"})
#         return JsonResponse({"status": "exists"})
#     return JsonResponse({"status": "error"}, status=400)

# @csrf_exempt
# @login_required
# def remove_from_favorites(request):
#     if request.method == "POST":
#         restaurant_id = request.POST.get("restaurant_id")
#         restaurant = get_object_or_404(Restaurant, id=restaurant_id)
#         deleted, _ = Favorite.objects.filter(user=request.user, restaurant=restaurant).delete()
#         if deleted:
#             return JsonResponse({"status": "removed"})
#         return JsonResponse({"status": "not found"})
#     return JsonResponse({"status": "error"}, status=400)


def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related("restaurant")
    favorite_restaurants = [fav.restaurant for fav in favorites]  # Extract only restaurants
    return render(request, "delivery/favorites.html", {"favorites": favorite_restaurants})



from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Restaurant, Favorite

@login_required
def toggle_favorite(request, restaurant_id):
    if request.method == "POST":
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        favorite, created = Favorite.objects.get_or_create(user=request.user, restaurant=restaurant)

        if created:
            message = "Added to favorites"
        else:
            favorite.delete()
            message = "Removed from favorites"

        return JsonResponse({"success": True, "message": message})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

