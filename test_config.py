import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing environment variable loading:")
print(f"MAX_TEXT_LENGTH from os.getenv: {os.getenv('MAX_TEXT_LENGTH', 'NOT FOUND')}")
print(f"MAX_TEXT_LENGTH from os.getenv with default: {os.getenv('MAX_TEXT_LENGTH', '5000')}")

# Test the Config class
from config import Config
print(f"MAX_TEXT_LENGTH from Config class: {Config.MAX_TEXT_LENGTH}")

# Test creating the app
from app import create_app
app = create_app()
print(f"MAX_TEXT_LENGTH from app config: {app.config.get('MAX_TEXT_LENGTH', 'NOT SET')}") 