import re
import uuid
from app import app, db, User

uname = 'u' + uuid.uuid4().hex[:8]
email = uname + '@example.com'
password = 'TestPass123!'

with app.app_context():
    u = User.query.filter_by(username=uname).first()
    if u:
        db.session.delete(u)
        db.session.commit()

client = app.test_client()
r = client.get('/signup')
html = r.get_data(as_text=True)
m = re.search(r'name="csrf_token" value="([^"]+)"', html)
csrf = m.group(1) if m else ''

r2 = client.post('/signup', data={
    'csrf_token': csrf,
    'username': uname,
    'email': email,
    'password': password,
    'confirm_password': password,
}, follow_redirects=True)

print('signup_status', r2.status_code)
print('signup_success_message', 'Registration successful. You can now log in.' in r2.get_data(as_text=True))

r3 = client.get('/login')
html2 = r3.get_data(as_text=True)
m2 = re.search(r'name="csrf_token" value="([^"]+)"', html2)
csrf2 = m2.group(1) if m2 else ''

r4 = client.post('/login', data={
    'csrf_token': csrf2,
    'identifier': uname,
    'password': password,
}, follow_redirects=False)

print('login_status', r4.status_code)
print('login_location', r4.headers.get('Location'))
