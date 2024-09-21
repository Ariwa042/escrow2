from django import template
from core.models import Trade  # Adjust based on your model location

register = template.Library()

@register.filter
def status_is_pending(trades):
    return trades.filter(status='PENDING')

@register.filter
def status_is_completed(trades):
    return trades.filter(status='COMPLETED')
