# chat/models.py - Simplified for Client-Side Encryption
from django.db import models
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class ChatRoom(models.Model):
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Room {self.id}"
    
    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    encrypted_content = models.TextField()  # Store client-encrypted content directly
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Encrypted message from {self.sender.username} at {self.timestamp}"
    
    def get_content_preview(self):
        """Get a preview of encrypted content for admin/debugging"""
        if self.encrypted_content:
            preview = self.encrypted_content[:50]
            return f"{preview}... (AES-encrypted, {len(self.encrypted_content)} chars)"
        return "No content"