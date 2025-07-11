from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app, send_file, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from extensions import db
from models import User, Video, BackgroundAsset, UsageLog
from utils import log_usage, get_user_usage_stats, validate_file_upload, get_storage_path, format_file_size, generate_thumbnail
from reddit_shorts.main import run_local_video_generation
from reddit_shorts.tiktok_voice.src.voice import Voice
from reddit_shorts.config import footage, music

main_bp = Blueprint('main', __name__)

# Voice name mapping
VOICE_NAME_MAP = {
    'en_male_jomboy': 'Game On',
    'en_us_002': 'Jessie',
    'es_mx_002': 'Warm',
    'en_male_funny': 'Wacky',
    'en_us_ghostface': 'Scream',
    'en_female_samc': 'Empathetic',
    'en_male_cody': 'Serious',
    'en_female_makeup': 'Beauty Guru',
    'en_female_richgirl': 'Bestie',
    'en_male_grinch': 'Trickster',
    'en_us_006': 'Joey',
    'en_male_narration': 'Story Teller',
    'en_male_deadpool': 'Mr. GoodGuy',
    'en_uk_001': 'Narrator',
    'en_uk_003': 'Male English UK',
    'en_au_001': 'Metro',
    'en_male_jarvis': 'Alfred',
    'en_male_ashmagic': 'ashmagic',
    'en_male_olantekkers': 'olantekkers',
    'en_male_ukneighbor': 'Lord Cringe',
    'en_male_ukbutler': 'Mr. Meticulous',
    'en_female_shenna': 'Debutante',
    'en_female_pansino': 'Varsity',
    'en_male_trevor': 'Marty',
    'en_female_f08_twinkle': 'Pop Lullaby',
    'en_male_m03_classical': 'Classic Electric',
    'en_female_betty': 'Bae',
    'en_male_cupid': 'Cupid',
    'en_female_grandma': 'Granny',
    'en_male_m2_xhxs_m03_christmas': 'Cozy',
    'en_male_santa_narration': 'Author',
    'en_male_sing_deep_jingle': 'Caroler',
    'en_male_santa_effect': 'Santa',
    'en_female_ht_f08_newyear': 'NYE 2023',
    'en_male_wizard': 'Magician',
    'en_female_ht_f08_halloween': 'Opera',
    'en_female_ht_f08_glorious': 'Euphoric',
    'en_male_sing_funny_it_goes_up': 'Hypetrain',
    'en_female_ht_f08_wonderful_world': 'Melodrama',
    'en_male_m2_xhxs_m03_silly': 'Quirky Time',
    'en_female_emotional': 'Peaceful',
    'en_male_m03_sunshine_soon': 'Toon Beat',
    'en_female_f08_warmy_breeze': 'Open Mic',
    'en_male_sing_funny_thanksgiving': 'Thanksgiving',
    'en_female_f08_salut_damour': 'Cottagecore',
    'en_us_007': 'Professor',
    'en_us_009': 'Scientist',
    'en_us_010': 'Confidence',
    'en_au_002': 'Smooth',
    'fr_001': 'French - Male 1'
}

@main_bp.route('/')
def index():
    """Serve React app"""
    return send_from_directory('frontend/build', 'index.html')

@main_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files from React build"""
    import os
    static_dir = os.path.join(os.getcwd(), 'frontend', 'build', 'static')
    return send_from_directory(static_dir, filename)

@main_bp.route('/<path:path>')
def serve_react(path):
    """Serve React app for all other routes"""
    return send_from_directory('frontend/build', 'index.html')

@main_bp.route('/api/voices')
@login_required
def get_voices():
    return jsonify([
        {
            "voice_id": "emily",
            "name": "Emily",
            "description": "Default voice"
        }
    ])

@main_bp.route('/api/backgrounds')
@login_required
def get_backgrounds():
    """Get available background videos"""
    backgrounds = []
    
    # Get from database first
    db_backgrounds = BackgroundAsset.query.filter_by(
        asset_type='video',
        is_active=True
    ).all()
    
    for bg in db_backgrounds:
        # Check if premium content is available for user
        if bg.is_premium and current_user.subscription_plan == 'free':
            continue
            
        backgrounds.append({
            'id': bg.id,
            'name': bg.name,
            'path': bg.file_path,
            'thumbnail': bg.thumbnail_path,
            'is_premium': bg.is_premium
        })
    
    # Fallback to config backgrounds
    if not backgrounds and footage:
        for video_path in footage:
            base_name = os.path.basename(video_path)
            video_name = os.path.splitext(base_name)[0]
            backgrounds.append({
                'id': base_name,
                'name': video_name,
                'path': video_path,
                'thumbnail': f"/static/thumbnails/{video_name}.jpg",
                'is_premium': False
            })
    
    return jsonify(backgrounds)

@main_bp.route('/api/music')
@login_required
def get_music():
    """Get available music tracks"""
    tracks = []
    
    # Get from database first
    db_tracks = BackgroundAsset.query.filter_by(
        asset_type='music',
        is_active=True
    ).all()
    
    for track in db_tracks:
        # Check if premium content is available for user
        if track.is_premium and current_user.subscription_plan == 'free':
            continue
            
        tracks.append({
            'id': track.id,
            'name': track.name,
            'path': track.file_path,
            'type': track.category or 'general',
            'is_premium': track.is_premium
        })
    
    # Fallback to config music
    if not tracks and music:
        for music_file_path, volume, music_type in music:
            base_name = os.path.basename(music_file_path)
            track_name = os.path.splitext(base_name)[0]
            tracks.append({
                'id': base_name,
                'name': track_name,
                'path': music_file_path,
                'type': music_type,
                'is_premium': False
            })
    
    return jsonify(tracks)

@main_bp.route('/api/generate', methods=['POST'])
@login_required
def generate_video():
    """Generate video"""
    # Check if user can create video
    if not current_user.can_create_video():
        return jsonify({'error': 'Monthly video limit reached. Please upgrade your plan.'}), 403
    
    data = request.get_json()
    
    # Validate input
    title = data.get('title', '').strip()
    story = data.get('story', '').strip()
    voice = data.get('voice')
    background_video = data.get('background_video')
    background_music = data.get('background_music')
    filter_profanity = data.get('filter', False)
    
    if not title or not story:
        return jsonify({'error': 'Title and story are required'}), 400
    
    if len(story) > current_app.config.get('MAX_TEXT_LENGTH', 5000):
        return jsonify({'error': f'Story too long. Maximum {current_app.config.get("MAX_TEXT_LENGTH", 5000)} characters.'}), 400
    
    # Create video record
    video = Video()
    video.user_id = current_user.id
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
            'voice': voice or 'en_us_002',
            'background_video': background_video,
            'background_music': background_music,
            'title': title,
            'story': story
        }
        
        # Generate video
        import asyncio
        video_path = asyncio.run(run_local_video_generation(**params))
        
        if video_path and os.path.exists(video_path):
            # Update video record
            video.status = 'completed'
            video.output_path = video_path
            video.completed_at = datetime.utcnow()
            video.file_size = os.path.getsize(video_path)
            
            # Get video duration
            try:
                import ffmpeg
                probe = ffmpeg.probe(video_path)
                video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
                video.duration = float(video_info['duration'])
            except:
                video.duration = 0
            
            # Update user usage
            current_user.videos_created_this_month += 1
            
            db.session.commit()
            
            # Log usage
            log_usage(current_user.id, 'video_created', {
                'video_id': video.id,
                'title': title,
                'duration': video.duration,
                'file_size': video.file_size
            })
            
            # Clean up temp file
            if os.path.exists(temp_story_file):
                os.remove(temp_story_file)
            
            return jsonify({
                'message': 'Video generated successfully',
                'video_id': video.id,
                'download_url': url_for('main.download_video', video_id=video.id)
            }), 200
        else:
            video.status = 'failed'
            video.error_message = 'Video generation failed'
            db.session.commit()
            
            return jsonify({'error': 'Video generation failed'}), 500
            
    except Exception as e:
        video.status = 'failed'
        video.error_message = str(e)
        db.session.commit()
        
        current_app.logger.error(f"Video generation error: {e}")
        return jsonify({'error': 'Video generation failed'}), 500

@main_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload custom background/music files"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    file_type = request.form.get('type', 'video')  # video, music, image
    
    # Validate file
    is_valid, error_message = validate_file_upload(file, current_app.config['ALLOWED_EXTENSIONS'])
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
    # Save file
    if not file.filename:
        return jsonify({'error': 'No filename provided'}), 400
    filename = secure_filename(file.filename)
    file_path = get_storage_path(current_user.id, filename, file_type)
    file.save(file_path)
    
    # Create asset record
    asset = BackgroundAsset()
    asset.name = os.path.splitext(filename)[0]
    asset.file_path = file_path
    asset.asset_type = file_type
    asset.file_size = os.path.getsize(file_path)
    asset.is_premium = False  # User uploads are not premium
    
    # Generate thumbnail for videos
    if file_type == 'video':
        thumbnail_path = file_path.rsplit('.', 1)[0] + '_thumb.jpg'
        if generate_thumbnail(file_path, thumbnail_path):
            asset.thumbnail_path = thumbnail_path
    
    db.session.add(asset)
    db.session.commit()
    
    return jsonify({
        'message': 'File uploaded successfully',
        'asset_id': asset.id,
        'file_path': file_path
    }), 200 