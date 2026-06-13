from django.urls import path

from . import views
from .views import CreatePaymentSessionView, CreateFeaturedJobPaymentView
from .cv_upgrade_views import (
    CVUpgradeCheckoutAuthenticatedView,
    CVUpgradeCheckoutView,
    CVUpgradeCreateLinkView,
    CVUpgradePublicView,
    CVUpgradeStatusView,
)

urlpatterns = [
    path('session/<int:pk>', CreatePaymentSessionView.as_view(), name='create-payment-session'),
    path('featured-job/<int:job_id>', CreateFeaturedJobPaymentView.as_view(), name='create-featured-job-payment'),
    path('cv-upgrade', CVUpgradeCreateLinkView.as_view(), name='cv-upgrade-create'),
    path('cv-upgrade/status', CVUpgradeStatusView.as_view(), name='cv-upgrade-status'),
    path('cv-upgrade/session', CVUpgradeCheckoutAuthenticatedView.as_view(), name='cv-upgrade-checkout-auth'),
    path('cv-upgrade/<uuid:token>', CVUpgradePublicView.as_view(), name='cv-upgrade-public'),
    path('cv-upgrade/<uuid:token>/session', CVUpgradeCheckoutView.as_view(), name='cv-upgrade-checkout'),
    path('webhook/', views.stripe_webhook, name='stripe-webhook'),
]
