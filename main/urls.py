from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
    path('', views.name),
    path('partner/', views.find_partner),
    path('keyword/', views.get_two_ready),
    path('score/', views.get_result),
    path('rank/', views.send_rank),
]