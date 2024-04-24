from django.urls import path
from pepejeans_scraper import views

urlpatterns = [
    path('', views.index, name='index'),
]
