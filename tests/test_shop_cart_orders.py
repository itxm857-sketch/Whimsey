from .conftest import login
from app.extensions import db
from app.models import Product, Order

def test_add_to_cart_and_quantity_limits(client):
    login(client)
    token = __import__('re').search(r'name="csrf_token" value="([^"]+)"', client.get('/shop').get_data(as_text=True)).group(1)
    r = client.post('/cart/add/1', data={'quantity':4,'csrf_token':token}, follow_redirects=True)
    assert b'Test Puzzle' in r.data
    r = client.post('/cart/add/1', data={'quantity':4,'csrf_token':token}, follow_redirects=True)
    assert b'Only 5 unit' in r.data

def test_checkout_deducts_stock_and_creates_order(client, app):
    login(client)
    token = __import__('re').search(r'name="csrf_token" value="([^"]+)"', client.get('/shop').get_data(as_text=True)).group(1)
    client.post('/cart/add/1', data={'quantity':2,'csrf_token':token})
    r = client.post('/checkout', data={'csrf_token':token,'customer_name':'Test Customer','phone':'03001234567','email':'customer@example.com','address':'123 Street','city':'Lahore','postal_code':'54000','notes':''}, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        assert Product.query.get(1).stock == 3
        order = Order.query.one()
        assert order.stock_deducted is True
        assert order.items[0].quantity == 2

def test_customer_only_sees_own_order(client, app):
    login(client)
    token = __import__('re').search(r'name="csrf_token" value="([^"]+)"', client.get('/shop').get_data(as_text=True)).group(1)
    client.post('/cart/add/1', data={'quantity':1,'csrf_token':token})
    client.post('/checkout', data={'csrf_token':token,'customer_name':'Test Customer','phone':'03001234567','email':'customer@example.com','address':'123','city':'Lahore'}, follow_redirects=True)
    r = client.get('/orders')
    assert b'WHM-' in r.data
