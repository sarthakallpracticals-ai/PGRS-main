from django.contrib import admin
from .models import Gear, Rental, Profile, Cart, CartItem

@admin.register(Gear)
class GearAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'available')
	search_fields = ('name', 'category')
	list_filter = ('category', 'available')

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
	list_display = ('user', 'gear', 'start_date', 'end_date', 'returned')
	list_filter = ('returned', 'start_date', 'end_date')
	search_fields = ('user__username', 'gear__name')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'phone')
	search_fields = ('user__username', 'phone')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'created_at', 'checked_out')
	list_filter = ('checked_out', 'created_at')
	search_fields = ('user__username',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
	list_display = ('cart', 'gear', 'quantity', 'added_at')
	search_fields = ('cart__user__username', 'gear__name')
