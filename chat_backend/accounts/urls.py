from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('search/', views.search_users, name='search_users'),
    path('add-friend/', views.add_friend, name='add_friend'),
    path('friends/', views.friends_list, name='friends_list'),
]