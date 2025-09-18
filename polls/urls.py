from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import PollViewSet

router = DefaultRouter()
router.register(r'polls', PollViewSet, basename='poll')

urlpatterns = [
    path('', include(router.urls)),
]
