from django.urls import path, include
from rest_framework import routers
from .views import ProfileViewSet, UserSearchViewset

router = routers.DefaultRouter()
router.register("profiles", ProfileViewSet, basename="profiles")
router.register("search", UserSearchViewset, basename="search")

urlpatterns = [
    path("", include(router.urls), name="profiles"),
]
