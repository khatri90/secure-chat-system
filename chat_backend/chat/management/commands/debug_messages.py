# Create: chat/management/commands/debug_messages.py

from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from chat.models import ChatRoom, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug message loading and persistence'
    
    def handle(self, *args, **options):
        self.stdout.write("=== SecureChat Message Debug ===")
        
        # Show all users and their keys
        users = CustomUser.objects.all()
        self.stdout.write(f"Total users: {users.count()}")
        
        for user in users:
            key_preview = user.public_key_pem[:50] if user.public_key_pem else "No key"
            self.stdout.write(f"  - {user.username}: {key_preview}...")
        
        # Show all chat rooms and messages
        rooms = ChatRoom.objects.all()
        self.stdout.write(f"\nTotal chat rooms: {rooms.count()}")
        
        for room in rooms:
            participants = [p.username for p in room.participants.all()]
            messages = room.messages.all()
            
            self.stdout.write(f"\nRoom {room.id}: {', '.join(participants)}")
            self.stdout.write(f"  Messages: {messages.count()}")
            
            for msg in messages:
                decrypted = msg.decrypt_message()
                sender = msg.sender.username
                timestamp = msg.timestamp.strftime("%H:%M:%S")
                self.stdout.write(f"    [{timestamp}] {sender}: {decrypted}")
        
        # Test message API endpoint simulation
        self.stdout.write("\n=== API Endpoint Test ===")
        
        if rooms.exists():
            test_room = rooms.first()
            test_messages = test_room.messages.all()
            
            self.stdout.write(f"Room {test_room.id} API would return:")
            for msg in test_messages:
                api_data = {
                    'id': msg.id,
                    'sender': {
                        'id': msg.sender.id,
                        'username': msg.sender.username
                    },
                    'decrypted_content': msg.decrypt_message(),
                    'timestamp': msg.timestamp.isoformat(),
                    'is_read': msg.is_read
                }
                self.stdout.write(f"  {api_data}")
        
        self.stdout.write("\n✅ Debug complete")