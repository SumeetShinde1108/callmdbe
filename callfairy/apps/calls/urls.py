"""
URL configuration for calls app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, CallViewSet, BatchCallViewSet, CSVUploadViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'calls', CallViewSet, basename='call')
router.register(r'batches', BatchCallViewSet, basename='batch')
router.register(r'csv-uploads', CSVUploadViewSet, basename='csv-upload')

urlpatterns = [
    path('', include(router.urls)),
]
