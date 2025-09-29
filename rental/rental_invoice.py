from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.shortcuts import get_object_or_404
from datetime import date, datetime
from .models import Rental
from django.contrib.auth.decorators import login_required

@login_required
def download_rental_invoice(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)
    from .penalty_utils import calculate_penalty
    penalty = calculate_penalty(rental)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_rental_{rental.id}.pdf"'
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    # Header
    try:
        p.drawImage(r"c:/Users/Sahil Devidas Jedhe/Searches/Downloads/Gemini_Generated_Image_183enu183enu183e.png", 40, height-100, width=60, height=60, mask='auto')
    except Exception:
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
    # Invoice info
    p.setFillColorRGB(0.95, 0.95, 0.95)
    p.roundRect(width-220, height-100, 160, 60, 10, fill=1, stroke=0)
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(width-210, height-70, f"Invoice #: {rental.id}")
    p.setFont("Helvetica", 12)
    p.drawString(width-210, height-85, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    # Section line
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.setLineWidth(1)
    p.line(40, height-110, width-40, height-110)
    # Billing info
    y = height - 130
    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "Billed To:")
    p.setFont("Helvetica", 12)
    p.drawString(120, y, f"{rental.user.username}")
    y -= 30
    # Rental details
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Gear")
    p.drawString(170, y, "Brand")
    p.drawString(270, y, "Period")
    p.drawString(410, y, "Days")
    p.drawString(480, y, "Subtotal")
    y -= 22
    p.setFont("Helvetica", 11)
    num_days = (rental.end_date - rental.start_date).days + 1
    subtotal = rental.gear.price * num_days
    p.drawString(50, y, rental.gear.name)
    p.drawString(170, y, rental.gear.brand)
    # Show start date and end date on separate lines
    p.drawString(270, y, f"Start: {rental.start_date}")
    p.drawString(270, y-14, f"End:   {rental.end_date}")
    p.drawString(410, y, str(num_days))
    p.drawString(480, y, f"₹{subtotal}")
    y -= 38
    # Penalty section
    if penalty > 0:
        p.setFont("Helvetica-Bold", 12)
        p.setFillColorRGB(1, 0.2, 0.2)
        p.drawString(50, y, f"Penalty for late return: ₹{penalty}")
        p.setFillColorRGB(0, 0, 0)
        y -= 20
    # Total
    total = subtotal + penalty
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"Total Amount Due: ₹{total}")
    p.showPage()
    p.save()
    return response
