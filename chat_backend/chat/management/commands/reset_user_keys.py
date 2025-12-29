# Create: accounts/management/__init__.py (empty file)
# Create: accounts/management/commands/__init__.py (empty file)  
# Create: accounts/management/commands/reset_user_keys.py

from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Reset all user encryption keys to generate unique keys for each user'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Reset keys for specific user (by username)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Reset keys for all users',
        )
    
    def handle(self, *args, **options):
        if options['user']:
            # Reset keys for specific user
            try:
                user = CustomUser.objects.get(username=options['user'])
                self.reset_user_keys(user)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Reset keys for user: {user.username}")
                )
            except CustomUser.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ User '{options['user']}' not found")
                )
                
        elif options['all']:
            # Reset keys for all users
            users = CustomUser.objects.all()
            self.stdout.write(f"Resetting keys for {users.count()} users...")
            
            for user in users:
                self.reset_user_keys(user)
                self.stdout.write(f"✅ Reset keys for: {user.username}")
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully reset keys for all {users.count()} users")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Please specify --user <username> or --all")
            )
            return
    
    def reset_user_keys(self, user):
        """Reset encryption keys for a single user"""
        # Clear existing keys to force regeneration
        user.public_key_pem = None
        user.private_key_encrypted = None
        user.symmetric_key = None
        
        # Save will trigger key generation with unique values
        user.save()
        
        # Verify keys were generated
        if user.public_key_pem and user.private_key_encrypted and user.symmetric_key:
            self.stdout.write(f"  - Generated new keys for {user.username}")
            self.stdout.write(f"  - Public key preview: {user.public_key_pem[:50]}...")
        else:
            self.stdout.write(
                self.style.WARNING(f"  - Warning: Key generation may have failed for {user.username}")
            )