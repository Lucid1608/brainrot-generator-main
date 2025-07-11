from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Subscription related fields
    subscription_plan = db.Column(db.String(20), default='free')
    subscription_status = db.Column(db.String(20), default='active')
    stripe_customer_id = db.Column(db.String(255))
    subscription_end_date = db.Column(db.DateTime)
    
    # Usage tracking
    videos_created_this_month = db.Column(db.Integer, default=0)
    last_usage_reset = db.Column(db.Date, default=datetime.utcnow().date)
    
    # Relationships
    videos = db.relationship('Video', backref='user', lazy=True)
    api_keys = db.relationship('APIKey', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_create_video(self):
        """Check if user can create a video based on their plan"""
        if self.subscription_plan == 'free':
            return self.videos_created_this_month < 3
        elif self.subscription_plan == 'pro':
            return self.videos_created_this_month < 50
        elif self.subscription_plan == 'business':
            return self.videos_created_this_month < 500
        return False
    
    def get_plan_limits(self):
        """Get current plan limits"""
        from config import Config
        return Config.SUBSCRIPTION_PLANS.get(self.subscription_plan, {})
    
    def reset_monthly_usage(self):
        """Reset monthly usage counter"""
        current_date = datetime.utcnow().date()
        if self.last_usage_reset.month != current_date.month or self.last_usage_reset.year != current_date.year:
            self.videos_created_this_month = 0
            self.last_usage_reset = current_date
            db.session.commit()

class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    story_content = db.Column(db.Text, nullable=False)
    voice_id = db.Column(db.String(50))
    background_video = db.Column(db.String(255))
    background_music = db.Column(db.String(255))
    output_path = db.Column(db.String(500))
    duration = db.Column(db.Float)
    file_size = db.Column(db.Integer)  # in bytes
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    # Video metadata
    resolution = db.Column(db.String(20), default='720p')
    format = db.Column(db.String(10), default='mp4')
    
    def __repr__(self):
        return f'<Video {self.title}>'

class APIKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super(APIKey, self).__init__(**kwargs)
        if not self.key:
            self.key = self.generate_key()
    
    @staticmethod
    def generate_key():
        return str(uuid.uuid4()).replace('-', '')

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), unique=True)
    plan = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='active')
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_payment_intent_id = db.Column(db.String(255), unique=True)
    amount = db.Column(db.Integer)  # Amount in cents
    currency = db.Column(db.String(3), default='usd')
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def __init__(self, **kwargs):
        super(UserSession, self).__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=7)

class BackgroundAsset(db.Model):
    __tablename__ = 'background_assets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    asset_type = db.Column(db.String(20), nullable=False)  # video, music, image
    category = db.Column(db.String(50))
    is_premium = db.Column(db.Boolean, default=False)
    duration = db.Column(db.Float)  # for videos and music
    file_size = db.Column(db.Integer)  # in bytes
    thumbnail_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class UsageLog(db.Model):
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # video_created, api_call, etc.
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(EmailVerification, self).__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(PasswordReset, self).__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=1) 