from django.urls import path
from .views import AsyncRegisterView

urlpatterns = [
    path("register/", AsyncRegisterView.as_view()),
]
