# cleanup_users.py - Run with: python manage.py shell < cleanup_users.py

from accounts.models import CustomUser
from chat.models import ChatRoom, Message

def cleanup_test_data():
    print("=== Cleaning up test data ===")
    
    # Delete test users and their data
    test_users = CustomUser.objects.filter(email__in=['test1@example.com', 'test2@example.com'])
    count = test_users.count()
    
    if count > 0:
        # Delete their messages first
        Message.objects.filter(sender__in=test_users).delete()
        
        # Delete their chat rooms
        for user in test_users:
            user.chat_rooms.all().delete()
        
        # Delete the users
        test_users.delete()
        
        print(f"Deleted {count} test users and their data")
    else:
        print("No test users found")
    
    # Also clean up users with broken keys (optional)
    broken_users = CustomUser.objects.filter(public_key_pem__contains="[Key generation error]")
    broken_count = broken_users.count()
    
    if broken_count > 0:
        print(f"Found {broken_count} users with broken keys")
        
        # Fix their keys instead of deleting them
        for user in broken_users:
            user.public_key_pem = None
            user.private_key_encrypted = None
            user.symmetric_key = None
            user.save()  # This will trigger key regeneration
            print(f"Fixed keys for user: {user.username}")
    
    print("✅ Cleanup completed")

# Run cleanup
cleanup_test_data()