import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # File upload configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', 5000))  # 5000 characters
    
    # Redis configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Stripe configuration
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    
    # Subscription plans
    SUBSCRIPTION_PLANS = {
        'free': {
            'name': 'Free',
            'price': 0,
            'videos_per_month': 3,
            'max_text_length': 1000,
            'api_calls_per_month': 0,
            'features': ['Basic voices', 'Standard backgrounds', '720p quality']
        },
        'pro': {
            'name': 'Pro',
            'price': 9.99,
            'videos_per_month': 50,
            'max_text_length': 3000,
            'api_calls_per_month': 1000,
            'features': ['All voices', 'Premium backgrounds', '1080p quality', 'API access']
        },
        'business': {
            'name': 'Business',
            'price': 29.99,
            'videos_per_month': 500,
            'max_text_length': 5000,
            'api_calls_per_month': 10000,
            'features': ['All voices', 'All backgrounds', '4K quality', 'Priority support', 'Custom branding']
        }
    } 