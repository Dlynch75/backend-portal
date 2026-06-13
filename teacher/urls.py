from django.urls import path
from .views import HireListCreateView, HireDetailView, JobAlertListCreateView, JobAlertDetailView, RecommendedJobsView

urlpatterns = [
    path('job/hire', HireListCreateView.as_view(), name='hire-list-create'),
    path('job/hire/<int:hire_id>', HireDetailView.as_view(), name='hire-detail'),
    path('job/recommended', RecommendedJobsView.as_view(), name='job-recommended'),
    path('job/alerts', JobAlertListCreateView.as_view(), name='job-alerts'),
    path('job/alerts/<int:alert_id>', JobAlertDetailView.as_view(), name='job-alert-detail'),
]
