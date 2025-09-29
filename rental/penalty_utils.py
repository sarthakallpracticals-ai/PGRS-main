from datetime import date
from decimal import Decimal

def calculate_penalty(rental):
    today = date.today()
    num_days = (rental.end_date - rental.start_date).days + 1
    subtotal = rental.gear.price * num_days
    penalty = Decimal('0.00')
    if today > rental.end_date:
        days_late = (today - rental.end_date).days
        daily_penalty = Decimal('0.10') * subtotal
        penalty = daily_penalty * days_late
    return penalty
