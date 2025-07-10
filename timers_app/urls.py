from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("manage-timer-sets/", views.manage_timer_sets, name="manage_timer_sets"),
    path("share/", views.share_state, name="share_state"),
    path("load/<slug:token>/", views.load_shared_state, name="load_shared_state"),
]
