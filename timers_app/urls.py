from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("manage-timer-sets/", views.manage_timer_sets, name="manage_timer_sets"),
]
