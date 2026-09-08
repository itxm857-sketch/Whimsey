from .conftest import login

def test_customer_cannot_access_admin(client):
    login(client)
    r = client.get('/admin')
    assert r.status_code == 403

def test_admin_can_access_dashboard(client, csrf_token):
    login(client, 'admin@example.com', 'AdminPass123', csrf_token)
    r = client.get('/admin')
    assert r.status_code == 200
    assert b'WHIMSY ADMIN' in r.data
