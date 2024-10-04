from django.urls import path
from .views import HireListCreateView, HireDetailView

urlpatterns = [
    path('job/hire', HireListCreateView.as_view(), name='hire-list-create'),
    path('job/hire/<int:hire_id>', HireDetailView.as_view(), name='hire-detail'),
]
