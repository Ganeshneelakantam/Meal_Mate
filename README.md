# Meal Mate

## Overview
Meal Mate is a full-featured food ordering and delivery application built using Django. It enables users to browse restaurants, view menus, place orders, and manage their accounts. The platform also supports an admin dashboard for restaurant and order management.

## Features

### User Management
- **User Registration & Authentication**: Secure signup and login for customers and admins.
- **Role-Based Access Control**: Separate dashboards for admins and customers.
- **Password Recovery**: OTP-based verification for password reset.
- **User Profile Management**: Edit profile details, including username, email, and address.

### Restaurant & Menu Management (Admin Features)
- **Add, Update, and Delete Restaurants**: Manage restaurant details including name, location, and cuisine type.
- **Menu Management**: Add, update, and remove menu items with details such as name, price, description, and category.
- **Order Tracking**: View and manage customer orders with real-time updates.

### Ordering System
- **Cart Management**: Users can add, remove, and update menu items in their cart.
- **Reorder Functionality**: Users can reorder past purchases for convenience.
- **Order History**: Track previous orders with detailed information.
- **Secure Payments**: Integrated with Razorpay for online payments.

### Admin Dashboard
- **Order Statistics**: View order trends, top-selling items, and customer activity.
- **Customer & Restaurant Management**: Admins can manage registered users and restaurant profiles.
- **Order Summary & Reports**: Generate reports on sales and order trends.

### API Endpoints
- **Restaurant APIs**: Fetch restaurant details and menu items.
- **Cart APIs**: Add, update, and remove items from the cart.
- **Order APIs**: Place orders, view order history, and reorder items.

### Error Handling
- **Custom 404 & 500 Pages**: Improved user experience with error messages.
- **Session Management & Access Control**: Secure user sessions with Django authentication.

## Installation & Setup
### Prerequisites
- Python 3.x
- Django
- PostgreSQL or SQLite

### Steps to Set Up Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/meal-mate.git
   cd meal-mate
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser for admin access:
   ```bash
   python manage.py createsuperuser
   ```
6. Run the development server:
   ```bash
   python manage.py runserver
   ```
7. Open the application in the browser:
   ```
   http://127.0.0.1:8000
   ```
