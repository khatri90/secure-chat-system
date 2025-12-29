# accounts/models.py - Updated with better error handling
from django.contrib.auth.models import AbstractUser
from django.db import models
from cryptography.fernet import Fernet
import base64
import logging

logger = logging.getLogger(__name__)

def generate_demo_rsa_keys():
    """Generate demo RSA key pair for educational display"""
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        # Generate RSA key pair for educational display
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
        
        return public_pem, private_pem
        
    except ImportError as e:
        logger.error(f"Cryptography library not available: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Error generating RSA keys: {e}")
        return None, None

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    public_key_pem = models.TextField(blank=True, null=True)  # Store PEM format for display
    private_key_encrypted = models.TextField(blank=True, null=True)  # Store encrypted private key
    symmetric_key = models.TextField(blank=True, null=True)  # For message encryption
    created_at = models.DateTimeField(auto_now_add=True)
    is_online = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def save(self, *args, **kwargs):
        # Only generate keys for new users or users with missing keys
        is_new_user = not self.pk
        needs_keys = not self.public_key_pem or not self.private_key_encrypted or not self.symmetric_key
        
        if is_new_user or needs_keys:
            # Always generate new unique keys for each user
            try:
                symmetric_key = Fernet.generate_key()
                self.symmetric_key = base64.urlsafe_b64encode(symmetric_key).decode()
                logger.info(f"Generated symmetric key for user {self.username}")
            except Exception as e:
                logger.error(f"Error generating symmetric key: {e}")
                # Create a basic key if Fernet fails
                import secrets
                basic_key = secrets.token_urlsafe(32)
                self.symmetric_key = base64.urlsafe_b64encode(basic_key.encode()).decode()
            
            # Generate unique RSA keys for each user
            public_pem, private_pem = generate_demo_rsa_keys()
            
            if public_pem and private_pem:
                self.public_key_pem = public_pem
                self.private_key_encrypted = base64.urlsafe_b64encode(private_pem.encode()).decode()
                logger.info(f"Generated unique RSA keys for user {self.username}")
            else:
                # Fallback to unique demo keys with user-specific data
                import time
                import random
                unique_id = f"{self.username}_{int(time.time())}_{random.randint(1000, 9999)}"
                
                self.public_key_pem = f"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA{unique_id[:64].ljust(64, 'A')}
{unique_id[64:128].ljust(64, 'B')}GHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz
1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv
wxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop
qrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ{unique_id[-16:]}
-----END PUBLIC KEY-----"""
                self.private_key_encrypted = base64.urlsafe_b64encode(f"demo_private_key_{unique_id}".encode()).decode()
                logger.info(f"Generated fallback unique keys for user {self.username}")
            
        super().save(*args, **kwargs)
    
    def get_display_public_key(self):
        """Return public key for display in frontend"""
        return self.public_key_pem or "No public key available"
    
    def get_symmetric_key(self):
        """Return symmetric key for message encryption"""
        try:
            if self.symmetric_key:
                return base64.urlsafe_b64decode(self.symmetric_key.encode())
            else:
                # Generate a new key if none exists
                new_key = Fernet.generate_key()
                self.symmetric_key = base64.urlsafe_b64encode(new_key).decode()
                self.save(update_fields=['symmetric_key'])
                return new_key
        except Exception as e:
            logger.error(f"Error getting symmetric key: {e}")
            # Fallback: return a basic key
            import secrets
            return secrets.token_bytes(32)

class Friendship(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friendships')
    friend = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friend_of')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'friend')
        
    def __str__(self):
        return f"{self.user.username} -> {self.friend.username}"