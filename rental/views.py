from .rental_invoice import download_rental_invoice
from decimal import Decimal
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Gear, Rental, Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.db.models import Q

def catalogue(request):
	query = request.GET.get('q', '')
	category = request.GET.get('category', '')
	gear_list = Gear.objects.all()
	if query:
		gear_list = gear_list.filter(Q(name__icontains=query) | Q(description__icontains=query))
	if category:
		gear_list = gear_list.filter(category=category)
	print(f"[DEBUG] Selected category: '{category}', Gear count: {gear_list.count()}")
	categories = Gear.CATEGORY_CHOICES
	return render(request, 'rental/catalogue.html', {'gear_list': gear_list, 'categories': categories, 'selected_category': category, 'query': query})

def gear_detail(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    can_rent = gear.available and request.user.is_authenticated
    return render(request, 'rental/gear_detail.html', {
        'gear': gear,
        'can_rent': can_rent,
    })

@login_required
def book_rental(request, gear_id):
	gear = get_object_or_404(Gear, id=gear_id)
	from datetime import datetime
	if request.method == 'POST' and gear.available:
		start_date = request.POST.get('start_date')
		end_date = request.POST.get('end_date')
		try:
			start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
			end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
		except Exception:
			return render(request, 'rental/book_rental.html', {'gear': gear, 'error': 'Invalid date format.'})

		# Check for overlapping rentals
		overlap = Rental.objects.filter(
			gear=gear,
			returned=False,
			end_date__gte=start_date_obj,
			start_date__lte=end_date_obj
		).exists()
		if overlap:
			return render(request, 'rental/book_rental.html', {'gear': gear, 'error': 'This gear is already booked for the selected dates.'})

		# Calculate deposit (e.g., 20% of gear price, minimum ₹500)
		deposit = max(gear.price * 0.2, 500)
		Rental.objects.create(
			user=request.user,
			gear=gear,
			start_date=start_date_obj,
			end_date=end_date_obj,
			deposit_amount=deposit,
			deposit_refunded=False
		)
		gear.available = False
		gear.save()
		return redirect('my_rentals')
	return render(request, 'rental/book_rental.html', {'gear': gear})

@login_required
def my_rentals(request):
	from datetime import date
	rentals = Rental.objects.filter(user=request.user).order_by('-start_date')
	today = date.today()
	return render(request, 'rental/my_rentals.html', {'rentals': rentals, 'today': today})


@login_required
def return_gear(request, rental_id):
	rental = get_object_or_404(Rental, id=rental_id, user=request.user)
	if rental.returned:
		return redirect('my_rentals')
	guidelines = [
		"Gear must be returned in the same condition as rented.",
		"Late returns may incur additional charges.",
		"Report any damage or issues immediately.",
		"PixelGEAR reserves the right to inspect returned gear before finalizing return.",
	]
	if request.method == 'POST':
		rental.returned = True
		rental.save()
		rental.gear.available = True
		rental.gear.save()
		# Refund deposit (if no penalty)
		if not rental.deposit_refunded:
			from .penalty_utils import calculate_penalty
			penalty = calculate_penalty(rental)
			if penalty == 0:
				rental.deposit_refunded = True
				rental.save()
		else:
			from .penalty_utils import calculate_penalty
			penalty = calculate_penalty(rental)
		return render(request, 'rental/return_confirmation.html', {'rental': rental, 'penalty': penalty})
	return render(request, 'rental/return_gear.html', {'rental': rental, 'guidelines': guidelines})

def register(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('catalogue')
	else:
		form = UserCreationForm()
	return render(request, 'rental/register.html', {'form': form})

def add_to_cart(request, gear_id):
	if not request.user.is_authenticated:
		return redirect('login')
	gear = get_object_or_404(Gear, id=gear_id)
	cart, created = Cart.objects.get_or_create(user=request.user, checked_out=False)
	cart_item, created = CartItem.objects.get_or_create(cart=cart, gear=gear)
	if not created:
		if cart_item.quantity < 5:
			cart_item.quantity += 1
			cart_item.save()
	else:
		cart_item.quantity = 1
		cart_item.save()
	return redirect('cart')

@login_required
@login_required
def cart_view(request):
	cart = Cart.objects.filter(user=request.user, checked_out=False).first()
	items = cart.items.all() if cart else []
	total = sum(item.gear.price * item.quantity for item in items)
	return render(request, 'rental/cart.html', {'cart': cart, 'items': items, 'total': total})

@login_required
def delete_cart_item(request, item_id):
	item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__checked_out=False)
	item.delete()
	return redirect('cart')

@login_required
def cart_history(request):
	carts = Cart.objects.filter(user=request.user, checked_out=True).order_by('-created_at')
	return render(request, 'rental/cart_history.html', {'carts': carts})

@login_required
def delete_cart(request, cart_id):
	cart = get_object_or_404(Cart, id=cart_id, user=request.user, checked_out=True)
	cart.delete()
	return redirect('cart_history')

@login_required
def checkout_cart(request):
	cart = Cart.objects.filter(user=request.user, checked_out=False).first()
	items = cart.items.all() if cart else []
	total = sum(item.gear.price * item.quantity for item in items)
	if not cart:
		return redirect('cart')
	if request.method == 'POST':
		# If billing form submitted
		if all(field in request.POST for field in ['name', 'address', 'phone', 'start_date', 'end_date']):
			name = request.POST['name']
			address = request.POST['address']
			phone = request.POST['phone']
			start_date = request.POST['start_date']
			end_date = request.POST['end_date']
			import re
			errors = []
			if not re.match(r'^[A-Za-z ]+$', name):
				errors.append('Name must contain only letters and spaces.')
			if not re.match(r'^\d{10}$', phone):
				errors.append('Phone must be a 10-digit number.')
			if not address.strip():
				errors.append('Address cannot be empty.')
			if not start_date or not end_date:
				errors.append('Rental period must be specified.')
			if errors:
				return render(request, 'rental/billing.html', {
					'cart': cart,
					'items': items,
					'total': total,
					'errors': errors
				})
			from datetime import datetime
			try:
				start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
				end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
			except Exception:
				return render(request, 'rental/billing.html', {
					'cart': cart,
					'items': items,
					'total': total,
					'errors': ['Invalid date format.']
				})
			# Create Rental records for each cart item
			for item in items:
				deposit = max(item.gear.price * Decimal('0.2'), Decimal('500'))
				Rental.objects.create(
					user=request.user,
					gear=item.gear,
					start_date=start_date_obj,
					end_date=end_date_obj,
					deposit_amount=deposit,
					deposit_refunded=False
				)
				item.gear.available = False
				item.gear.save()
			cart.checked_out = True
			cart.save()
			return redirect('orders')
		# Otherwise, show billing form
		return render(request, 'rental/billing.html', {
			'cart': cart,
			'items': items,
			'total': total
		})
	# GET: show billing form
	return render(request, 'rental/billing.html', {
		'cart': cart,
		'items': items,
		'total': total
	})

@login_required
@login_required
def orders_view(request):
	orders = Cart.objects.filter(user=request.user, checked_out=True).order_by('-created_at')
	return render(request, 'rental/orders.html', {'orders': orders})

@login_required
def download_invoice(request, cart_id):
	cart = get_object_or_404(Cart, id=cart_id, user=request.user, checked_out=True)
	response = HttpResponse(content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="invoice_cart_{cart.id}.pdf"'
	p = canvas.Canvas(response, pagesize=letter)
	width, height = letter
	# Header with logo image and company info
	try:
		p.drawImage(r"c:/Users/Sahil Devidas Jedhe/Searches/Downloads/Gemini_Generated_Image_183enu183enu183e.png", 40, height-100, width=60, height=60, mask='auto')
	except Exception:
		# fallback to placeholder if image not found
		p.setFillColorRGB(0.2, 0.4, 0.6)
		p.roundRect(40, height-100, 60, 60, 10, fill=1)
		p.setFillColorRGB(1, 1, 1)
		p.setFont("Helvetica-Bold", 22)
		p.drawString(55, height-65, "PG")
	p.setFillColorRGB(0, 0, 0)
	p.setFont("Helvetica-Bold", 26)
	p.drawString(120, height-60, "PixelGEAR")
	p.setFont("Helvetica", 12)
	p.drawString(120, height-80, "www.pixelgear.com | support@pixelgear.com")
	# Invoice info box
	p.setFillColorRGB(0.95, 0.95, 0.95)
	p.roundRect(width-220, height-100, 160, 60, 10, fill=1, stroke=0)
	p.setFillColorRGB(0, 0, 0)
	p.setFont("Helvetica-Bold", 12)
	p.drawString(width-210, height-70, f"Invoice #: {cart.id}")
	p.setFont("Helvetica", 12)
	p.drawString(width-210, height-85, f"Date: {cart.created_at.strftime('%Y-%m-%d %H:%M')}")
	# Section line
	p.setStrokeColorRGB(0.8, 0.8, 0.8)
	p.setLineWidth(1)
	p.line(40, height-110, width-40, height-110)
	# Billing info
	y = height - 130
	p.setFont("Helvetica-Bold", 13)
	p.drawString(50, y, "Billed To:")
	p.setFont("Helvetica", 12)
	p.drawString(120, y, f"{cart.user.username}")
	y -= 30
	# Items table header
	p.setFont("Helvetica-Bold", 12)
	p.drawString(50, y, "Qty")
	p.drawString(90, y, "Item")
	p.drawString(260, y, "Brand")
	p.drawString(350, y, "Price")
	p.drawString(420, y, "Subtotal")
	y -= 10
	p.setStrokeColorRGB(0.8, 0.8, 0.8)
	p.line(40, y, width-40, y)
	y -= 18
	p.setFont("Helvetica", 11)
	total = 0
	for item in cart.items.all():
		p.drawString(50, y, str(item.quantity))
		p.drawString(90, y, item.gear.name)
		p.drawString(260, y, item.gear.brand)
		p.drawString(350, y, f"₹{item.gear.price}")
		subtotal = item.gear.price * item.quantity
		p.drawString(420, y, f"₹{subtotal}")
		total += subtotal
		y -= 18
		if y < 100:
			# Draw total at the bottom of the page if items overflow
			p.setStrokeColorRGB(0.8, 0.8, 0.8)
			p.line(40, y, width-40, y)
			p.setFillColorRGB(0.95, 0.95, 0.95)
			p.roundRect(350, 60, 150, 35, 8, fill=1, stroke=0)
			p.setFillColorRGB(0, 0, 0)
			p.setFont("Helvetica-Bold", 13)
			p.drawString(360, 80, "Total:")
			p.setFont("Helvetica-Bold", 14)
			p.drawString(420, 80, f"₹{total}")
			p.showPage()
			y = height - 150
	# Section line above total
	y -= 10
	p.setStrokeColorRGB(0.8, 0.8, 0.8)
	p.line(40, y, width-40, y)
	y -= 25
	# Total summary box (always at bottom right)
	p.setFillColorRGB(0.95, 0.95, 0.95)
	p.roundRect(350, y, 150, 35, 8, fill=1, stroke=0)
	p.setFillColorRGB(0, 0, 0)
	p.setFont("Helvetica-Bold", 13)
	p.drawString(360, y+20, "Total:")
	p.setFont("Helvetica-Bold", 14)
	p.drawString(420, y+20, f"₹{total}")
	p.showPage()
	p.save()
	return response
