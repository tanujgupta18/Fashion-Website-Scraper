from django.urls import path
from tatacliq_scraper import views

urlpatterns = [
    path('', views.index, name='index'),
    path('scrape/', views.scrape_and_store, name='scrape_and_store'),
]
