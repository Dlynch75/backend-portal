from django.urls import path
from .views import JobPostingListCreateView, JobPostingDetailView, JobSaveView, SchoolView, CountryView

urlpatterns = [
    path('', SchoolView.as_view(), name='job-posting-list-create'),
    path('job', JobPostingListCreateView.as_view(), name='job-posting-list-create'),
    path('job/<int:pk>', JobPostingDetailView.as_view(), name='job-posting-detail'),
    path('job/save', JobSaveView.as_view(), name='job-save'),
    path('job/save/<int:pk>', JobSaveView.as_view(), name='job-save-delete'),
    path('countries', CountryView.as_view(), name='country-list'),

]
