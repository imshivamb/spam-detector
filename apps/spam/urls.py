from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SpamViewSet

router = DefaultRouter()
router.register('spam', SpamViewSet, basename='spam')

urlpatterns = router.urls