import uuid
from django.db import models
from core.models import CustomUser, Package, Teacher, School


class Invoice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT)  # Prevent cascade delete
    invoice_id = models.CharField(max_length=255)  
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount charged
    currency = models.CharField(max_length=10)  # Currency code (e.g., USD)
    status = models.CharField(max_length=50)  # e.g., 'paid', 'pending', 'canceled', etc.
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the invoice was created
    payment_date = models.DateTimeField(null=True, blank=True)  # Date of payment if successful
    canceled_at = models.DateTimeField(null=True, blank=True)  
    pdf_url = models.URLField(max_length=1024, null=True, blank=True)  # Store the invoice PDF URL
    package_type = models.ForeignKey(Package, on_delete=models.PROTECT, default=None,  null=True) 

    def __str__(self):
        return f"Invoice {self.invoice_id} for {self.user.email} - Status: {self.status}"


class CVUpgradeOrder(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Pending payment'),
        ('paid', 'Paid'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    teacher = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='cv_upgrade_orders'
    )
    created_by_school = models.ForeignKey(
        School, on_delete=models.SET_NULL, null=True, blank=True, related_name='cv_upgrade_links_created'
    )
    candidate_name = models.CharField(max_length=200, blank=True, default='')
    candidate_email = models.EmailField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=19.99)
    currency = models.CharField(max_length=10, default='USD')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"CV Upgrade {self.id} – {self.candidate_email} ({self.status})"
