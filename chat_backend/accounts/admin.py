from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Friendship

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_online', 'created_at']
    list_filter = ['is_online', 'is_staff', 'created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_online',)}),
    )

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['user', 'friend', 'created_at']
    list_filter = ['created_at']