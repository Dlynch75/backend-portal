from django.urls import path

from stats.views import CardView, GraphView

urlpatterns = [
    path('cards', CardView.as_view(), name='stats-cards'),
    path('graphs', GraphView.as_view(), name='graphs-cards'),
   
]
