# chat/views.py - Views for Client-Side Encryption
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer, SendMessageSerializer, CreateRoomSerializer
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['GET'])
def chat_rooms(request):
    """Get all chat rooms for the current user"""
    try:
        rooms = ChatRoom.objects.filter(participants=request.user).order_by('-updated_at')
        logger.info(f"User {request.user.username} has {rooms.count()} chat rooms")
        serializer = ChatRoomSerializer(rooms, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error loading chat rooms for {request.user.username}: {e}")
        return Response({'error': 'Failed to load chat rooms'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_or_get_room(request):
    """Create a new chat room or get existing room between two users"""
    serializer = CreateRoomSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    participant_id = serializer.validated_data['participant_id']
    
    try:
        participant = User.objects.get(id=participant_id)
        logger.info(f"Creating/getting room between {request.user.username} and {participant.username}")
        
        # Find existing room between these two users (and only these two users)
        existing_room = ChatRoom.objects.filter(
            participants=request.user
        ).filter(
            participants=participant
        ).annotate(
            participant_count=Count('participants')
        ).filter(
            participant_count=2
        ).first()
        
        if existing_room:
            logger.info(f"Found existing room {existing_room.id} between {request.user.username} and {participant.username}")
            serializer = ChatRoomSerializer(existing_room, context={'request': request})
            return Response(serializer.data)
        
        # Create new room with exactly 2 participants
        room = ChatRoom.objects.create()
        room.participants.add(request.user, participant)
        logger.info(f"Created new room {room.id} between {request.user.username} and {participant.username}")
        
        serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except User.DoesNotExist:
        logger.warning(f"User {participant_id} not found")
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        return Response({'error': 'Failed to create room'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def room_messages(request, room_id):
    """Get all encrypted messages for a room"""
    try:
        # Verify user has access to this room
        room = ChatRoom.objects.get(id=room_id, participants=request.user)
        messages = room.messages.all()
        
        logger.info(f"Room {room_id} has {messages.count()} encrypted messages for {request.user.username}")
        
        # Mark messages as read (except user's own messages)
        unread_count = Message.objects.filter(
            room=room, is_read=False
        ).exclude(sender=request.user).count()
        
        if unread_count > 0:
            Message.objects.filter(
                room=room, is_read=False
            ).exclude(sender=request.user).update(is_read=True)
            logger.info(f"Marked {unread_count} messages as read in room {room_id}")
        
        # Return encrypted messages - client will decrypt them
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        
        # Log encryption info for debugging
        encrypted_messages = [msg for msg in messages if msg.encrypted_content]
        logger.info(f"Serving {len(encrypted_messages)} encrypted messages to client for decryption")
        
        return Response(serializer.data)
        
    except ChatRoom.DoesNotExist:
        logger.warning(f"Room {room_id} not found or access denied for user {request.user.username}")
        return Response({'error': 'Chat room not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting messages for room {room_id}: {e}")
        return Response({'error': 'Failed to load messages'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def send_message(request):
    """Save client-encrypted message to database"""
    serializer = SendMessageSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        logger.warning(f"Invalid message data from {request.user.username}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    room_id = serializer.validated_data['room_id']
    encrypted_content = serializer.validated_data['encrypted_content']
    
    try:
        # Verify user has access to this room
        room = ChatRoom.objects.get(id=room_id, participants=request.user)
        
        # Create message with encrypted content (no server-side encryption/decryption)
        message = Message.objects.create(
            room=room,
            sender=request.user,
            encrypted_content=encrypted_content  # Store client-encrypted content directly
        )
        
        # Log for debugging (don't log full encrypted content)
        content_preview = encrypted_content[:50] + "..." if len(encrypted_content) > 50 else encrypted_content
        logger.info(f"Encrypted message saved to room {room_id} by {request.user.username}: {content_preview}")
        
        # Update room's updated_at timestamp for sorting
        room.save()
        
        # Return the saved message
        response_serializer = MessageSerializer(message, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
    except ChatRoom.DoesNotExist:
        logger.warning(f"Room {room_id} not found or access denied for user {request.user.username}")
        return Response({'error': 'Chat room not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error sending encrypted message to room {room_id}: {e}")
        return Response({'error': 'Failed to send message'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def mark_messages_read(request, room_id):
    """Mark messages as read in a room"""
    try:
        room = ChatRoom.objects.get(id=room_id, participants=request.user)
        
        updated_count = Message.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        logger.info(f"Marked {updated_count} messages as read in room {room_id} for {request.user.username}")
        
        return Response({'marked_read': updated_count})
        
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Chat room not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error marking messages as read in room {room_id}: {e}")
        return Response({'error': 'Failed to mark messages as read'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def room_info(request, room_id):
    """Get detailed information about a chat room"""
    try:
        room = ChatRoom.objects.get(id=room_id, participants=request.user)
        serializer = ChatRoomSerializer(room, context={'request': request})
        
        # Add additional encryption info
        data = serializer.data
        data['encryption_details'] = {
            'client_side': True,
            'algorithm': 'AES-256-GCM',
            'key_derivation': f'room_{room_id}_based',
            'message_count': room.messages.count(),
            'encrypted_storage': True
        }
        
        return Response(data)
        
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Chat room not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting room info for {room_id}: {e}")
        return Response({'error': 'Failed to get room info'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)