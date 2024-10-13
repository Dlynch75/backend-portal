from django.urls import path

from stats.views import CardView

urlpatterns = [
    path('cards', CardView.as_view(), name='stats-cards'),
   
]
