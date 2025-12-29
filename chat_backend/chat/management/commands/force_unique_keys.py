# Create: accounts/management/commands/force_unique_keys.py

from django.core.management.base import BaseCommand
from accounts.models import CustomUser
import base64
import time
import random
import hashlib

class Command(BaseCommand):
    help = 'Force generate truly unique keys for all users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Fix keys for specific user (by username)',
        )
    
    def handle(self, *args, **options):
        if options['user']:
            try:
                user = CustomUser.objects.get(username=options['user'])
                self.force_unique_keys(user)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Generated unique keys for: {user.username}")
                )
            except CustomUser.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ User '{options['user']}' not found")
                )
        else:
            # Fix all users
            users = CustomUser.objects.all()
            self.stdout.write(f"Generating unique keys for {users.count()} users...")
            
            for user in users:
                self.force_unique_keys(user)
                self.stdout.write(f"✅ {user.username}: New unique key generated")
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ All {users.count()} users now have unique keys!")
            )
    
    def force_unique_keys(self, user):
        """Generate truly unique keys for a user"""
        
        # Create unique seed for this user
        unique_seed = f"{user.username}_{user.id}_{int(time.time() * 1000)}_{random.randint(10000, 99999)}"
        hash_seed = hashlib.sha256(unique_seed.encode()).hexdigest()
        
        self.stdout.write(f"  Generating keys for {user.username} with seed: {hash_seed[:16]}...")
        
        # Try to generate real RSA keys first
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Serialize public key for display
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            # Serialize private key 
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            user.public_key_pem = public_pem
            user.private_key_encrypted = base64.urlsafe_b64encode(private_pem.encode()).decode()
            
            self.stdout.write(f"    ✅ Real RSA keys generated")
            
        except Exception as e:
            self.stdout.write(f"    ⚠️  RSA generation failed: {e}")
            
            # Fallback: Create unique demo keys using the hash
            user.public_key_pem = f"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA{hash_seed[:64]}
{hash_seed[64:128]}{user.username.ljust(32, 'X')[:32]}YZabcdefghijklmnopqrstuvwxyz
1234567890ABCDEFGHIJ{hash_seed[128:160]}opqrstuvwxyz1234567890ABCDEF
GHIJKLMNOPQRSTUVWXYZ{hash_seed[160:192]}fghijklmnopqrstuvwxyz12345678
90ABCDEFGHIJKLMNOPQRSTUVWXYZ{hash_seed[192:224]}qrstuvwxyz123456789
0ABCDEFGHIJKLMNOPQRSTUVWXYZ{hash_seed[224:256]}TUVWXYZ{user.id:06d}
-----END PUBLIC KEY-----"""
            
            user.private_key_encrypted = base64.urlsafe_b64encode(f"private_key_{hash_seed}_{user.username}".encode()).decode()
            
            self.stdout.write(f"    ✅ Unique demo keys generated")
        
        # Always generate new symmetric key
        from cryptography.fernet import Fernet
        try:
            symmetric_key = Fernet.generate_key()
            user.symmetric_key = base64.urlsafe_b64encode(symmetric_key).decode()
            self.stdout.write(f"    ✅ Symmetric key generated")
        except Exception as e:
            self.stdout.write(f"    ⚠️  Fernet failed, using hash: {e}")
            # Fallback: use hash-based key
            symmetric_key = hash_seed[:32].encode().ljust(32, b'0')[:32]
            user.symmetric_key = base64.urlsafe_b64encode(symmetric_key).decode()
        
        # Save the user (bypass the save() method to avoid recursion)
        CustomUser.objects.filter(id=user.id).update(
            public_key_pem=user.public_key_pem,
            private_key_encrypted=user.private_key_encrypted,
            symmetric_key=user.symmetric_key
        )
        
        # Refresh from database
        user.refresh_from_db()
        
        # Show preview
        key_preview = user.public_key_pem[:100] if user.public_key_pem else "None"
        self.stdout.write(f"    Key preview: {key_preview}...")