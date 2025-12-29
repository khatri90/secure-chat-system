# chat/consumers.py - WebSocket Consumer for Client-Side Encryption
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            logger.warning(f"Anonymous user attempted to connect to room {self.room_id}")
            await self.close()
            return

        # Check if user is participant in the room
        is_participant = await self.check_room_participation()
        if not is_participant:
            logger.warning(f"User {self.user.username} attempted to access unauthorized room {self.room_id}")
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.user.username} connected to room {self.room_id}")

        # Set user as online
        await self.set_user_online_status(True)

        # Notify others that user came online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_online': True
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Set user as offline
            await self.set_user_online_status(False)

            # Notify others that user went offline
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status_update',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_online': False
                }
            )

            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            logger.info(f"User {self.user.username} disconnected from room {self.room_id}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'chat_message')

            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)
            elif message_type == 'read_message':
                await self.handle_read_message(text_data_json)

        except json.JSONDecodeError:
            logger.error("Invalid JSON received in WebSocket")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def handle_chat_message(self, data):
        encrypted_content = data.get('content', '').strip()
        if not encrypted_content:
            logger.warning(f"Empty message received from {self.user.username}")
            return

        # Validate encrypted content (basic checks)
        if len(encrypted_content) > 10000:  # Reasonable limit for encrypted content
            logger.warning(f"Encrypted message too long from {self.user.username}: {len(encrypted_content)} chars")
            return

        # Save ENCRYPTED message to database (no server-side decryption)
        message = await self.save_encrypted_message(encrypted_content)
        if not message:
            logger.error(f"Failed to save encrypted message from {self.user.username}")
            return

        logger.info(f"Encrypted message saved: Room {self.room_id}, User {self.user.username}, Length {len(encrypted_content)}")

        # Send ENCRYPTED content to all room participants via WebSocket
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message.id,
                'content': encrypted_content,  # ← ENCRYPTED CONTENT in WebSocket packet!
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'timestamp': message.timestamp.isoformat(),
            }
        )

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        # Send typing indicator to room group (except sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing,
                'sender_channel': self.channel_name,  # To exclude sender
            }
        )

    async def handle_read_message(self, data):
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_as_read(message_id)

    # WebSocket message handlers
    async def chat_message(self, event):
        """Send encrypted message to WebSocket client"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'content': event['content'],  # ← This is encrypted content
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
        }))

    async def typing_indicator(self, event):
        # Don't send typing indicator back to sender
        if event.get('sender_channel') != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    async def user_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_online': event['is_online'],
        }))

    # Database operations
    @database_sync_to_async
    def check_room_participation(self):
        """Check if user is participant in the room"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.participants.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_encrypted_message(self, encrypted_content):
        """Save client-encrypted message directly to database"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            message = Message.objects.create(
                room=room,
                sender=self.user,
                encrypted_content=encrypted_content  # Store encrypted content as-is
            )
            
            # Update room timestamp for sorting
            room.save()
            return message
        except Exception as e:
            logger.error(f"Error saving encrypted message: {e}")
            return None

    @database_sync_to_async
    def set_user_online_status(self, is_online):
        """Update user online status"""
        try:
            self.user.is_online = is_online
            self.user.save(update_fields=['is_online'])
        except Exception as e:
            logger.error(f"Error updating user status: {e}")

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Mark message as read"""
        try:
            Message.objects.filter(
                id=message_id,
                room_id=self.room_id
            ).exclude(sender=self.user).update(is_read=True)
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")


class UserStatusConsumer(AsyncWebsocketConsumer):
    """Consumer for global user status updates"""
    
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return

        self.user_group_name = f'user_{self.user.id}'
        
        # Join user's personal group for notifications
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.username} connected to status updates")

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.username} disconnected from status updates")

    async def receive(self, text_data):
        # Handle global status updates if needed
        pass

    async def notification(self, event):
        """Send notification to user"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'data': event.get('data', {})
        }))