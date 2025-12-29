# chat/urls.py - URLs for Client-Side Encryption
from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.chat_rooms, name='chat_rooms'),
    path('rooms/create/', views.create_or_get_room, name='create_room'),
    path('rooms/<int:room_id>/', views.room_info, name='room_info'),
    path('rooms/<int:room_id>/messages/', views.room_messages, name='room_messages'),
    path('rooms/<int:room_id>/mark-read/', views.mark_messages_read, name='mark_messages_read'),
    path('messages/send/', views.send_message, name='send_message'),
]