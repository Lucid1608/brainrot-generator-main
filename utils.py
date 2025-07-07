import os
import json
from datetime import datetime
from flask import current_app, render_template
from flask_mail import Message
from models import db, UsageLog

# Initialize Redis (optional)
redis_client = None  # Disabled due to async client issues

# Initialize Stripe (optional)
try:
    import stripe
    from config import Config
    stripe.api_key = Config.STRIPE_SECRET_KEY
except ImportError:
    stripe = None

def send_email(subject, recipients, template, **kwargs):
    """Send email using Flask-Mail"""
    try:
        from app import mail
        
        msg = Message(
            subject=subject,
            recipients=recipients,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Render HTML template
        msg.html = render_template(template, **kwargs)
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        return False

def log_usage(user_id, action, details=None):
    """Log user actions for analytics"""
    try:
        usage_log = UsageLog()
        usage_log.user_id = user_id
        usage_log.action = action
        usage_log.details = details or {}
        if details:
            usage_log.ip_address = details.get('ip_address')
            usage_log.user_agent = details.get('user_agent')
        db.session.add(usage_log)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to log usage: {e}")

def get_user_usage_stats(user_id):
    """Get user usage statistics"""
    try:
        # Get monthly video count
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        videos_this_month = UsageLog.query.filter(
            UsageLog.user_id == user_id,
            UsageLog.action == 'video_created',
            UsageLog.created_at >= current_month
        ).count()
        
        # Get total videos
        total_videos = UsageLog.query.filter(
            UsageLog.user_id == user_id,
            UsageLog.action == 'video_created'
        ).count()
        
        # Get last activity
        last_activity = UsageLog.query.filter(
            UsageLog.user_id == user_id
        ).order_by(UsageLog.created_at.desc()).first()
        
        return {
            'videos_this_month': videos_this_month,
            'total_videos': total_videos,
            'last_activity': last_activity.created_at if last_activity else None
        }
    except Exception as e:
        current_app.logger.error(f"Failed to get usage stats: {e}")
        return {}

def cache_set(key, value, expire=3600):
    """Set cache value"""
    if not redis_client:
        return False
    try:
        redis_client.setex(key, expire, json.dumps(value))
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to set cache: {e}")
        return False

def cache_get(key):
    """Get cache value"""
    if not redis_client:
        return None
    try:
        value = redis_client.get(key)
        if value is not None:
            # Handle both string and bytes responses
            if isinstance(value, bytes):
                return json.loads(value.decode('utf-8'))
            return json.loads(value)
        return None
    except Exception as e:
        current_app.logger.error(f"Failed to get cache: {e}")
        return None

def cache_delete(key):
    """Delete cache value"""
    if not redis_client:
        return False
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to delete cache: {e}")
        return False

def create_stripe_customer(user):
    """Create Stripe customer"""
    if not stripe:
        return None
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}".strip(),
            metadata={
                'user_id': user.id,
                'username': user.username
            }
        )
        
        user.stripe_customer_id = customer.id
        db.session.commit()
        
        return customer
    except Exception as e:
        current_app.logger.error(f"Failed to create Stripe customer: {e}")
        return None

def create_stripe_subscription(user, price_id):
    """Create Stripe subscription"""
    if not stripe:
        return None
    try:
        if not user.stripe_customer_id:
            create_stripe_customer(user)
        
        subscription = stripe.Subscription.create(
            customer=user.stripe_customer_id,
            items=[{'price': price_id}],
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent'],
        )
        
        return subscription
    except Exception as e:
        current_app.logger.error(f"Failed to create subscription: {e}")
        return None

def cancel_stripe_subscription(subscription_id):
    """Cancel Stripe subscription"""
    if not stripe:
        return None
    try:
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        return subscription
    except Exception as e:
        current_app.logger.error(f"Failed to cancel subscription: {e}")
        return None

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except Exception:
        return 0

def format_duration(seconds):
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def validate_file_upload(file, allowed_extensions):
    """Validate file upload"""
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size (100MB limit)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 100 * 1024 * 1024:  # 100MB
        return False, "File too large. Maximum size is 100MB"
    
    return True, "File is valid"

def generate_thumbnail(video_path, output_path, time_offset=5):
    """Generate thumbnail from video"""
    try:
        import ffmpeg
        
        # Extract frame at specified time
        (
            ffmpeg
            .input(video_path, ss=time_offset)
            .filter('scale', 320, -1)
            .output(output_path, vframes=1)
            .overwrite_output()
            .run(quiet=True)
        )
        
        return True
    except ImportError:
        current_app.logger.warning("ffmpeg-python not installed, thumbnail generation disabled")
        return False
    except Exception as e:
        current_app.logger.error(f"Failed to generate thumbnail: {e}")
        return False

def get_video_duration(video_path):
    """Get video duration using ffmpeg"""
    try:
        import ffmpeg
        
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        duration = float(video_info['duration'])
        
        return duration
    except ImportError:
        current_app.logger.warning("ffmpeg-python not installed, duration detection disabled")
        return 0
    except Exception as e:
        current_app.logger.error(f"Failed to get video duration: {e}")
        return 0

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:100-len(ext)] + ext
    
    return filename

def get_storage_path(user_id, filename, file_type):
    """Get storage path for user files"""
    # Create user directory structure
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id), file_type)
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    
    return os.path.join(user_dir, unique_filename)

def cleanup_old_files(directory, max_age_days=7):
    """Clean up old files"""
    try:
        cutoff_time = datetime.utcnow().timestamp() - (max_age_days * 24 * 3600)
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    current_app.logger.info(f"Cleaned up old file: {file_path}")
    except Exception as e:
        current_app.logger.error(f"Failed to cleanup old files: {e}")

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}" 