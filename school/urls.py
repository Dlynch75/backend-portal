from django.urls import path
from .views import JobPostingListCreateView, JobPostingDetailView

urlpatterns = [
    path('job', JobPostingListCreateView.as_view(), name='job-posting-list-create'),
    path('job/<int:pk>', JobPostingDetailView.as_view(), name='job-posting-detail'),

]
