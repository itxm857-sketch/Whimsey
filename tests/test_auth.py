from .conftest import login

def test_register_and_login(client, csrf_token):
    r = client.post('/register', data={'name':'New User','email':'new@example.com','phone':'03001234567','password':'Password123','confirm_password':'Password123','csrf_token':csrf_token}, follow_redirects=True)
    assert r.status_code == 200
    assert b'Welcome to Whimsy' in r.data

def test_duplicate_registration(client, csrf_token):
    r = client.post('/register', data={'name':'New User','email':'customer@example.com','phone':'','password':'Password123','confirm_password':'Password123','csrf_token':csrf_token})
    assert b'Unable to create the account' in r.data

def test_invalid_login(client, csrf_token):
    r = client.post('/login', data={'email':'customer@example.com','password':'wrong','csrf_token':csrf_token})
    assert b'Invalid email or password' in r.data

def test_logout(client):
    login(client)
    r = client.get('/logout', follow_redirects=True)
    assert b'logged out' in r.data
