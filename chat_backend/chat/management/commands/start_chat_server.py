from django.core.management.base import BaseCommand
from django.core.management import execute_from_command_line
import subprocess
import sys
import time

class Command(BaseCommand):
    help = 'Start the chat server with Redis and Django'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting Secure Chat Server...")
        
        # Start Redis
        try:
            subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL)
            time.sleep(2)
            self.stdout.write(self.style.SUCCESS("✅ Redis server started"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("❌ Redis not found. Please install Redis first."))
            return

        # Start Django server
        self.stdout.write("🔄 Starting Django server with WebSocket support...")
        execute_from_command_line(['manage.py', 'runserver'])