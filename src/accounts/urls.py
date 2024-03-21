from django.urls import path, include
from rest_framework import routers
from .views import ProfileViewSet, UserSearchViewset, HistoryViewSet, StatsViewSet

router = routers.DefaultRouter()
router.register("profiles", ProfileViewSet, basename="profiles")
router.register("search", UserSearchViewset, basename="search")
router.register("history", HistoryViewSet, basename="history")
router.register("stats", StatsViewSet, basename="stats")

urlpatterns = [
    path("", include(router.urls), name="profiles"),
]
