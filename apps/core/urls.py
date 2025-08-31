from django.urls import path

from .views import (
    GetYearsAPIView,
    GetMakesAPIView,
    GetModelsAPIView,
    GetSubmodelsAPIView,
    GetTrimsAPIView,
    GetBodiesAPIView,
    GetEnginesAPIView,
    VINDecodeAPIView,

)

urlpatterns = [
    # CarAPI.app endpoints
    path('carapi/years/', GetYearsAPIView.as_view(), name='carapi-years'),
    path('carapi/makes/', GetMakesAPIView.as_view(), name='carapi-makes'),
    path('carapi/models/', GetModelsAPIView.as_view(), name='carapi-models'),
    path('carapi/submodels/', GetSubmodelsAPIView.as_view(), name='carapi-submodels'),
    path('carapi/trims/', GetTrimsAPIView.as_view(), name='carapi-trims'),
    path('carapi/bodies/', GetBodiesAPIView.as_view(), name='carapi-bodies'),
    path('carapi/engines/', GetEnginesAPIView.as_view(), name='carapi-engines'),
    path('carapi/vin/<str:vin>/', VINDecodeAPIView.as_view(), name='carapi-vin'),

]
