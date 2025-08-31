from django.urls import path

from .views import CarDataAPIView

urlpatterns = [
    path('car-data/', CarDataAPIView.as_view(), name='car-data')
]
