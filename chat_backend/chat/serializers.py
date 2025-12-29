# chat/serializers.py - Serializers for Client-Side Encryption
from rest_framework import serializers
from .models import ChatRoom, Message
from accounts.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ('id', 'sender', 'encrypted_content', 'timestamp', 'is_read')
        read_only_fields = ('id', 'sender', 'timestamp')
    
    def to_representation(self, instance):
        """
        Return the encrypted content directly - client will decrypt it
        """
        data = super().to_representation(instance)
        # Log for debugging (don't log full encrypted content for security)
        if instance.encrypted_content:
            content_preview = instance.encrypted_content[:50] + "..." if len(instance.encrypted_content) > 50 else instance.encrypted_content
            print(f"API serving encrypted message {instance.id}: {content_preview}")
        return data

class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    encryption_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ('id', 'participants', 'last_message', 'unread_count', 'encryption_info', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_last_message(self, obj):
        """Get the last message (encrypted) for the room"""
        last_message = obj.messages.last()
        if last_message:
            return {
                'id': last_message.id,
                'encrypted_content': last_message.encrypted_content,
                'timestamp': last_message.timestamp,
                'sender_username': last_message.sender.username,
                # Don't include decrypted content - client handles decryption
                'decrypted_content': '[Client will decrypt]'  # Placeholder for client
            }
        return None
    
    def get_unread_count(self, obj):
        """Get count of unread messages for the current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
    
    def get_encryption_info(self, obj):
        """Return encryption info for client"""
        return {
            'type': 'client_side_aes',
            'algorithm': 'AES-256-GCM',
            'key_derivation': 'room_based',
            'room_id': obj.id,
            'secure': True,
            'note': 'Messages encrypted in browser before transmission'
        }

class SendMessageSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    encrypted_content = serializers.CharField(max_length=10000)  # Allow larger encrypted content
    
    def validate_room_id(self, value):
        """Validate that the room exists and user has access"""
        try:
            room = ChatRoom.objects.get(id=value)
            if not room.participants.filter(id=self.context['request'].user.id).exists():
                raise serializers.ValidationError("You are not a participant in this chat room")
            return value
        except ChatRoom.DoesNotExist:
            raise serializers.ValidationError("Chat room does not exist")
    
    def validate_encrypted_content(self, value):
        """Basic validation of encrypted content"""
        if not value or not value.strip():
            raise serializers.ValidationError("Encrypted content cannot be empty")
        
        # Basic check that it looks like base64 (our encryption output format)
        import re
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', value.strip()):
            raise serializers.ValidationError("Invalid encrypted content format")
        
        return value.strip()

class CreateRoomSerializer(serializers.Serializer):
    participant_id = serializers.IntegerField()
    
    def validate_participant_id(self, value):
        """Validate that the participant exists and is not the current user"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            participant = User.objects.get(id=value)
            if participant == self.context['request'].user:
                raise serializers.ValidationError("Cannot create room with yourself")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")