import re
import secrets
from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import abort, current_app, flash, redirect, request, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename


def slugify(value):
    value = re.sub(r'[^\w\s-]', '', value.lower()).strip()
    return re.sub(r'[-\s]+', '-', value)


def unique_slug(model, value, current_id=None):
    base = slugify(value) or secrets.token_hex(4)
    slug = base
    counter = 2
    query = model.query.filter_by(slug=slug)
    if current_id:
        query = query.filter(model.id != current_id)
    while query.first():
        slug = f'{base}-{counter}'
        counter += 1
        query = model.query.filter_by(slug=slug)
        if current_id:
            query = query.filter(model.id != current_id)
    return slug


def unique_order_number():
    return 'WHM-' + secrets.token_hex(5).upper()


def parse_money(value):
    try:
        amount = Decimal(str(value)).quantize(Decimal('0.01'))
        if amount < 0:
            raise InvalidOperation
        return amount
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Enter a valid non-negative price.')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['UPLOAD_EXTENSIONS']


def safe_filename(filename):
    return secure_filename(filename)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.path))
        if not current_user.is_active or current_user.role != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def flash_errors(errors):
    for error in errors:
        flash(error, 'error')
