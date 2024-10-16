from django.db import models
from core.models import CustomUser  # Adjust import based on your structure

class Invoice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT)  # Prevent cascade delete
    invoice_id = models.CharField(max_length=255, unique=True)  # Unique ID from Stripe
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount charged
    currency = models.CharField(max_length=10)  # Currency code (e.g., USD)
    status = models.CharField(max_length=50)  # e.g., 'paid', 'pending', 'canceled', etc.
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the invoice was created
    payment_date = models.DateTimeField(null=True, blank=True)  # Date of payment if successful
    canceled_at = models.DateTimeField(null=True, blank=True)  

    def __str__(self):
        return f"Invoice {self.invoice_id} for {self.user.email} - Status: {self.status}"
