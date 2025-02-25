from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('edit_chat/<int:chat_id>/', views.chat_management, name='edit_chat'),
    path('chat/<int:chat_id>/', views.chat, name='chat'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
]