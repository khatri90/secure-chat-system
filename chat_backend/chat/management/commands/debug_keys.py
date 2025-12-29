# Create: accounts/management/commands/debug_keys.py

from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Debug user encryption keys'
    
    def handle(self, *args, **options):
        self.stdout.write("=== User Keys Debug ===")
        
        users = CustomUser.objects.all()
        self.stdout.write(f"Total users: {users.count()}")
        
        for user in users:
            self.stdout.write(f"\n👤 User: {user.username} (ID: {user.id})")
            self.stdout.write(f"   Email: {user.email}")
            self.stdout.write(f"   Created: {user.date_joined}")
            
            # Check if keys exist
            has_public = bool(user.public_key_pem)
            has_private = bool(user.private_key_encrypted) 
            has_symmetric = bool(user.symmetric_key)
            
            self.stdout.write(f"   Has Public Key: {has_public}")
            self.stdout.write(f"   Has Private Key: {has_private}")
            self.stdout.write(f"   Has Symmetric Key: {has_symmetric}")
            
            if has_public:
                # Show first and last parts of key to check uniqueness
                key_start = user.public_key_pem[:100] if user.public_key_pem else "None"
                key_end = user.public_key_pem[-100:] if user.public_key_pem else "None"
                self.stdout.write(f"   Key Start: {key_start}")
                self.stdout.write(f"   Key End: {key_end}")
                
                # Check if it's a fallback key
                if "1234567890ABCDEF" in user.public_key_pem:
                    self.stdout.write("   ⚠️  This looks like a fallback key!")
                elif "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A" in user.public_key_pem:
                    self.stdout.write("   ✅ This looks like a real RSA key")
                else:
                    self.stdout.write("   ❓ Unknown key format")
        
        # Check for duplicate keys
        self.stdout.write("\n=== Checking for Duplicate Keys ===")
        
        public_keys = {}
        for user in users:
            if user.public_key_pem:
                key_hash = user.public_key_pem[:200]  # Compare first 200 chars
                if key_hash in public_keys:
                    self.stdout.write(f"🔴 DUPLICATE KEY FOUND!")
                    self.stdout.write(f"   Users: {public_keys[key_hash]} and {user.username}")
                else:
                    public_keys[key_hash] = user.username
        
        if len(public_keys) == users.count():
            self.stdout.write("✅ All users have unique keys")
        else:
            self.stdout.write(f"❌ Found {users.count() - len(public_keys)} duplicate keys")
        
        self.stdout.write("\n✅ Debug complete")