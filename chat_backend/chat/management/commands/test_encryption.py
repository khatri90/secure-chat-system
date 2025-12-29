# Create: chat/management/__init__.py (empty file)
# Create: chat/management/commands/__init__.py (empty file)
# Create: chat/management/commands/test_encryption.py

from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from chat.models import ChatRoom, Message

class Command(BaseCommand):
    help = 'Test SecureChat encryption and message persistence'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test data after testing',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("=== Testing SecureChat Message System ===")
        
        try:
            # Get or create test users
            user1, created1 = CustomUser.objects.get_or_create(
                email='test1@example.com',
                defaults={'username': 'test1'}
            )
            if created1:
                user1.set_password('testpass123')
                user1.save()
                self.stdout.write(f"Created user: {user1.username}")
            
            user2, created2 = CustomUser.objects.get_or_create(
                email='test2@example.com', 
                defaults={'username': 'test2'}
            )
            if created2:
                user2.set_password('testpass123')
                user2.save()
                self.stdout.write(f"Created user: {user2.username}")

            # Check keys
            self.stdout.write(f"User1: {user1.username} - Has Key: {bool(user1.public_key_pem)}")
            self.stdout.write(f"User2: {user2.username} - Has Key: {bool(user2.public_key_pem)}")
            
            # Show key preview (avoid Unicode issues)
            if user1.public_key_pem:
                key_preview = user1.public_key_pem[:100].replace('\n', '\\n')
                self.stdout.write(f"User1 Key Preview: {key_preview}...")

            # Create chat room
            room = ChatRoom.objects.create()
            room.participants.add(user1, user2)
            self.stdout.write(f"Created room {room.id}")

            # Test message encryption/decryption
            test_message = "Hello, this is a test message!"
            self.stdout.write(f"Testing message: '{test_message}'")
            
            message = Message.objects.create(room=room, sender=user1)
            message.encrypt_message(test_message)
            message.save()

            self.stdout.write(f"Encrypted: {message.encrypted_content[:50]}...")
            
            decrypted = message.decrypt_message()
            self.stdout.write(f"Decrypted: '{decrypted}'")

            # Test persistence
            saved_message = Message.objects.get(id=message.id)
            saved_decrypted = saved_message.decrypt_message()
            self.stdout.write(f"From DB: '{saved_decrypted}'")

            # Test with simple special chars (avoid emojis that cause issues)
            special_message = "Test with accents: café, naïve, résumé"
            message2 = Message.objects.create(room=room, sender=user2)
            message2.encrypt_message(special_message)
            message2.save()
            
            self.stdout.write(f"Special chars test: '{message2.decrypt_message()}'")

            # Show all messages in room
            all_messages = room.messages.all()
            self.stdout.write(f"Room has {all_messages.count()} messages:")
            
            for msg in all_messages:
                sender_name = msg.sender.username
                content = msg.decrypt_message()
                self.stdout.write(f"  - {sender_name}: '{content}'")

            # Test result
            success = (decrypted == test_message) and (saved_decrypted == test_message)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS("✅ All tests PASSED! Messages are working correctly.")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Test FAILED - check encryption/decryption logic")
                )
            
            # Cleanup if requested
            if options['cleanup']:
                self.stdout.write("Cleaning up test data...")
                Message.objects.filter(room=room).delete()
                room.delete()
                if created1:
                    user1.delete()
                if created2:
                    user2.delete()
                self.stdout.write("Test data cleaned up.")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Test failed with error: {str(e)}")
            )
            import traceback
            self.stdout.write(traceback.format_exc())