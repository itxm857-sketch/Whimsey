from .conftest import login

def test_csrf_rejects_missing_token(client):
    r = client.post('/contact', data={'name':'A','email':'a@example.com','subject':'Hi','message':'Hello'})
    assert r.status_code == 400

def test_contact_message(client, csrf_token):
    r = client.post('/contact', data={'name':'A','email':'a@example.com','phone':'','subject':'Hi','message':'Hello','csrf_token':csrf_token}, follow_redirects=True)
    assert b'message has been sent' in r.data
