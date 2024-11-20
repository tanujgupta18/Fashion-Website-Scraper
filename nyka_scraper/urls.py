from django.urls import path
from nyka_scraper import views

urlpatterns = [
    path('', views.index, name='index'),
]
