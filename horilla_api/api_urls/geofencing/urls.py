from django.urls import path
from ...api_views.geofencing import views

urlpatterns = [
    path("geofencings/", views.GeoFencingAPIView.as_view(), name="api-geofencing-list"),
    path("geofencings/<int:pk>/", views.GeoFencingAPIView.as_view(), name="api-geofencing-detail"),
]

