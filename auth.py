from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
import os
import secrets
import re
from datetime import datetime, timedelta
from extensions import db
from models import User, EmailVerification, PasswordReset, UserSession, UsageLog
from utils import send_email, log_usage

auth_bp = Blueprint('auth', __name__)

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

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    print('DEBUG: /auth/register endpoint was called')
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
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
        
        # Send verification email
        send_verification_email(user)
        
        return jsonify({
            'message': 'Registration successful! Please check your email to verify your account.',
            'user_id': user.id
        }), 201
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
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
        
        # Create session
        session = UserSession(
            user_id=user.id,
            session_id=secrets.token_urlsafe(32),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(session)
        db.session.commit()
        
        login_user(user, remember=remember)
        
        # Log usage
        log_usage(user.id, 'login', {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        })
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        
        return jsonify({
            'message': 'Login successful',
            'redirect': next_page
        }), 200
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # Log usage
    log_usage(current_user.id, 'logout', {
        'ip_address': request.remote_addr
    })
    
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    verification = EmailVerification.query.filter_by(
        token=token, 
        is_used=False
    ).first()
    
    if not verification:
        flash('Invalid or expired verification link', 'error')
        return redirect(url_for('auth.login'))
    
    if verification.expires_at < datetime.utcnow():
        flash('Verification link has expired', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(verification.user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))
    
    user.is_verified = True
    verification.is_used = True
    
    db.session.commit()
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Email not found'}), 404
    
    if user.is_verified:
        return jsonify({'error': 'Email is already verified'}), 400
    
    send_verification_email(user)
    
    return jsonify({'message': 'Verification email sent'}), 200

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        if user:
            send_password_reset_email(user)
        
        # Always return success to prevent email enumeration
        return jsonify({'message': 'If an account with that email exists, a password reset link has been sent'}), 200
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    reset_request = PasswordReset.query.filter_by(
        token=token, 
        is_used=False
    ).first()
    
    if not reset_request:
        flash('Invalid or expired reset link', 'error')
        return redirect(url_for('auth.login'))
    
    if reset_request.expires_at < datetime.utcnow():
        flash('Reset link has expired', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password', '')
        
        is_valid, password_error = is_valid_password(password)
        if not is_valid:
            return jsonify({'error': password_error}), 400
        
        user = User.query.get(reset_request.user_id)
        user.set_password(password)
        reset_request.is_used = True
        
        db.session.commit()
        
        flash('Password has been reset successfully', 'success')
        return jsonify({'message': 'Password reset successful'}), 200
    
    return render_template('auth/reset_password.html')

def send_verification_email(user):
    """Send email verification link"""
    token = secrets.token_urlsafe(32)
    
    verification = EmailVerification(
        user_id=user.id,
        token=token
    )
    db.session.add(verification)
    db.session.commit()
    
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    
    send_email(
        subject='Verify Your Email',
        recipients=[user.email],
        template='emails/verify_email.html',
        user=user,
        verification_url=verification_url
    )

def send_password_reset_email(user):
    """Send password reset email"""
    token = secrets.token_urlsafe(32)
    
    reset_request = PasswordReset(
        user_id=user.id,
        token=token
    )
    db.session.add(reset_request)
    db.session.commit()
    
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    send_email(
        subject='Reset Your Password',
        recipients=[user.email],
        template='emails/reset_password.html',
        user=user,
        reset_url=reset_url
    ) 