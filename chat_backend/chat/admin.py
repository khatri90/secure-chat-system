# chat/admin.py - Admin for Client-Side Encryption
from django.contrib import admin
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_participants', 'message_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    filter_horizontal = ['participants']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants.short_description = 'Participants'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'room', 'get_content_preview', 'timestamp', 'is_read']
    list_filter = ['timestamp', 'is_read', 'room']
    search_fields = ['sender__username', 'sender__email']
    readonly_fields = ['timestamp', 'get_content_preview', 'get_encryption_info']
    
    def get_content_preview(self, obj):
        """Show a preview of encrypted content"""
        if obj.encrypted_content:
            preview = obj.encrypted_content[:100]
            return f"{preview}... ({len(obj.encrypted_content)} chars total)"
        return "No content"
    get_content_preview.short_description = 'Encrypted Content Preview'
    
    def get_encryption_info(self, obj):
        """Show encryption information"""
        if obj.encrypted_content:
            return {
                'length': len(obj.encrypted_content),
                'type': 'AES-256-GCM (Client-side)',
                'room_id': obj.room.id,
                'note': 'Content encrypted in browser before storage'
            }
        return "No encryption data"
    get_encryption_info.short_description = 'Encryption Info'
    
    fieldsets = (
        ('Message Info', {
            'fields': ('room', 'sender', 'timestamp', 'is_read')
        }),
        ('Encrypted Content', {
            'fields': ('encrypted_content', 'get_content_preview', 'get_encryption_info'),
            'description': 'Content is encrypted client-side using AES-256-GCM'
        }),
    )