# Create a file: test_messages.py in your project root
# Run with: python manage.py shell < test_messages.py

from accounts.models import CustomUser
from chat.models import ChatRoom, Message

print("=== Testing SecureChat Message System ===")

# Get or create test users
user1, created1 = CustomUser.objects.get_or_create(
    email='test1@example.com',
    defaults={'username': 'test1'}
)
if created1:
    user1.set_password('testpass123')
    user1.save()
    
user2, created2 = CustomUser.objects.get_or_create(
    email='test2@example.com', 
    defaults={'username': 'test2'}
)
if created2:
    user2.set_password('testpass123')
    user2.save()

print(f"User1: {user1.username} - Has Key: {bool(user1.public_key_pem)}")
print(f"User2: {user2.username} - Has Key: {bool(user2.public_key_pem)}")

# Show first 100 chars of public key
if user1.public_key_pem:
    print(f"User1 Key Preview: {user1.public_key_pem[:100]}...")

# Create or get chat room
room = ChatRoom.objects.create()
room.participants.add(user1, user2)
print(f"Created room {room.id}")

# Test simple message
test_message = "Hello, this is a test message!"
print(f"Original message: '{test_message}'")

message = Message.objects.create(room=room, sender=user1)
message.encrypt_message(test_message)
message.save()

print(f"Encrypted content: {message.encrypted_content[:50]}...")

decrypted = message.decrypt_message()
print(f"Decrypted message: '{decrypted}'")

# Test if message persists in database
saved_message = Message.objects.get(id=message.id)
saved_decrypted = saved_message.decrypt_message()
print(f"From database: '{saved_decrypted}'")

# Check room messages
all_messages = room.messages.all()
print(f"Room has {all_messages.count()} messages total")

for msg in all_messages:
    print(f"- {msg.sender.username}: '{msg.decrypt_message()}'")

success = (decrypted == test_message) and (saved_decrypted == test_message)
print(f"Test Result: {'PASSED' if success else 'FAILED'}")

if success:
    print("✅ All tests passed! Messages are working correctly.")
else:
    print("❌ Test failed - check encryption/decryption logic")
    
print("=== Test Complete ===")