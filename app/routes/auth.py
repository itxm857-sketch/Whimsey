import re
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from ..extensions import db
from ..models import User


auth_bp = Blueprint('auth', __name__)
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
PHONE_RE = re.compile(r'^\+?[0-9\s().-]{7,20}$')


def safe_next_url(target):
    if target and target.startswith('/') and not target.startswith('//'):
        return target
    return url_for('shop.home')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('shop.home'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        errors = []
        if not name:
            errors.append('Name is required.')
        if not EMAIL_RE.match(email):
            errors.append('Enter a valid email address.')
        if phone and not PHONE_RE.match(phone):
            errors.append('Enter a valid phone number.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if User.query.filter(func.lower(User.email) == email).first():
            errors.append('Unable to create the account with those details. If you already have an account, please log in.')
        if errors:
            for e in errors: flash(e, 'error')
            return render_template('register.html')
        user = User(name=name, email=email, phone=phone or None)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        flash('Welcome to Whimsy! Your account has been created.', 'success')
        return redirect(url_for('shop.home'))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('shop.home'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter(func.lower(User.email) == email).first()
        if not email or not password or not user or not user.check_password(password) or not user.is_active:
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
        login_user(user, remember=True)
        flash('Welcome back!', 'success')
        return redirect(safe_next_url(request.args.get('next')))
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('shop.home'))


@auth_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        if not name:
            flash('Name is required.', 'error')
        elif phone and not PHONE_RE.match(phone):
            flash('Enter a valid phone number.', 'error')
        else:
            current_user.name = name
            current_user.phone = phone or None
            db.session.commit()
            flash('Profile updated.', 'success')
    return render_template('profile.html')


@auth_bp.route('/account/password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
    elif len(new_password) < 8:
        flash('New password must be at least 8 characters.', 'error')
    elif new_password != confirm:
        flash('New passwords do not match.', 'error')
    else:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully.', 'success')
    return redirect(url_for('auth.account'))
