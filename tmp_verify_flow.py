import re
import sys

sys.path.insert(0, '.')
import app as app_module
from app import app, PendingRegistration, User, db

client = app.test_client()
verification_required = bool(app.config.get('REQUIRE_EMAIL_VERIFICATION', True))


def get_csrf(path):
    html = client.get(path).data.decode('utf-8', errors='ignore')
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return match.group(1) if match else None

with app.app_context():
    User.query.filter(User.username == 'verify_flow_user').delete()
    PendingRegistration.query.filter(PendingRegistration.username == 'verify_flow_user').delete()
    db.session.commit()

original_sender = app_module._send_email_detailed
app_module._send_email_detailed = lambda *args, **kwargs: (True, '')

signup_token = get_csrf('/signup')
signup_resp = client.post(
    '/signup',
    data={
        'csrf_token': signup_token,
        'username': 'verify_flow_user',
        'email': 'verify_flow_user@example.com',
        'password': 'Strong@123',
        'confirm_password': 'Strong@123',
    },
    follow_redirects=True,
)
signup_text = signup_resp.data.decode('utf-8', errors='ignore')

with app.app_context():
    pending = PendingRegistration.query.filter_by(username='verify_flow_user').first()
    token = pending.token if pending else None

login_token = get_csrf('/login')
login_resp = client.post(
    '/login',
    data={
        'csrf_token': login_token,
        'identifier': 'verify_flow_user',
        'password': 'Strong@123',
    },
    follow_redirects=True,
)
login_text = login_resp.data.decode('utf-8', errors='ignore')

verify_resp = None
verify_text = ''
if token:
    verify_resp = client.get(f'/verify-email/{token}', follow_redirects=True)
    verify_text = verify_resp.data.decode('utf-8', errors='ignore')

login_token_after = get_csrf('/login')
login_after_resp = client.post(
    '/login',
    data={
        'csrf_token': login_token_after,
        'identifier': 'verify_flow_user',
        'password': 'Strong@123',
    },
    follow_redirects=True,
)

app_module._send_email_detailed = original_sender

print('signup_path=', signup_resp.request.path)
print('verification_required=', verification_required)
print('signup_has_pending_message=', 'Please verify your email to complete registration.' in signup_text)
print('login_before_verify_has_warning=', 'pending email verification' in login_text.lower())
print('verify_path=', verify_resp.request.path if verify_resp else None)
print('verify_success=', 'Email verified successfully!' in verify_text if verify_resp else None)
print('login_after_verify_path=', login_after_resp.request.path)
