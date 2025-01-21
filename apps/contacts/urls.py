from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet

router = DefaultRouter()
router.register('contacts', ContactViewSet, basename='contacts')

urlpatterns = router.urls