
from django.db import models
from django.contrib.auth.models import User

class Gear(models.Model):
	CATEGORY_CHOICES = [
		('camera', 'Camera'),
		('lens', 'Lens'),
		('action_camera', 'Action Camera'),
		('gimbal', 'Gimble'),
		('battery', 'Battery'),
		('memory_card', 'Memory Card'),
	# Removed Camera Bag
		('other', 'Other'),
	]
	name = models.CharField(max_length=100)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
	description = models.TextField(blank=True)
	available = models.BooleanField(default=True)
	image = models.ImageField(upload_to='gear_images/', blank=True, null=True)
	specs = models.TextField(blank=True)
	brand = models.CharField(max_length=50, blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

	def __str__(self):
		return f"{self.name} ({self.get_category_display()})"

class Rental(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	gear = models.ForeignKey(Gear, on_delete=models.CASCADE)
	start_date = models.DateField()
	end_date = models.DateField()
	returned = models.BooleanField(default=False)
	deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
	deposit_refunded = models.BooleanField(default=False)

	def __str__(self):
		return f"{self.user.username} - {self.gear.name} ({self.start_date} to {self.end_date})"

# Optional: User profile extension
class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	phone = models.CharField(max_length=20, blank=True)
	address = models.TextField(blank=True)

	def __str__(self):
		return self.user.username



# Cart model for add-to-cart and cart history
class Cart(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	checked_out = models.BooleanField(default=False)

	def __str__(self):
		return f"Cart {self.id} for {self.user.username} ({'Checked out' if self.checked_out else 'Active'})"

# CartItem model for items in cart
class CartItem(models.Model):
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
	gear = models.ForeignKey(Gear, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)
	added_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.quantity} x {self.gear.name} in Cart {self.cart.id}"
