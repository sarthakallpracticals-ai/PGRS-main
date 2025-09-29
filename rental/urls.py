from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.catalogue, name='catalogue'),
    path('login/', auth_views.LoginView.as_view(template_name='rental/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('gear/<int:gear_id>/', views.gear_detail, name='gear_detail'),
    path('gear/<int:gear_id>/book/', views.book_rental, name='book_rental'),
    path('gear/<int:gear_id>/add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/history/', views.cart_history, name='cart_history'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    path('my_rentals/', views.my_rentals, name='my_rentals'),
    path('rental/<int:rental_id>/invoice/', views.download_rental_invoice, name='download_rental_invoice'),
    path('cart/item/<int:item_id>/delete/', views.delete_cart_item, name='delete_cart_item'),
    path('cart/history/<int:cart_id>/delete/', views.delete_cart, name='delete_cart'),
    path('orders/', views.orders_view, name='orders'),
    path('rental/<int:rental_id>/return/', views.return_gear, name='return_gear'),
]