import re
from flask import Blueprint, flash, redirect, render_template, request, url_for
from ..extensions import db
from ..models import Message

messages_bp = Blueprint('messages', __name__)


@messages_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if not name or not subject or not message or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            flash('Please complete all required fields with a valid email.', 'error')
            return render_template('contact.html')
        db.session.add(Message(name=name, email=email, phone=phone or None, subject=subject, message=message))
        db.session.commit()
        flash('Thanks! Your message has been sent to Whimsy.', 'success')
        return redirect(url_for('messages.contact'))
    return render_template('contact.html')
