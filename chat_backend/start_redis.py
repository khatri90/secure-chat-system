import subprocess
import sys
import time

def start_redis():
    try:
        # Try to start Redis server
        print("Starting Redis server...")
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        print("✅ Redis server started successfully!")
        return True
    except FileNotFoundError:
        print("❌ Redis not found. Please install Redis:")
        print("Windows: Download from https://github.com/microsoftarchive/redis/releases")
        print("Mac: brew install redis")
        print("Linux: sudo apt-get install redis-server")
        return False

if __name__ == "__main__":
    start_redis()