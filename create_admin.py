import getpass
from app import create_app
from app.extensions import db
from app.models import User
from config import Config

app = create_app(Config)

with app.app_context():
    print('Create Whimsy administrator')
    name = input('Admin name: ').strip()
    email = input('Admin email: ').strip().lower()
    password = getpass.getpass('Admin password (8+ chars): ')
    confirm = getpass.getpass('Confirm password: ')
    if not name or '@' not in email or len(password) < 8 or password != confirm:
        raise SystemExit('Invalid input. Name, valid email and matching 8+ character password are required.')
    existing = User.query.filter_by(email=email).first()
    if existing:
        if existing.role == 'admin':
            raise SystemExit('An admin with that email already exists.')
        raise SystemExit('A customer already uses that email. Use another admin email.')
    user = User(name=name, email=email, role='admin', is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print('Admin created successfully.')
