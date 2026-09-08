import pytest
from app import create_app
from app.extensions import db
from app.models import User, Category, Product

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SHIPPING_FEE = 200
    SUPABASE_URL = ''
    SUPABASE_KEY = ''
    SUPABASE_SERVICE_ROLE_KEY = ''
    UPLOAD_EXTENSIONS = {'jpg','jpeg','png','webp'}

@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        category = Category(name='Games', slug='games')
        product = Product(name='Test Puzzle', slug='test-puzzle', description='Puzzle', price=1000, sku='PUZ-001', stock=5, low_stock_threshold=2, category=category, active=True, featured=True)
        user = User(name='Test Customer', email='customer@example.com', phone='03001234567')
        user.set_password('Password123')
        admin = User(name='Admin', email='admin@example.com', role='admin')
        admin.set_password('AdminPass123')
        db.session.add_all([category, product, user, admin])
        db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def csrf_token(client):
    with client.get('/login') as response:
        # Extract token from rendered form without BeautifulSoup.
        import re
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))
        return match.group(1)


def login(client, email='customer@example.com', password='Password123', token=None):
    if token is None:
        token = csrf_token(client)
    return client.post('/login', data={'email': email, 'password': password, 'csrf_token': token}, follow_redirects=True)
