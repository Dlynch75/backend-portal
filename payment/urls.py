from django.urls import path

from . import views
from .views import CreatePaymentSessionView

urlpatterns = [
    path('session/<int:pk>', CreatePaymentSessionView.as_view(), name='create-payment-session'),
    path('webhook/', views.stripe_webhook, name='stripe-webhook'),
]
