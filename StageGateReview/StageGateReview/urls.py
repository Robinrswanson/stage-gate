from django.urls import path
from reviewai import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chat, name='chat'),
    path('chat_api/', views.chat_api, name='chat_api'),
]