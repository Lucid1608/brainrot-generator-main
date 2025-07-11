from flask import Blueprint, request, jsonify, current_app, g
from flask_login import login_required, current_user, login_user, logout_user
from functools import wraps
import os
import re
import secrets
from datetime import datetime
from extensions import db
from models import User, Video, APIKey, UsageLog
from utils import log_usage, get_user_usage_stats, validate_file_upload, get_storage_path
from reddit_shorts.main import run_local_video_generation

api_bp = Blueprint('api', __name__)

def is_valid_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """Password validation"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Check if API key exists and is active
        key_record = APIKey.query.filter_by(key=api_key, is_active=True).first()
        if not key_record:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Update last used timestamp
        key_record.last_used = datetime.utcnow()
        db.session.commit()
        
        # Get user from API key
        user = User.query.get(key_record.user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'User account inactive'}), 401
        
        # Add user to Flask g context
        g.api_user = user
        return f(*args, **kwargs)
    
    return decorated_function

@api_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/videos', methods=['GET'])
@require_api_key
def list_videos():
    """List user's videos"""
    user = g.api_user
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    videos = Video.query.filter_by(user_id=user.id)\
        .order_by(Video.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'videos': [{
            'id': video.id,
            'title': video.title,
            'status': video.status,
            'created_at': video.created_at.isoformat(),
            'completed_at': video.completed_at.isoformat() if video.completed_at else None,
            'duration': video.duration,
            'file_size': video.file_size,
            'download_url': f"/api/v1/videos/{video.id}/download" if video.status == 'completed' else None
        } for video in videos.items],
        'pagination': {
            'page': videos.page,
            'pages': videos.pages,
            'per_page': videos.per_page,
            'total': videos.total,
            'has_next': videos.has_next,
            'has_prev': videos.has_prev
        }
    })

@api_bp.route('/videos/<int:video_id>', methods=['GET'])
@require_api_key
def get_video(video_id):
    """Get video details"""
    user = g.api_user
    
    video = Video.query.filter_by(id=video_id, user_id=user.id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    
    return jsonify({
        'id': video.id,
        'title': video.title,
        'story_content': video.story_content,
        'voice_id': video.voice_id,
        'background_video': video.background_video,
        'background_music': video.background_music,
        'status': video.status,
        'created_at': video.created_at.isoformat(),
        'completed_at': video.completed_at.isoformat() if video.completed_at else None,
        'duration': video.duration,
        'file_size': video.file_size,
        'error_message': video.error_message,
        'download_url': f"/api/v1/videos/{video.id}/download" if video.status == 'completed' else None
    })

@api_bp.route('/videos', methods=['POST'])
@require_api_key
def create_video():
    """Create a new video"""
    user = g.api_user
    
    # Check if user can create video
    if not user.can_create_video():
        return jsonify({'error': 'Monthly video limit reached'}), 403
    
    data = request.get_json()
    
    # Validate input
    title = data.get('title', '').strip()
    story = data.get('story', '').strip()
    voice = data.get('voice', 'en_us_002')
    background_video = data.get('background_video')
    background_music = data.get('background_music')
    filter_profanity = data.get('filter', False)
    
    if not title or not story:
        return jsonify({'error': 'Title and story are required'}), 400
    
    if len(story) > current_app.config['MAX_TEXT_LENGTH']:
        return jsonify({'error': f'Story too long. Maximum {current_app.config["MAX_TEXT_LENGTH"]} characters.'}), 400
    
    # Create video record
    video = Video()
    video.user_id = user.id
    video.title = title
    video.story_content = story
    video.voice_id = voice
    video.background_video = background_video
    video.background_music = background_music
    video.status = 'pending'
    db.session.add(video)
    db.session.commit()
    
    try:
        # Generate video using existing logic
        story_content = f"""Title: {title}
Story:
{story}
"""
        
        # Save story to temporary file
        temp_story_file = f'temp_story_{video.id}.txt'
        with open(temp_story_file, 'w', encoding='utf-8') as f:
            f.write(story_content)
        
        # Set up generation parameters
        params = {
            'filter': filter_profanity,
            'voice': voice,
            'background_video': background_video,
            'background_music': background_music
        }
        
        # Generate video
        video_path = run_local_video_generation(**params)
        
        if video_path and os.path.exists(video_path):
            # Update video record
            video.status = 'completed'
            video.output_path = video_path
            video.completed_at = datetime.utcnow()
            video.file_size = os.path.getsize(video_path)
            
            # Update user usage
            user.videos_created_this_month += 1
            
            db.session.commit()
            
            # Log usage
            log_usage(user.id, 'api_video_created', {
                'video_id': video.id,
                'title': title,
                'file_size': video.file_size
            })
            
            # Clean up temp file
            if os.path.exists(temp_story_file):
                os.remove(temp_story_file)
            
            return jsonify({
                'message': 'Video created successfully',
                'video': {
                    'id': video.id,
                    'title': video.title,
                    'status': video.status,
                    'created_at': video.created_at.isoformat(),
                    'completed_at': video.completed_at.isoformat(),
                    'file_size': video.file_size,
                    'download_url': f"/api/v1/videos/{video.id}/download"
                }
            }), 201
        else:
            video.status = 'failed'
            video.error_message = 'Video generation failed'
            db.session.commit()
            
            return jsonify({'error': 'Video generation failed'}), 500
            
    except Exception as e:
        video.status = 'failed'
        video.error_message = str(e)
        db.session.commit()
        
        current_app.logger.error(f"API video generation error: {e}")
        return jsonify({'error': 'Video generation failed'}), 500

@api_bp.route('/usage', methods=['GET'])
@require_api_key
def get_usage():
    """Get user usage statistics"""
    user = g.api_user
    
    usage_stats = get_user_usage_stats(user.id)
    plan_limits = user.get_plan_limits()
    
    return jsonify({
        'usage': usage_stats,
        'plan': {
            'name': user.subscription_plan,
            'limits': plan_limits
        }
    })

@api_bp.route('/auth/register', methods=['POST'])
def register():
    print('DEBUG: /api/auth/register endpoint was called')
    data = request.get_json()
    
    # Validate input
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    
    # Validation
    if not email or not username or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    is_valid, password_error = is_valid_password(password)
    if not is_valid:
        return jsonify({'error': password_error}), 400
    
    if len(username) < 3 or len(username) > 20:
        return jsonify({'error': 'Username must be between 3 and 20 characters'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    # Create user
    user = User()
    user.email = email
    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'Registration successful! You can now log in.',
        'user_id': user.id
    }), 201

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    remember = data.get('remember', False)
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 401
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    login_user(user, remember=remember)
    
    # Log usage
    log_usage(user.id, 'login', {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent')
    })
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
    }), 200

@api_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """User logout endpoint"""
    log_usage(current_user.id, 'logout', {
        'ip_address': request.remote_addr
    })
    
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

@api_bp.route('/auth/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'username': current_user.username,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'is_verified': current_user.is_verified,
            'subscription_plan': current_user.subscription_plan
        }
    }), 200

@api_bp.route('/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get user statistics for dashboard"""
    try:
        # Get usage stats
        usage_stats = get_user_usage_stats(current_user.id)
        
        # Get plan limits
        plan_limits = current_user.get_plan_limits()
        
        # Count total videos
        total_videos = Video.query.filter_by(user_id=current_user.id).count()
        
        # Count videos this month
        from datetime import datetime, timedelta
        first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        videos_this_month = Video.query.filter(
            Video.user_id == current_user.id,
            Video.created_at >= first_day_of_month
        ).count()
        
        return jsonify({
            'totalVideos': total_videos,
            'videosThisMonth': videos_this_month,
            'planUsed': current_user.videos_created_this_month,
            'planLimit': plan_limits.get('videos_per_month', 3),
            'planName': current_user.subscription_plan
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user stats: {e}")
        return jsonify({'error': 'Failed to get user stats'}), 500

@api_bp.route('/videos/dashboard', methods=['GET'])
@login_required
def get_user_videos_dashboard():
    """Get user's videos for dashboard (session auth)"""
    limit = request.args.get('limit', 5, type=int)
    
    videos = Video.query.filter_by(user_id=current_user.id)\
        .order_by(Video.created_at.desc())\
        .limit(limit)\
        .all()
    
    return jsonify({
        'videos': [{
            'id': video.id,
            'title': video.title,
            'status': video.status,
            'created_at': video.created_at.isoformat(),
            'completed_at': video.completed_at.isoformat() if video.completed_at else None,
            'duration': video.duration,
            'file_size': video.file_size,
            'download_url': f"/api/videos/{video.id}/download" if video.status == 'completed' else None
        } for video in videos]
    }) 