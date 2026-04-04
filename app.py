from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import HTTPException
import re
import os
import secrets
import subprocess
from sqlalchemy import text, func, or_
try:
    import certifi
except Exception:
    certifi = None
import threading
import datetime
import json
import time
import urllib.request
import urllib.error
import urllib.parse
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
    else:
        gemini_model = None
except ImportError:
    gemini_model = None

app = Flask(__name__, instance_relative_config=True)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
# In production set a real secret key via environment or config
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')  # replace 'dev' in production (use env var) 
app.config.from_pyfile('config.py', silent=True)
app.config.setdefault('LAUNCH_PIPELINE_URL', os.environ.get('LAUNCH_PIPELINE_URL', ''))
app.config.setdefault('LAUNCH_PIPELINE_TIMEOUT_SECONDS', int(os.environ.get('LAUNCH_PIPELINE_TIMEOUT_SECONDS', '5')))
app.config.setdefault('TEST_ALERT_INTERVAL_MINUTES', int(os.environ.get('TEST_ALERT_INTERVAL_MINUTES', '300')))
app.config.setdefault('COURSE_COMPLETION_MINUTES', int(os.environ.get('COURSE_COMPLETION_MINUTES', '300')))
app.config.setdefault('QUIZ_PASS_THRESHOLD', int(os.environ.get('QUIZ_PASS_THRESHOLD', '70'))) 
app.config.setdefault('SMTP_HOST', os.environ.get('SMTP_HOST', ''))
app.config.setdefault('SMTP_PORT', os.environ.get('SMTP_PORT', ''))
app.config.setdefault('SMTP_USER', os.environ.get('SMTP_USER', ''))
app.config.setdefault('SMTP_PASS', os.environ.get('SMTP_PASS', ''))
app.config.setdefault('NODEMAILER_HOST', os.environ.get('NODEMAILER_HOST', ''))
app.config.setdefault('NODEMAILER_PORT', os.environ.get('NODEMAILER_PORT', ''))
app.config.setdefault('NODEMAILER_USER', os.environ.get('NODEMAILER_USER', ''))
app.config.setdefault('NODEMAILER_PASS', os.environ.get('NODEMAILER_PASS', ''))
app.config.setdefault('EMAIL_FROM', os.environ.get('EMAIL_FROM', ''))
app.config.setdefault('EMAIL_PROVIDER', os.environ.get('EMAIL_PROVIDER', ''))
app.config.setdefault('RESEND_API_KEY', os.environ.get('RESEND_API_KEY', ''))
app.config.setdefault('RESEND_API_URL', os.environ.get('RESEND_API_URL', 'https://api.resend.com/emails'))
app.config.setdefault('SERVER_BASE_URL', os.environ.get('SERVER_BASE_URL', ''))
app.config.setdefault('SMTP_ALLOW_INSECURE', os.environ.get('SMTP_ALLOW_INSECURE', 'false'))
app.config.setdefault('NODEMAILER_ALLOW_INSECURE', os.environ.get('NODEMAILER_ALLOW_INSECURE', 'false'))
app.config.setdefault('EMAIL_VERIFICATION_EXPIRY_SECONDS', int(os.environ.get('EMAIL_VERIFICATION_EXPIRY_SECONDS', '900')))
app.config.setdefault(
    'SMTP_USE_AUTH',
    str(os.environ.get('SMTP_USE_AUTH', 'true')).strip().lower() in ('1', 'true', 'yes', 'on')
)
app.config.setdefault(
    'NODEMAILER_USE_AUTH',
    str(os.environ.get('NODEMAILER_USE_AUTH', 'true')).strip().lower() in ('1', 'true', 'yes', 'on')
)
app.config.setdefault(
    'REQUIRE_EMAIL_VERIFICATION',
    str(os.environ.get('REQUIRE_EMAIL_VERIFICATION', 'true')).strip().lower() in ('1', 'true', 'yes', 'on')
)

# Log email provider configuration on startup (for debugging)
@app.before_request
def log_smtp_config():
    try:
        ensure_test_alert_dispatcher_started()
        if not hasattr(app, '_smtp_logged'):
            email_provider = str(app.config.get('EMAIL_PROVIDER') or os.environ.get('EMAIL_PROVIDER') or '').strip().lower()
            resend_api_key = (app.config.get('RESEND_API_KEY') or os.environ.get('RESEND_API_KEY') or '').strip()
            if not email_provider:
                email_provider = 'resend' if resend_api_key else 'nodemailer'

            nodemailer_host = (app.config.get('NODEMAILER_HOST') or os.environ.get('NODEMAILER_HOST') or app.config.get('SMTP_HOST') or os.environ.get('SMTP_HOST') or '').strip()
            nodemailer_user = (app.config.get('NODEMAILER_USER') or os.environ.get('NODEMAILER_USER') or app.config.get('SMTP_USER') or os.environ.get('SMTP_USER') or '').strip()
            nodemailer_port = (str(app.config.get('NODEMAILER_PORT') or os.environ.get('NODEMAILER_PORT') or app.config.get('SMTP_PORT') or os.environ.get('SMTP_PORT') or '')).strip()
            email_from = (app.config.get('EMAIL_FROM') or os.environ.get('EMAIL_FROM') or '').strip()
            nodemailer_pass = (app.config.get('NODEMAILER_PASS') or os.environ.get('NODEMAILER_PASS') or app.config.get('SMTP_PASS') or os.environ.get('SMTP_PASS') or '').strip()
            nodemailer_use_auth_raw = app.config.get('NODEMAILER_USE_AUTH')
            if nodemailer_use_auth_raw is None:
                nodemailer_use_auth_raw = app.config.get('SMTP_USE_AUTH')
            if isinstance(nodemailer_use_auth_raw, bool):
                nodemailer_use_auth = nodemailer_use_auth_raw
            else:
                nodemailer_use_auth = str(nodemailer_use_auth_raw).strip().lower() in ('1', 'true', 'yes', 'on')

            if email_provider == 'resend':
                if resend_api_key and email_from:
                    app.logger.info(f'Email provider configured: provider=resend, from={email_from}')
                else:
                    missing = []
                    if not resend_api_key:
                        missing.append('RESEND_API_KEY')
                    if not email_from:
                        missing.append('EMAIL_FROM')
                    app.logger.warning(f'Resend not fully configured - missing fields: {", ".join(missing)}')
            elif all([nodemailer_host, nodemailer_port, email_from]) and (not nodemailer_use_auth or (nodemailer_user and nodemailer_pass)):
                app.logger.info(f'Email provider configured: provider=nodemailer, host={nodemailer_host}, user={nodemailer_user}, port={nodemailer_port}, from={email_from}')
            else:
                missing = []
                if not nodemailer_host:
                    missing.append('NODEMAILER_HOST')
                if not nodemailer_port:
                    missing.append('NODEMAILER_PORT')
                if not email_from:
                    missing.append('EMAIL_FROM')
                if nodemailer_use_auth and not nodemailer_user:
                    missing.append('NODEMAILER_USER')
                if nodemailer_use_auth and not nodemailer_pass:
                    missing.append('NODEMAILER_PASS')
                app.logger.warning(f'NodeMailer not fully configured - missing fields: {", ".join(missing)}')

            # Surface email misconfiguration loudly when verification is required.
            if app.config.get('REQUIRE_EMAIL_VERIFICATION'):
                if email_provider == 'resend' and not all([resend_api_key, email_from]):
                    app.logger.error('REQUIRE_EMAIL_VERIFICATION is enabled but Resend is incomplete.')
                if email_provider != 'resend':
                    nodemailer_ready = all([nodemailer_host, nodemailer_port, email_from]) and (
                        (not nodemailer_use_auth) or (nodemailer_user and nodemailer_pass)
                    )
                    if not nodemailer_ready:
                        app.logger.error('REQUIRE_EMAIL_VERIFICATION is enabled but NodeMailer is incomplete.')
            app._smtp_logged = True
    except Exception as exc:
        app.logger.exception(f'Non-fatal before_request email config logging failure: {exc}')


@app.errorhandler(500)
def handle_internal_server_error(exc):
    app.logger.exception(f'Unhandled Internal Server Error: {exc}')
    try:
        db.session.rollback()
    except Exception:
        pass
    wants_json = request.path.startswith('/api/') or request.is_json
    if wants_json:
        return jsonify({'error': 'Internal server error'}), 500
    return 'Internal Server Error. Please try again shortly.', 500


@app.errorhandler(Exception)
def handle_unexpected_exception(exc):
    if isinstance(exc, HTTPException):
        return exc

    app.logger.exception(f'Unhandled exception: {exc}')
    try:
        db.session.rollback()
    except Exception:
        pass

    wants_json = request.path.startswith('/api/') or request.is_json
    if wants_json:
        return jsonify({'error': 'Internal server error'}), 500
    return 'Internal Server Error. Please try again shortly.', 500

# Simple in-memory user store (for demo only)
users = {}


def ensure_domains_seeded_if_empty():
    """Seed domains at runtime if the table exists but has no rows."""
    try:
        current_count = Domain.query.count()
    except Exception as exc:
        app.logger.warning(f'Unable to check domain count: {exc}')
        return

    if current_count > 0:
        return

    try:
        from reset_domains import reset_domains
        reset_domains()
        app.logger.info('Domain auto-seed completed via reset_domains fallback.')
    except Exception as exc:
        app.logger.warning(f'Domain auto-seed failed: {exc}')

# Database setup and avatar uploads
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    """Return True when a filename has an allowed image extension."""
    return bool(filename) and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

data_dir = os.environ.get('DATA_DIR', app.instance_path)
os.makedirs(data_dir, exist_ok=True)
db_path = os.environ.get('DATABASE_PATH', os.path.join(data_dir, 'database.db'))
database_url = os.environ.get('DATABASE_URL', '').strip()
if database_url:
    # Render may expose legacy postgres:// URLs; SQLAlchemy expects postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    avatar = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), default='user')
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    email_token_created_at = db.Column(db.DateTime, nullable=True)


class PendingRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    token_created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    instructor = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(30), default='Beginner')
    duration = db.Column(db.String(40), default='')
    lessons = db.Column(db.Integer, default=0)
    students = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0)
    reviews = db.Column(db.Integer, default=0)
    thumbnail = db.Column(db.String(20), default='ðŸ“š')
    status = db.Column(db.String(20), default='bookmarked')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    video_url = db.Column(db.String(500), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, default=1)
    duration_minutes = db.Column(db.Integer, default=0)
    level = db.Column(db.String(30), default='Beginner')
    is_free = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    course = db.relationship('Course', backref=db.backref('lessons_list', cascade='all, delete-orphan', lazy=True))


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    level_assessed = db.Column(db.String(30), nullable=True)
    recommended_lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=True)
    progress_percent = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref=db.backref('enrollments', cascade='all, delete-orphan', lazy=True))
    course = db.relationship('Course', backref=db.backref('enrollments', cascade='all, delete-orphan', lazy=True))
    recommended_lesson = db.relationship('Lesson')


# ===== NEW DOMAIN-BASED LEARNING SYSTEM =====

class Domain(db.Model):
    """Learning domains: ML, Python, Web Dev, etc."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(10), default='ðŸ“š')
    keywords = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class DomainEnrollment(db.Model):
    """Track user domain selection and assessed level"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    selected_level = db.Column(db.String(30), nullable=False)
    assessed_level = db.Column(db.String(30), nullable=True)
    level_quiz_score = db.Column(db.Integer, default=0)
    learning_phase = db.Column(db.String(30), default='assessment')
    preferred_course_link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_quiz_date = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('domain_enrollments', cascade='all, delete-orphan', lazy=True))
    domain = db.relationship('Domain', backref=db.backref('enrollments', cascade='all, delete-orphan', lazy=True))


class DomainQuiz(db.Model):
    """Store generated quizzes for domains and levels"""
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    level = db.Column(db.String(30), nullable=False)
    quiz_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    domain = db.relationship('Domain', backref=db.backref('quizzes', cascade='all, delete-orphan', lazy=True))


class DailyQuiz(db.Model):
    """Track daily quizzes for users"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_enrollment_id = db.Column(db.Integer, db.ForeignKey('domain_enrollment.id'), nullable=False)
    quiz_data = db.Column(db.Text, nullable=False)
    user_answers = db.Column(db.Text, nullable=True)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    grade = db.Column(db.String(10), nullable=True)
    based_on_course_link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('daily_quizzes', cascade='all, delete-orphan', lazy=True))
    domain_enrollment = db.relationship('DomainEnrollment', backref=db.backref('daily_quizzes', cascade='all, delete-orphan', lazy=True))


class LearningProgress(db.Model):
    """Track user's learning journey"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_enrollment_id = db.Column(db.Integer, db.ForeignKey('domain_enrollment.id'), nullable=False)
    activity_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    extra_data = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref=db.backref('learning_progress', cascade='all, delete-orphan', lazy=True))
    domain_enrollment = db.relationship('DomainEnrollment', backref=db.backref('progress_logs', cascade='all, delete-orphan', lazy=True))


class CourseLink(db.Model):
    """Store fetched course links from internet"""
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False, unique=True)
    source = db.Column(db.String(50))
    rating = db.Column(db.Float, default=0)
    duration_minutes = db.Column(db.Integer, nullable=True)
    price = db.Column(db.String(20), default='Free')
    language = db.Column(db.String(20), default='English')
    difficulty = db.Column(db.String(30), nullable=True)
    fetched_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    domain = db.relationship('Domain', backref=db.backref('course_links', cascade='all, delete-orphan', lazy=True))


class DomainCourseProgress(db.Model):
    """Track tutorial completion for a specific domain course link"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    course_link_id = db.Column(db.Integer, db.ForeignKey('course_link.id'), nullable=False)
    tutorial_minutes = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, nullable=True)
    quiz_unlocked = db.Column(db.Boolean, default=False)
    quiz_passed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref=db.backref('domain_course_progress', cascade='all, delete-orphan', lazy=True))
    domain = db.relationship('Domain')
    course_link = db.relationship('CourseLink')


class DomainCourseQuiz(db.Model):
    """Quiz content for a specific domain course link"""
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    course_link_id = db.Column(db.Integer, db.ForeignKey('course_link.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    quiz_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    domain = db.relationship('Domain')
    course_link = db.relationship('CourseLink')


class DomainCourseQuizAttempt(db.Model):
    """User quiz attempt for a domain course link"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    course_link_id = db.Column(db.Integer, db.ForeignKey('course_link.id'), nullable=False)
    quiz_data = db.Column(db.Text, nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_heartbeat_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)
    violation_count = db.Column(db.Integer, default=0)
    invalidated = db.Column(db.Boolean, default=False)
    violation_reason = db.Column(db.String(255), nullable=True)

    user = db.relationship('User')
    domain = db.relationship('Domain')
    course_link = db.relationship('CourseLink')


class DomainCertificate(db.Model):
    """Certificates issued after course completion and quiz pass"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    course_link_id = db.Column(db.Integer, db.ForeignKey('course_link.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200), default='SkillForge Academy')
    certificate_code = db.Column(db.String(100), unique=True, nullable=False)
    grade = db.Column(db.String(10), default='A')
    score = db.Column(db.Integer, default=0)
    issued_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_sample = db.Column(db.Boolean, default=False)

    user = db.relationship('User')
    domain = db.relationship('Domain')
    course_link = db.relationship('CourseLink')


class DomainTestAlertSchedule(db.Model):
    """Recurring test alerts after course completion until first test attempt"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    course_link_id = db.Column(db.Integer, db.ForeignKey('course_link.id'), nullable=False)
    course_completed_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    next_alert_at = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, default=True)
    completion_notified = db.Column(db.Boolean, default=False)
    scheduling_notified = db.Column(db.Boolean, default=False)
    stopped_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'domain_id', 'course_link_id', name='uq_domain_test_alert_schedule_triplet'),
    )

    user = db.relationship('User')
    domain = db.relationship('Domain')
    course_link = db.relationship('CourseLink')


def notify_launch_pipeline(event_type, payload):
    launch_url = app.config.get('LAUNCH_PIPELINE_URL')
    if not launch_url:
        return False

    body = {
        'event_type': event_type,
        'event_time': datetime.datetime.utcnow().isoformat() + 'Z',
        'payload': payload
    }

    timeout_seconds = int(app.config.get('LAUNCH_PIPELINE_TIMEOUT_SECONDS', 5))
    request_body = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(
        launch_url,
        data=request_body,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            status_code = getattr(response, 'status', 200)
            return 200 <= status_code < 300
    except urllib.error.HTTPError as exc:
        app.logger.warning(f'Launch pipeline HTTP error for {event_type}: {exc.code}')
    except Exception as exc:
        app.logger.warning(f'Launch pipeline request failed for {event_type}: {exc}')
    return False


def get_alert_interval_minutes():
    return max(1, int(app.config.get('TEST_ALERT_INTERVAL_MINUTES', 300)))


def get_course_completion_minutes():
    return max(1, int(app.config.get('COURSE_COMPLETION_MINUTES', 300)))


def format_duration_label(minutes):
    safe_minutes = max(1, int(minutes or 0))
    if safe_minutes % 60 == 0:
        hours = safe_minutes // 60
        return f"{hours} hour" if hours == 1 else f"{hours} hours"
    return f"{safe_minutes} minutes"


def infer_course_duration_minutes(course_title, source):
    if course_title:
        duration_match = re.search(r'(\d+(?:\.\d+)?)\s*(hours?|hrs?|hr|h|minutes?|mins?|min|m)\b', course_title.lower())
        if duration_match:
            value = float(duration_match.group(1))
            unit = duration_match.group(2)
            if unit.startswith('h'):
                return max(30, int(round(value * 60)))
            return max(15, int(round(value)))

    source_defaults = {
        'youtube': 180,
        'freecodecamp': 240,
        'udemy': 300,
        'coursera': 360,
        'edx': 360,
        'datacamp': 240,
        'khan academy': 180,
        'linkedin learning': 180,
        'pluralsight': 240,
        'codecademy': 180,
        'microsoft learn': 180,
    }
    source_key = (source or '').strip().lower()
    return source_defaults.get(source_key, get_course_completion_minutes())


def get_required_minutes_for_course(course_link_id):
    course_link = CourseLink.query.get(course_link_id)
    if not course_link:
        return get_course_completion_minutes()
    return max(1, int(course_link.duration_minutes or get_course_completion_minutes()))


def tutorial_requirement_text(required_minutes=None):
    required_minutes = max(1, int(required_minutes or get_course_completion_minutes()))
    if required_minutes % 60 == 0:
        hours = required_minutes // 60
        if hours == 1:
            return 'Complete 1 hour of tutorials before taking the quiz.'
        return f'Complete {hours} hours of tutorials before taking the quiz.'
    return f'Complete {required_minutes} minutes of tutorials before taking the quiz.'


def ensure_test_alert_schedule(user_id, domain_id, course_link_id, completed_at):
    schedule = DomainTestAlertSchedule.query.filter_by(
        user_id=user_id,
        domain_id=domain_id,
        course_link_id=course_link_id
    ).first()

    interval_minutes = get_alert_interval_minutes()
    first_alert_at = completed_at + datetime.timedelta(minutes=interval_minutes)

    if not schedule:
        schedule = DomainTestAlertSchedule(
            user_id=user_id,
            domain_id=domain_id,
            course_link_id=course_link_id,
            course_completed_at=completed_at,
            next_alert_at=first_alert_at,
            active=True,
            updated_at=datetime.datetime.utcnow()
        )
        db.session.add(schedule)
    else:
        schedule.course_completed_at = schedule.course_completed_at or completed_at
        if not schedule.active:
            schedule.active = True
            schedule.stopped_at = None
        if not schedule.next_alert_at:
            schedule.next_alert_at = first_alert_at
        schedule.updated_at = datetime.datetime.utcnow()
    return schedule


def stop_test_alert_schedule(user_id, domain_id, course_link_id):
    schedule = DomainTestAlertSchedule.query.filter_by(
        user_id=user_id,
        domain_id=domain_id,
        course_link_id=course_link_id,
        active=True
    ).first()
    if schedule:
        schedule.active = False
        schedule.stopped_at = datetime.datetime.utcnow()
        schedule.updated_at = datetime.datetime.utcnow()
        db.session.commit()


def process_due_test_alerts(batch_size=50):
    now = datetime.datetime.utcnow()
    due_schedules = DomainTestAlertSchedule.query.filter(
        DomainTestAlertSchedule.active == True,
        DomainTestAlertSchedule.next_alert_at <= now
    ).limit(batch_size).all()

    if not due_schedules:
        return

    interval_minutes = get_alert_interval_minutes()
    interval_delta = datetime.timedelta(minutes=interval_minutes)

    for schedule in due_schedules:
        payload = {
            'user_id': schedule.user_id,
            'domain_id': schedule.domain_id,
            'course_link_id': schedule.course_link_id,
            'course_completed_at': schedule.course_completed_at.isoformat() + 'Z' if schedule.course_completed_at else None,
            'next_alert_at': schedule.next_alert_at.isoformat() + 'Z' if schedule.next_alert_at else None,
            'message': 'Please attempt your course test.'
        }
        notify_launch_pipeline('test_alert_reminder', payload)
        schedule.next_alert_at = (schedule.next_alert_at or now) + interval_delta
        schedule.updated_at = now

    db.session.commit()


def run_test_alert_dispatcher():
    with app.app_context():
        while True:
            try:
                process_due_test_alerts()
            except Exception as exc:
                app.logger.warning(f'Test alert dispatcher failed: {exc}')
            time.sleep(60)


def ensure_test_alert_dispatcher_started():
    if getattr(app, '_test_alert_dispatcher_started', False):
        return
    dispatcher = threading.Thread(target=run_test_alert_dispatcher, daemon=True)
    dispatcher.start()
    app._test_alert_dispatcher_started = True

# Ensure DB is created and migrate any in-memory users
with app.app_context():
    try:
        db.create_all()

        backend_name = db.engine.url.get_backend_name()

        # Lightweight migration for existing PostgreSQL DBs used on Render.
        if backend_name in ('postgresql', 'postgres'):
            postgres_migrations = [
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE',
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255)',
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email_token_created_at TIMESTAMP',
                'ALTER TABLE domain_enrollment ADD COLUMN IF NOT EXISTS assessed_level VARCHAR(30)',
                'ALTER TABLE course_link ADD COLUMN IF NOT EXISTS duration_minutes INTEGER',
                'ALTER TABLE domain_course_quiz_attempt ADD COLUMN IF NOT EXISTS violation_count INTEGER DEFAULT 0',
            ]
            for stmt in postgres_migrations:
                try:
                    db.session.execute(text(stmt))
                except Exception as migration_exc:
                    app.logger.warning(f'PostgreSQL migration step failed ({stmt}): {migration_exc}')
            try:
                db.session.execute(text('UPDATE "user" SET email_verified = TRUE WHERE email_verified IS NULL'))
                db.session.execute(text('UPDATE domain_course_quiz_attempt SET violation_count = 0 WHERE violation_count IS NULL'))
            except Exception as migration_exc:
                app.logger.warning(f'PostgreSQL migration data backfill warning: {migration_exc}')
            db.session.commit()

        # Lightweight migration for existing SQLite DBs only.
        if backend_name == 'sqlite':
            columns = [row[1] for row in db.session.execute(text("PRAGMA table_info(user)"))]
            if "email_verified" not in columns:
                db.session.execute(text("ALTER TABLE user ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
            if "email_verification_token" not in columns:
                db.session.execute(text("ALTER TABLE user ADD COLUMN email_verification_token VARCHAR(255)"))
            db.session.execute(text("UPDATE user SET email_verified = 1 WHERE email_verified IS NULL"))
            db.session.commit()

            domain_enrollment_columns = [row[1] for row in db.session.execute(text("PRAGMA table_info(domain_enrollment)"))]
            if "assessed_level" not in domain_enrollment_columns:
                db.session.execute(text("ALTER TABLE domain_enrollment ADD COLUMN assessed_level VARCHAR(30)"))
            db.session.commit()

            course_link_columns = [row[1] for row in db.session.execute(text("PRAGMA table_info(course_link)"))]
            if "duration_minutes" not in course_link_columns:
                db.session.execute(text("ALTER TABLE course_link ADD COLUMN duration_minutes INTEGER"))
            db.session.commit()

            quiz_attempt_columns = [row[1] for row in db.session.execute(text("PRAGMA table_info(domain_course_quiz_attempt)"))]
            if "violation_count" not in quiz_attempt_columns:
                db.session.execute(text("ALTER TABLE domain_course_quiz_attempt ADD COLUMN violation_count INTEGER DEFAULT 0"))
                db.session.execute(text("UPDATE domain_course_quiz_attempt SET violation_count = 0 WHERE violation_count IS NULL"))
            db.session.commit()

        for uname, info in list(users.items()):
            if not User.query.filter_by(username=uname).first():
                try:
                    created = datetime.datetime.fromisoformat(info.get('created_at')) if info.get('created_at') else datetime.datetime.utcnow()
                except Exception:
                    created = datetime.datetime.utcnow()
                u = User(
                    username=uname,
                    email=info.get('email', ''),
                    password_hash=info.get('password_hash', ''),
                    created_at=created,
                    email_verified=True
                )
                db.session.add(u)
        db.session.commit()
        # Seed initial admin if none exists
        if User.query.filter_by(role='admin').count() == 0:
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@skillforge.local')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@123')
            if not User.query.filter_by(username=admin_username).first():
                admin_user = User(
                    username=admin_username,
                    email=admin_email,
                    password_hash=generate_password_hash(admin_password),
                    created_at=datetime.datetime.utcnow(),
                    role='admin',
                    email_verified=True
                )
                db.session.add(admin_user)
                db.session.commit()
    except Exception as e:
        print(f"Database initialization warning: {e}")
        # Database might need to be recreated
        pass
    # Seed courses and lessons if empty
    try:
        should_seed_courses = Course.query.count() == 0
    except Exception:
        should_seed_courses = False

    if should_seed_courses:
        sample_courses = [
            {
                'title': 'HTML & CSS Foundations',
                'category': 'Web Development',
                'instructor': 'Ava Thompson',
                'description': 'Build beautiful, responsive web pages using semantic HTML and modern CSS.',
                'level': 'Beginner',
                'duration': '4 weeks',
                'thumbnail': 'ðŸ§±',
                'status': 'bookmarked',
                'lessons': [
                    ('Intro to HTML', 'https://example.com/html-1', 'Structure your pages with semantic HTML.', 1, 25, 'Zero'),
                    ('CSS Basics', 'https://example.com/css-1', 'Selectors, colors, and typography.', 2, 30, 'Beginner'),
                    ('Layouts with Flexbox', 'https://example.com/css-2', 'Flexible layouts and alignment.', 3, 35, 'Beginner'),
                    ('Responsive Design', 'https://example.com/css-3', 'Media queries and mobile-first.', 4, 30, 'Beginner')
                ]
            },
            {
                'title': 'JavaScript Essentials',
                'category': 'Programming',
                'instructor': 'Noah Patel',
                'description': 'Master JavaScript fundamentals, DOM, and async programming.',
                'level': 'Beginner',
                'duration': '6 weeks',
                'thumbnail': 'ðŸŸ¨',
                'status': 'bookmarked',
                'lessons': [
                    ('JS Fundamentals', 'https://example.com/js-1', 'Variables, functions, and control flow.', 1, 35, 'Beginner'),
                    ('DOM Manipulation', 'https://example.com/js-2', 'Selecting and updating elements.', 2, 40, 'Beginner'),
                    ('Events & Forms', 'https://example.com/js-3', 'Build interactive pages.', 3, 35, 'Beginner'),
                    ('Async JavaScript', 'https://example.com/js-4', 'Promises, async/await.', 4, 40, 'Intermediate')
                ]
            },
            {
                'title': 'Python for Beginners',
                'category': 'Programming',
                'instructor': 'Liam Carter',
                'description': 'Start coding with Python and build real-world scripts.',
                'level': 'Beginner',
                'duration': '5 weeks',
                'thumbnail': 'ðŸ',
                'status': 'bookmarked',
                'lessons': [
                    ('Getting Started', 'https://example.com/py-1', 'Install Python and run your first script.', 1, 25, 'Zero'),
                    ('Data Types', 'https://example.com/py-2', 'Strings, numbers, lists, dicts.', 2, 35, 'Beginner'),
                    ('Control Flow', 'https://example.com/py-3', 'If/else, loops, and logic.', 3, 35, 'Beginner'),
                    ('Functions', 'https://example.com/py-4', 'Write reusable code.', 4, 35, 'Beginner')
                ]
            },
            {
                'title': 'Data Structures & Algorithms',
                'category': 'Computer Science',
                'instructor': 'Prof. Michael Chen',
                'description': 'Learn core DS&A patterns for interviews and problem solving.',
                'level': 'Intermediate',
                'duration': '10 weeks',
                'thumbnail': 'ðŸ“Š',
                'status': 'bookmarked',
                'lessons': [
                    ('Big-O & Complexity', 'https://example.com/dsa-1', 'Analyze time and space.', 1, 40, 'Beginner'),
                    ('Arrays & Strings', 'https://example.com/dsa-2', 'Common patterns and techniques.', 2, 45, 'Beginner'),
                    ('Stacks & Queues', 'https://example.com/dsa-3', 'Linear data structures.', 3, 45, 'Intermediate'),
                    ('Trees & Graphs', 'https://example.com/dsa-4', 'Traversal and search.', 4, 50, 'Intermediate')
                ]
            },
            {
                'title': 'SQL Crash Course',
                'category': 'Database',
                'instructor': 'Sofia Alvarez',
                'description': 'Query and analyze data using modern SQL.',
                'level': 'Beginner',
                'duration': '3 weeks',
                'thumbnail': 'ðŸ§®',
                'status': 'bookmarked',
                'lessons': [
                    ('SELECT Basics', 'https://example.com/sql-1', 'Retrieve data from tables.', 1, 25, 'Beginner'),
                    ('Filtering & Sorting', 'https://example.com/sql-2', 'WHERE, ORDER BY, LIMIT.', 2, 30, 'Beginner'),
                    ('Joins', 'https://example.com/sql-3', 'Combine data from multiple tables.', 3, 35, 'Intermediate')
                ]
            }
        ]

        for course_data in sample_courses:
            lessons = course_data.pop('lessons', [])
            course = Course(
                title=course_data['title'],
                category=course_data['category'],
                instructor=course_data['instructor'],
                description=course_data['description'],
                level=course_data['level'],
                duration=course_data['duration'],
                thumbnail=course_data['thumbnail'],
                status=course_data['status'],
                lessons=len(lessons),
                students=0,
                rating=0,
                reviews=0
            )
            db.session.add(course)
            db.session.flush()

            for title, video_url, summary, order_index, duration_minutes, level in lessons:
                lesson = Lesson(
                    course_id=course.id,
                    title=title,
                    video_url=video_url,
                    summary=summary,
                    order_index=order_index,
                    duration_minutes=duration_minutes,
                    level=level,
                    is_free=True
                )
                db.session.add(lesson)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Course seed skipped due to DB error: {e}")
    
    # Seed domains if empty
    try:
        should_seed_domains = Domain.query.count() == 0
    except Exception:
        should_seed_domains = False

    if should_seed_domains:
        domains_data = [
            # Top 100 High-Demand Tech Domains
            {'name': 'Machine Learning', 'description': 'AI/ML models, neural networks, deep learning, NLP, computer vision', 'icon': 'ðŸ§ ', 'keywords': 'tensorflow, pytorch, scikit-learn, nlp, cv, neural'},
            {'name': 'Python Programming', 'description': 'Core Python, data structures, automation, scripting, libraries', 'icon': 'ðŸ', 'keywords': 'python, pandas, numpy, scripting, automation, oop'},
            {'name': 'Web Development (MERN)', 'description': 'Full-stack web apps with MongoDB, Express, React, Node.js', 'icon': 'ðŸŒ', 'keywords': 'react, nodejs, express, mongodb, javascript, fullstack'},
            {'name': 'Flask Backend', 'description': 'Build APIs, microservices, and backend systems with Flask', 'icon': 'ðŸŒ¶ï¸', 'keywords': 'flask, sqlalchemy, api, backend, microservices, rest'},
            {'name': 'Data Science', 'description': 'Data analysis, visualization, statistical modeling, business intelligence', 'icon': 'ðŸ“Š', 'keywords': 'pandas, matplotlib, sql, statistics, analytics, bi'},
            {'name': 'Cloud & DevOps', 'description': 'AWS, Docker, Kubernetes, CI/CD, infrastructure automation', 'icon': 'â˜ï¸', 'keywords': 'aws, docker, kubernetes, ci-cd, terraform, devops'},
            {'name': 'Mobile Development', 'description': 'iOS, Android, React Native, Flutter app development', 'icon': 'ðŸ“±', 'keywords': 'ios, android, react native, flutter, mobile'},
            {'name': 'Database Design', 'description': 'SQL, NoSQL, schema design, optimization, querying', 'icon': 'ðŸ—„ï¸', 'keywords': 'sql, mongodb, postgres, mysql, database, schema'},
            {'name': 'Cybersecurity', 'description': 'Network security, encryption, penetration testing, secure coding', 'icon': 'ðŸ”', 'keywords': 'security, encryption, hacking, networks, ssl, auth'},
            {'name': 'Blockchain & Web3', 'description': 'Cryptocurrency, smart contracts, blockchain technology, DeFi', 'icon': 'â›“ï¸', 'keywords': 'blockchain, crypto, solidity, defi, nft, web3'},
            # 11-20
            {'name': 'Artificial Intelligence', 'description': 'AI fundamentals, expert systems, cognitive computing, AI ethics', 'icon': 'ðŸ¤–', 'keywords': 'ai, cognitive, expert systems, agi, ethics'},
            {'name': 'Java Programming', 'description': 'Enterprise Java, Spring Boot, microservices, JVM optimization', 'icon': 'â˜•', 'keywords': 'java, spring, jvm, maven, gradle, enterprise'},
            {'name': 'JavaScript Mastery', 'description': 'Modern JS, ES6+, async programming, design patterns', 'icon': 'âš¡', 'keywords': 'javascript, es6, async, promises, patterns'},
            {'name': 'TypeScript', 'description': 'Static typing, interfaces, generics, advanced TypeScript patterns', 'icon': 'ðŸ”·', 'keywords': 'typescript, types, interfaces, generics'},
            {'name': 'React.js', 'description': 'Component architecture, hooks, state management, performance', 'icon': 'âš›ï¸', 'keywords': 'react, hooks, redux, context, jsx'},
            {'name': 'Angular', 'description': 'Enterprise Angular apps, RxJS, services, dependency injection', 'icon': 'ðŸ…°ï¸', 'keywords': 'angular, rxjs, typescript, spa, components'},
            {'name': 'Vue.js', 'description': 'Progressive framework, Vuex, composition API, Nuxt.js', 'icon': 'ðŸŸ¢', 'keywords': 'vue, vuex, nuxt, composition, sfc'},
            {'name': 'Node.js Backend', 'description': 'Server-side JavaScript, Express, APIs, real-time apps', 'icon': 'ðŸŸ©', 'keywords': 'nodejs, express, npm, event-loop, async'},
            {'name': 'Django Framework', 'description': 'Python web framework, ORM, MVT, RESTful APIs', 'icon': 'ðŸŽ¸', 'keywords': 'django, orm, rest, python, mvt'},
            {'name': 'FastAPI', 'description': 'Modern Python API framework, async, auto documentation', 'icon': 'âš¡', 'keywords': 'fastapi, async, python, openapi, pydantic'},
            # 21-30
            {'name': 'Ruby on Rails', 'description': 'Full-stack framework, MVC, ActiveRecord, rapid development', 'icon': 'ðŸ’Ž', 'keywords': 'rails, ruby, mvc, activerecord, gems'},
            {'name': 'Go Programming', 'description': 'Golang, concurrency, microservices, system programming', 'icon': 'ðŸ¹', 'keywords': 'golang, goroutines, concurrency, performance'},
            {'name': 'Rust Programming', 'description': 'Memory safety, systems programming, performance, WebAssembly', 'icon': 'ðŸ¦€', 'keywords': 'rust, memory, ownership, wasm, systems'},
            {'name': 'C++ Programming', 'description': 'Modern C++, STL, templates, performance optimization', 'icon': 'âš™ï¸', 'keywords': 'cpp, stl, templates, performance, memory'},
            {'name': 'C# & .NET', 'description': '.NET Core, ASP.NET, Entity Framework, Azure integration', 'icon': 'ðŸ”µ', 'keywords': 'csharp, dotnet, asp, ef, azure'},
            {'name': 'Kotlin Development', 'description': 'Android development, coroutines, multiplatform', 'icon': 'ðŸŽ¯', 'keywords': 'kotlin, android, coroutines, jvm, multiplatform'},
            {'name': 'Swift & iOS', 'description': 'iOS app development, SwiftUI, UIKit, App Store publishing', 'icon': 'ðŸŽ', 'keywords': 'swift, ios, swiftui, uikit, xcode'},
            {'name': 'Flutter Development', 'description': 'Cross-platform apps, Dart, widgets, state management', 'icon': 'ðŸ¦‹', 'keywords': 'flutter, dart, widgets, crossplatform, material'},
            {'name': 'React Native', 'description': 'Mobile apps with React, native modules, performance', 'icon': 'ðŸ“²', 'keywords': 'reactnative, javascript, mobile, expo, native'},
            {'name': 'SQL Mastery', 'description': 'Advanced queries, optimization, indexing, stored procedures', 'icon': 'ðŸ—ƒï¸', 'keywords': 'sql, queries, optimization, joins, indexing'},
            # 31-40
            {'name': 'PostgreSQL', 'description': 'Advanced PostgreSQL, JSONB, full-text search, replication', 'icon': 'ðŸ˜', 'keywords': 'postgres, sql, jsonb, replication, pgadmin'},
            {'name': 'MongoDB', 'description': 'NoSQL database, aggregation, sharding, replica sets', 'icon': 'ðŸƒ', 'keywords': 'mongodb, nosql, aggregation, sharding, atlas'},
            {'name': 'Redis & Caching', 'description': 'In-memory databases, caching strategies, pub/sub', 'icon': 'ðŸ”´', 'keywords': 'redis, cache, inmemory, pubsub, performance'},
            {'name': 'GraphQL', 'description': 'Query language, Apollo, schema design, subscriptions', 'icon': 'ðŸ”·', 'keywords': 'graphql, apollo, queries, schema, subscriptions'},
            {'name': 'REST API Design', 'description': 'RESTful principles, API security, documentation, versioning', 'icon': 'ðŸ”Œ', 'keywords': 'rest, api, http, swagger, endpoints'},
            {'name': 'AWS Cloud', 'description': 'EC2, S3, Lambda, RDS, CloudFormation, serverless', 'icon': 'â˜ï¸', 'keywords': 'aws, ec2, lambda, s3, cloud, serverless'},
            {'name': 'Azure Cloud', 'description': 'Azure services, DevOps, Functions, App Services', 'icon': 'ðŸ”·', 'keywords': 'azure, cloud, devops, functions, microsoft'},
            {'name': 'Google Cloud Platform', 'description': 'GCP services, App Engine, BigQuery, Kubernetes Engine', 'icon': 'â˜ï¸', 'keywords': 'gcp, google, cloud, bigquery, kubernetes'},
            {'name': 'Docker Containerization', 'description': 'Containers, images, Docker Compose, orchestration', 'icon': 'ðŸ³', 'keywords': 'docker, containers, compose, images, orchestration'},
            {'name': 'Kubernetes', 'description': 'Container orchestration, pods, services, deployments', 'icon': 'âš“', 'keywords': 'kubernetes, k8s, orchestration, pods, helm'},
            # 41-50
            {'name': 'CI/CD Pipelines', 'description': 'Jenkins, GitLab CI, GitHub Actions, automation', 'icon': 'ðŸ”„', 'keywords': 'cicd, jenkins, github actions, automation, pipeline'},
            {'name': 'Git & Version Control', 'description': 'Git workflows, branching, merging, collaboration', 'icon': 'ðŸ“š', 'keywords': 'git, github, gitlab, version control, branching'},
            {'name': 'Microservices Architecture', 'description': 'Service design, communication, patterns, scalability', 'icon': 'ðŸ”—', 'keywords': 'microservices, architecture, apis, scalability'},
            {'name': 'System Design', 'description': 'Scalable systems, architecture patterns, trade-offs', 'icon': 'ðŸ—ï¸', 'keywords': 'system design, architecture, scalability, patterns'},
            {'name': 'Software Architecture', 'description': 'Design patterns, SOLID, clean architecture, DDD', 'icon': 'ðŸ›ï¸', 'keywords': 'architecture, patterns, solid, ddd, clean code'},
            {'name': 'Test-Driven Development', 'description': 'TDD, unit testing, integration tests, test automation', 'icon': 'ðŸ§ª', 'keywords': 'tdd, testing, unittest, pytest, automation'},
            {'name': 'Data Structures & Algorithms', 'description': 'Arrays, trees, graphs, sorting, searching, complexity', 'icon': 'ðŸ“', 'keywords': 'dsa, algorithms, complexity, leetcode, coding'},
            {'name': 'Computer Science Fundamentals', 'description': 'OS, networks, compilers, theory of computation', 'icon': 'ðŸ’»', 'keywords': 'cs, fundamentals, os, networks, theory'},
            {'name': 'Linux Administration', 'description': 'Shell scripting, system administration, permissions, services', 'icon': 'ðŸ§', 'keywords': 'linux, bash, shell, sysadmin, ubuntu'},
            {'name': 'Bash Scripting', 'description': 'Shell scripting, automation, text processing, DevOps', 'icon': 'ðŸ“œ', 'keywords': 'bash, shell, scripting, automation, linux'},
            # 51-60
            {'name': 'Terraform', 'description': 'Infrastructure as Code, cloud provisioning, modules', 'icon': 'ðŸ—ï¸', 'keywords': 'terraform, iac, cloud, provisioning, hcl'},
            {'name': 'Ansible', 'description': 'Configuration management, playbooks, automation', 'icon': 'ðŸ”§', 'keywords': 'ansible, automation, configuration, playbooks'},
            {'name': 'Elasticsearch', 'description': 'Search engine, full-text search, analytics, logging', 'icon': 'ðŸ”', 'keywords': 'elasticsearch, search, elk, logging, kibana'},
            {'name': 'Apache Kafka', 'description': 'Streaming platform, message queues, real-time data', 'icon': 'ðŸ“¨', 'keywords': 'kafka, streaming, messages, realtime, events'},
            {'name': 'RabbitMQ', 'description': 'Message broker, queues, pub/sub, async communication', 'icon': 'ðŸ°', 'keywords': 'rabbitmq, messaging, queue, broker, amqp'},
            {'name': 'Natural Language Processing', 'description': 'Text analysis, sentiment, transformers, chatbots', 'icon': 'ðŸ’¬', 'keywords': 'nlp, transformers, bert, text, sentiment'},
            {'name': 'Computer Vision', 'description': 'Image processing, object detection, CNNs, OpenCV', 'icon': 'ðŸ‘ï¸', 'keywords': 'cv, opencv, cnn, detection, image'},
            {'name': 'Deep Learning', 'description': 'Neural networks, CNNs, RNNs, transformers, GPUs', 'icon': 'ðŸ§¬', 'keywords': 'deeplearning, neural, cnn, rnn, gpu'},
            {'name': 'TensorFlow', 'description': 'ML framework, model building, training, deployment', 'icon': 'ðŸ”¶', 'keywords': 'tensorflow, ml, keras, models, training'},
            {'name': 'PyTorch', 'description': 'Deep learning framework, dynamic graphs, research', 'icon': 'ðŸ”¥', 'keywords': 'pytorch, deeplearning, neural, research, gpu'},
            # 61-70
            {'name': 'Big Data Engineering', 'description': 'Hadoop, Spark, data pipelines, distributed systems', 'icon': 'ðŸ“Š', 'keywords': 'bigdata, hadoop, spark, etl, pipelines'},
            {'name': 'Apache Spark', 'description': 'Distributed computing, data processing, MLlib', 'icon': 'âš¡', 'keywords': 'spark, distributed, bigdata, processing, scala'},
            {'name': 'Data Engineering', 'description': 'ETL pipelines, data warehousing, Airflow, dbt', 'icon': 'ðŸ”§', 'keywords': 'dataeng, etl, airflow, warehouse, pipelines'},
            {'name': 'Power BI', 'description': 'Business intelligence, dashboards, data visualization', 'icon': 'ðŸ“ˆ', 'keywords': 'powerbi, bi, dashboards, visualization, microsoft'},
            {'name': 'Tableau', 'description': 'Data visualization, analytics, storytelling, dashboards', 'icon': 'ðŸ“Š', 'keywords': 'tableau, visualization, analytics, dashboards'},
            {'name': 'Excel Advanced', 'description': 'Advanced formulas, macros, VBA, data analysis', 'icon': 'ðŸ“—', 'keywords': 'excel, formulas, vba, macros, analysis'},
            {'name': 'R Programming', 'description': 'Statistical computing, data analysis, ggplot2, Shiny', 'icon': 'ðŸ“Š', 'keywords': 'r, statistics, ggplot, shiny, analysis'},
            {'name': 'Statistics & Probability', 'description': 'Statistical inference, hypothesis testing, distributions', 'icon': 'ðŸ“', 'keywords': 'statistics, probability, inference, testing'},
            {'name': 'A/B Testing', 'description': 'Experimentation, hypothesis testing, metrics, analytics', 'icon': 'ðŸ§ª', 'keywords': 'abtesting, experiments, metrics, analytics'},
            {'name': 'Product Analytics', 'description': 'User behavior, metrics, funnels, retention, growth', 'icon': 'ðŸ“±', 'keywords': 'analytics, product, metrics, growth, users'},
            # 71-80
            {'name': 'UI/UX Design', 'description': 'User experience, interface design, prototyping, usability', 'icon': 'ðŸŽ¨', 'keywords': 'uiux, design, figma, usability, prototype'},
            {'name': 'Figma Design', 'description': 'Design tool, prototyping, collaboration, components', 'icon': 'ðŸŽ¨', 'keywords': 'figma, design, prototype, ui, collaboration'},
            {'name': 'Frontend Performance', 'description': 'Optimization, lazy loading, caching, Core Web Vitals', 'icon': 'âš¡', 'keywords': 'performance, optimization, webvitals, speed'},
            {'name': 'Web Accessibility', 'description': 'WCAG, ARIA, inclusive design, screen readers', 'icon': 'â™¿', 'keywords': 'a11y, accessibility, wcag, aria, inclusive'},
            {'name': 'Progressive Web Apps', 'description': 'PWA, service workers, offline-first, app-like experience', 'icon': 'ðŸ“±', 'keywords': 'pwa, serviceworker, offline, manifest'},
            {'name': 'WebAssembly', 'description': 'High-performance web code, Rust/C++ to web, gaming', 'icon': 'âš™ï¸', 'keywords': 'wasm, webassembly, performance, rust, binary'},
            {'name': 'Three.js & WebGL', 'description': '3D graphics, rendering, animations, game development', 'icon': 'ðŸŽ®', 'keywords': 'threejs, webgl, 3d, graphics, rendering'},
            {'name': 'Game Development', 'description': 'Unity, Unreal, game design, physics, multiplayer', 'icon': 'ðŸŽ®', 'keywords': 'gamedev, unity, unreal, gaming, physics'},
            {'name': 'Unity 3D', 'description': 'Game engine, C# scripting, physics, AR/VR', 'icon': 'ðŸŽ®', 'keywords': 'unity, gamedev, csharp, 3d, arvr'},
            {'name': 'Unreal Engine', 'description': 'AAA game development, Blueprints, C++, graphics', 'icon': 'ðŸŽ®', 'keywords': 'unreal, gamedev, cpp, blueprints, graphics'},
            # 81-90
            {'name': 'Augmented Reality', 'description': 'AR development, ARKit, ARCore, spatial computing', 'icon': 'ðŸ¥½', 'keywords': 'ar, arkit, arcore, spatial, reality'},
            {'name': 'Virtual Reality', 'description': 'VR development, Unity, Oculus, immersive experiences', 'icon': 'ðŸ¥½', 'keywords': 'vr, oculus, unity, immersive, reality'},
            {'name': 'IoT Development', 'description': 'Internet of Things, sensors, Arduino, Raspberry Pi, MQTT', 'icon': 'ðŸ“¡', 'keywords': 'iot, sensors, arduino, raspberrypi, mqtt'},
            {'name': 'Embedded Systems', 'description': 'Microcontrollers, real-time systems, firmware, C/C++', 'icon': 'ðŸ”Œ', 'keywords': 'embedded, microcontroller, firmware, realtime'},
            {'name': 'Robotics', 'description': 'Robot programming, ROS, sensors, automation, AI', 'icon': 'ðŸ¤–', 'keywords': 'robotics, ros, automation, sensors, ai'},
            {'name': 'Ethical Hacking', 'description': 'Penetration testing, vulnerability assessment, Kali Linux', 'icon': 'ðŸ‘¨â€ðŸ’»', 'keywords': 'hacking, pentest, security, kali, vulnerabilities'},
            {'name': 'Network Security', 'description': 'Firewalls, VPNs, intrusion detection, protocols', 'icon': 'ðŸ›¡ï¸', 'keywords': 'network, security, firewall, vpn, ids'},
            {'name': 'Cloud Security', 'description': 'Security in cloud, IAM, encryption, compliance', 'icon': 'ðŸ”', 'keywords': 'cloudsecurity, iam, encryption, compliance'},
            {'name': 'Cryptography', 'description': 'Encryption algorithms, PKI, hashing, SSL/TLS', 'icon': 'ðŸ”’', 'keywords': 'cryptography, encryption, ssl, hashing, pki'},
            {'name': 'GDPR & Compliance', 'description': 'Data privacy, regulations, GDPR, CCPA, compliance', 'icon': 'ðŸ“‹', 'keywords': 'gdpr, privacy, compliance, regulations, data'},
            # 91-100
            {'name': 'Quantum Computing', 'description': 'Quantum algorithms, Qiskit, quantum programming', 'icon': 'âš›ï¸', 'keywords': 'quantum, qiskit, qubits, algorithms, computing'},
            {'name': 'Edge Computing', 'description': 'Edge devices, distributed computing, low latency', 'icon': 'ðŸ“', 'keywords': 'edge, distributed, latency, iot, computing'},
            {'name': 'Serverless Architecture', 'description': 'FaaS, Lambda, serverless patterns, event-driven', 'icon': 'âš¡', 'keywords': 'serverless, lambda, faas, events, cloud'},
            {'name': 'GraphQL API Development', 'description': 'Schema design, resolvers, subscriptions, federation', 'icon': 'ðŸ”·', 'keywords': 'graphql, api, schema, resolvers, apollo'},
            {'name': 'gRPC', 'description': 'High-performance RPC, Protocol Buffers, streaming', 'icon': 'âš¡', 'keywords': 'grpc, rpc, protobuf, streaming, api'},
            {'name': 'WebSockets & Real-time', 'description': 'Real-time communication, Socket.io, WebRTC, streaming', 'icon': 'ðŸ”„', 'keywords': 'websockets, realtime, socketio, webrtc'},
            {'name': 'Content Management Systems', 'description': 'WordPress, Drupal, headless CMS, content delivery', 'icon': 'ðŸ“', 'keywords': 'cms, wordpress, drupal, contentful, strapi'},
            {'name': 'E-commerce Development', 'description': 'Online stores, Shopify, WooCommerce, payment gateways', 'icon': 'ðŸ›’', 'keywords': 'ecommerce, shopify, woocommerce, payments'},
            {'name': 'SEO & Digital Marketing', 'description': 'Search optimization, keywords, analytics, content strategy', 'icon': 'ðŸ“ˆ', 'keywords': 'seo, marketing, google, keywords, analytics'},
            {'name': 'Technical Writing', 'description': 'Documentation, API docs, tutorials, technical communication', 'icon': 'âœï¸', 'keywords': 'documentation, writing, technical, docs, guides'}
        ]
        
        for domain_data in domains_data:
            domain = Domain(
                name=domain_data['name'],
                description=domain_data['description'],
                icon=domain_data['icon'],
                keywords=domain_data['keywords']
            )
            db.session.add(domain)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Domain seed skipped due to DB error: {e}")

# Clear the transient in-memory store to avoid accidental use
users = {}


def is_strong_password(pw):
    errors = []
    if len(pw) < 8:
        errors.append('At least 8 characters')
    if not re.search(r'\d', pw):
        errors.append('At least one digit')
    if not re.search(r'[A-Z]', pw):
        errors.append('At least one uppercase letter')
    if not re.search(r'[^A-Za-z0-9]', pw):
        errors.append('At least one symbol')
    return (len(errors) == 0, errors)


def is_valid_email(email):
    # A reasonably strict but practical email regex (not full RFC 5322)
    pattern = r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None


def _password_matches(stored_password, candidate_password):
    """Return (is_match, was_legacy_plain_text)."""
    if not stored_password:
        return False, False

    stored = str(stored_password)
    # Werkzeug hashes in this app are prefixed by scheme, for example scrypt:/pbkdf2:.
    if stored.startswith('scrypt:') or stored.startswith('pbkdf2:'):
        try:
            return check_password_hash(stored, candidate_password), False
        except Exception:
            return False, False

    # Backward compatibility for legacy/plain-text rows.
    return secrets.compare_digest(stored, str(candidate_password)), True


def _verify_user_password(user, candidate_password):
    """Verify user password and transparently upgrade legacy plain-text storage."""
    is_match, was_legacy = _password_matches(user.password_hash, candidate_password)
    if is_match and was_legacy:
        user.password_hash = generate_password_hash(candidate_password)
        return True, True
    return is_match, False


def _pending_registration_is_expired(pending):
    if not pending or not pending.token_created_at:
        return True
    elapsed = (datetime.datetime.utcnow() - pending.token_created_at).total_seconds()
    return elapsed > int(app.config.get('EMAIL_VERIFICATION_EXPIRY_SECONDS', 900))


def _email_verification_expiry_minutes():
    expiry_seconds = max(int(app.config.get('EMAIL_VERIFICATION_EXPIRY_SECONDS', 900)), 60)
    return max(1, expiry_seconds // 60)


def _ensure_pending_registration_table():
    """Ensure pending registration table exists before verification queries."""
    try:
        PendingRegistration.__table__.create(bind=db.engine, checkfirst=True)
        return True, ''
    except Exception as exc:
        app.logger.exception(f'PendingRegistration table ensure failed: {exc}')
        return False, str(exc)


def require_admin():
    if not session.get('user'):
        flash('Please log in to continue.', 'error')
        return None, redirect(url_for('login'))
    user = User.query.filter_by(username=session.get('user')).first()
    if not user or user.role != 'admin':
        flash('Admin access required.', 'error')
        return user, redirect(url_for('dashboard'))
    return user, None


def _send_email(to_addr, subject, body):
    """Sends email synchronously. Returns True on success."""
    ok, _ = _send_email_detailed(to_addr, subject, body)
    return ok


def _email_provider():
    provider = str(app.config.get('EMAIL_PROVIDER') or os.environ.get('EMAIL_PROVIDER') or '').strip().lower()
    if provider:
        return provider
    resend_api_key = (app.config.get('RESEND_API_KEY') or os.environ.get('RESEND_API_KEY') or '').strip()
    return 'resend' if resend_api_key else 'nodemailer'


def _env_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _send_email_via_resend(to_addr, subject, body, is_html=False, plain_text=None):
    api_key = (app.config.get('RESEND_API_KEY') or os.environ.get('RESEND_API_KEY') or '').strip()
    api_url = str(app.config.get('RESEND_API_URL') or os.environ.get('RESEND_API_URL') or 'https://api.resend.com/emails').strip()
    from_addr = str(app.config.get('EMAIL_FROM') or os.environ.get('EMAIL_FROM') or '').strip()

    missing = []
    if not api_key:
        missing.append('RESEND_API_KEY')
    if not from_addr:
        missing.append('EMAIL_FROM')
    if missing:
        msg = 'Resend not fully configured. Missing: ' + ', '.join(missing)
        app.logger.warning(msg)
        print(f'WARN: {msg}')
        return False, msg

    payload = {
        'from': f'SkillForge <{from_addr}>',
        'to': [to_addr],
        'subject': subject,
    }
    if is_html:
        payload['html'] = body
        if plain_text:
            payload['text'] = plain_text
    else:
        payload['text'] = plain_text or body

    request_body = json.dumps(payload).encode('utf-8')
    request_obj = urllib.request.Request(
        api_url,
        data=request_body,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST'
    )

    print(f'Sending email to: {to_addr}')
    print(f'  Subject: {subject}')
    print(f'  Via: resend ({api_url})')

    try:
        with urllib.request.urlopen(request_obj, timeout=15) as response:
            response_body = response.read().decode('utf-8', errors='replace')
            if 200 <= response.status < 300:
                app.logger.info(f'Email sent to {to_addr}: {subject}')
                print(f'OK: Email sent to {to_addr}: {subject}')
                return True, ''
            error_msg = f'Resend returned HTTP {response.status}: {response_body}'
            app.logger.error(error_msg)
            print(f'ERROR: {error_msg}')
            return False, error_msg
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode('utf-8', errors='replace')
        error_msg = f'Resend HTTP {exc.code}: {response_body}'
        app.logger.error(error_msg)
        print(f'ERROR: {error_msg}')
        return False, error_msg
    except urllib.error.URLError as exc:
        error_msg = f'Resend connection failed: {exc.reason}'
        app.logger.error(error_msg)
        print(f'ERROR: {error_msg}')
        return False, error_msg
    except Exception as exc:
        error_msg = f'Resend send failed: {exc}'
        app.logger.error(error_msg)
        print(f'ERROR: {error_msg}')
        return False, error_msg


def _send_email_via_nodemailer(to_addr, subject, body, is_html=False, plain_text=None):
    """Sends email synchronously via NodeMailer. Returns (success, error_message)."""
    host = app.config.get('NODEMAILER_HOST') or os.environ.get('NODEMAILER_HOST') or app.config.get('SMTP_HOST') or os.environ.get('SMTP_HOST')
    port_raw = app.config.get('NODEMAILER_PORT') or os.environ.get('NODEMAILER_PORT') or app.config.get('SMTP_PORT') or os.environ.get('SMTP_PORT') or '587'
    user = app.config.get('NODEMAILER_USER') or os.environ.get('NODEMAILER_USER') or app.config.get('SMTP_USER') or os.environ.get('SMTP_USER')
    password = app.config.get('NODEMAILER_PASS') or os.environ.get('NODEMAILER_PASS') or app.config.get('SMTP_PASS') or os.environ.get('SMTP_PASS')
    from_addr = app.config.get('EMAIL_FROM') or os.environ.get('EMAIL_FROM') or user
    allow_insecure_raw = app.config.get('NODEMAILER_ALLOW_INSECURE')
    if allow_insecure_raw is None:
        allow_insecure_raw = app.config.get('SMTP_ALLOW_INSECURE') or os.environ.get('SMTP_ALLOW_INSECURE') or 'false'

    use_auth_raw = app.config.get('NODEMAILER_USE_AUTH')
    if use_auth_raw is None:
        use_auth_raw = app.config.get('SMTP_USE_AUTH')

    node_bin = str(app.config.get('NODE_BIN') or os.environ.get('NODE_BIN') or 'node').strip()
    script_path = str(
        app.config.get('NODEMAILER_SCRIPT')
        or os.environ.get('NODEMAILER_SCRIPT')
        or os.path.join(os.path.dirname(__file__), 'email_sender.js')
    ).strip()

    host = str(host).strip() if host is not None else ''
    user = str(user).strip() if user is not None else ''
    password = str(password).strip() if password is not None else ''
    from_addr = str(from_addr).strip() if from_addr is not None else ''

    try:
        port = int(str(port_raw).strip())
    except Exception:
        app.logger.warning(f'Invalid NODEMAILER_PORT value: {port_raw!r}; falling back to 587')
        port = 587

    allow_insecure = _env_bool(allow_insecure_raw, default=False)
    use_auth = _env_bool(use_auth_raw, default=True)

    missing = []
    if not host:
        missing.append('NODEMAILER_HOST')
    if not from_addr:
        missing.append('EMAIL_FROM')
    if use_auth and not user:
        missing.append('NODEMAILER_USER')
    if use_auth and not password:
        missing.append('NODEMAILER_PASS')

    if missing:
        msg = 'NodeMailer not fully configured. Missing: ' + ', '.join(missing)
        app.logger.warning(msg)
        print(f'WARN: {msg}')
        return False, msg

    print(f'Sending email to: {to_addr}')
    print(f'  Subject: {subject}')
    print(f'  Via: nodemailer ({host}:{port}, auth={use_auth}, allow_insecure={allow_insecure})')

    payload = {
        'transport': {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'from': from_addr,
            'allowInsecure': allow_insecure,
            'useAuth': use_auth,
        },
        'message': {
            'to': to_addr,
            'subject': subject,
            'html': body if is_html else '',
            'text': plain_text or (body if not is_html else ''),
        }
    }

    try:
        proc = subprocess.run(
            [node_bin, script_path],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except FileNotFoundError:
        error_msg = f'Node executable not found: {node_bin}'
        app.logger.error(error_msg)
        print(f'ERROR: {error_msg}')
        return False, error_msg
    except subprocess.TimeoutExpired:
        error_msg = 'NodeMailer send timed out after 45 seconds.'
        app.logger.error(error_msg)
        print(f'ERROR: {error_msg}')
        return False, error_msg
    except Exception as exc:
        error_msg = f'NodeMailer execution failed: {exc}'
        app.logger.error(error_msg)
        print(f'ERROR: {error_msg}')
        return False, error_msg

    stdout = (proc.stdout or '').strip()
    stderr = (proc.stderr or '').strip()

    if proc.returncode != 0:
        parsed_error = ''
        if stdout:
            try:
                failed_payload = json.loads(stdout)
                parsed_error = str(failed_payload.get('error') or '').strip()
            except Exception:
                parsed_error = ''
        error_msg = parsed_error or stderr or stdout or f'NodeMailer exited with code {proc.returncode}'
        app.logger.error(f'Failed to send email to {to_addr}: {error_msg}')
        print(f'ERROR: Failed to send email to {to_addr}: {error_msg}')
        return False, error_msg

    if stderr:
        app.logger.warning(f'NodeMailer stderr for {to_addr}: {stderr}')

    parsed = {}
    if stdout:
        try:
            parsed = json.loads(stdout)
        except Exception:
            parsed = {'ok': False, 'error': f'Invalid NodeMailer response: {stdout}'}

    if parsed.get('ok'):
        msg = f'Email sent to {to_addr}: {subject}'
        app.logger.info(msg)
        print(f'OK: {msg}')
        return True, ''

    error_msg = parsed.get('error') or stderr or 'Unknown NodeMailer failure.'
    app.logger.error(f'Failed to send email to {to_addr}: {error_msg}')
    print(f'ERROR: Failed to send email to {to_addr}: {error_msg}')
    return False, error_msg


def _send_email_detailed(to_addr, subject, body, is_html=False, plain_text=None):
    """Sends email synchronously. Returns (success, error_message)."""
    provider = _email_provider()
    if provider == 'resend':
        return _send_email_via_resend(to_addr, subject, body, is_html=is_html, plain_text=plain_text)

    nodemailer_ok, nodemailer_err = _send_email_via_nodemailer(
        to_addr,
        subject,
        body,
        is_html=is_html,
        plain_text=plain_text,
    )
    if nodemailer_ok:
        return True, ''

    # Production fallback: if NodeMailer fails and Resend is configured, try Resend automatically.
    resend_api_key = (app.config.get('RESEND_API_KEY') or os.environ.get('RESEND_API_KEY') or '').strip()
    if resend_api_key:
        resend_ok, resend_err = _send_email_via_resend(
            to_addr,
            subject,
            body,
            is_html=is_html,
            plain_text=plain_text,
        )
        if resend_ok:
            app.logger.warning('NodeMailer failed but Resend fallback succeeded.')
            return True, ''
        combined_error = f'NodeMailer failed: {nodemailer_err}; Resend fallback failed: {resend_err}'
        return False, combined_error

    return False, nodemailer_err


def send_email_async(to_addr, subject, body, is_html=False, plain_text=None):
    """Fire-and-forget email send in a background thread."""
    thread = threading.Thread(target=_send_email_detailed, args=(to_addr, subject, body, is_html, plain_text), daemon=True)
    thread.start()


def _normalized_public_base_url(raw_base_url):
    """Return a safe public base URL or an empty string when value is local/invalid."""
    candidate = str(raw_base_url or '').strip()
    if not candidate:
        return ''

    if '<' in candidate or '>' in candidate:
        return ''

    parsed = urllib.parse.urlparse(candidate)
    if not parsed.scheme:
        parsed = urllib.parse.urlparse('https://' + candidate)

    host = (parsed.hostname or '').strip().lower()
    if not host:
        return ''

    # Prevent generating unusable verification links in production emails.
    if host in ('localhost', '127.0.0.1', '0.0.0.0') or host.endswith('.local'):
        return ''

    return parsed._replace(path='', params='', query='', fragment='').geturl().rstrip('/')


def _send_verification_email_for_pending(pending):
    """Send verification email for a pending registration row."""
    configured_base_url = app.config.get('SERVER_BASE_URL')
    safe_base_url = _normalized_public_base_url(configured_base_url)
    if safe_base_url:
        verification_link = safe_base_url + url_for('verify_email', token=pending.token)
    else:
        if configured_base_url:
            app.logger.warning(
                f'Ignoring non-public SERVER_BASE_URL for verification link: {configured_base_url!r}'
            )
        verification_link = url_for('verify_email', token=pending.token, _external=True)

    subject = 'Verify your email - SkillForge'
    plain_text = f"""Hello {pending.username},

Please verify your email to complete your SkillForge registration.

    Click the link below within {_email_verification_expiry_minutes()} minutes:
{verification_link}

If you did not request this account, you can ignore this email.

Best regards,
The SkillForge Team
"""
    body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <style>
        body {{ font-family: Arial, sans-serif; background: #f8fafc; color: #0f172a; }}
        .card {{ max-width: 600px; margin: 24px auto; background: #ffffff; border-radius: 12px; padding: 32px; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08); }}
        .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; }}
        .muted {{ color: #64748b; font-size: 14px; }}
    </style>
</head>
<body>
    <div class=\"card\">
        <h2>Verify your email</h2>
        <p>Hello {pending.username},</p>
        <p>Please verify your email to complete your SkillForge registration.</p>
        <p><a class=\"button\" href=\"{verification_link}\">Verify Email</a></p>
        <p class=\"muted\">This link expires in {_email_verification_expiry_minutes()} minutes.</p>
        <p class=\"muted\">If you did not request this account, you can ignore this email.</p>
    </div>
</body>
</html>
"""

    return _send_email_detailed(
        pending.email,
        subject,
        body,
        is_html=True,
        plain_text=plain_text
    )


def _send_verification_email_async_for_pending(pending):
    """Fire-and-forget verification email send so signup requests do not time out."""
    pending_username = str(getattr(pending, 'username', '') or '')
    pending_email = str(getattr(pending, 'email', '') or '')
    pending_token = str(getattr(pending, 'token', '') or '')

    if not pending_email or not pending_token:
        app.logger.warning('Skipping async verification send due to missing pending email/token.')
        return

    class PendingEmailPayload:
        def __init__(self, username, email, token):
            self.username = username
            self.email = email
            self.token = token

    payload = PendingEmailPayload(pending_username, pending_email, pending_token)

    def _worker():
        with app.app_context():
            try:
                sent, err = _send_verification_email_for_pending(payload)
                if sent:
                    app.logger.info(f'Async verification email sent to {pending_email}')
                else:
                    app.logger.error(f'Async verification email failed for {pending_email}: {err}')
            except Exception as exc:
                app.logger.exception(f'Async verification email exception for {pending_email}: {exc}')

    threading.Thread(target=_worker, daemon=True).start()




@app.route('/')
def home():
    return render_template('welcome.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # CSRF check
            token = request.form.get('csrf_token')
            if not token or token != session.get('csrf_token'):
                flash('Form tampered or session expired. Please try again.', 'error')
                return redirect(url_for('signup'))

            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')

            if not username or not email or not password or not confirm:
                flash('Please fill in all fields.', 'error')
                return redirect(url_for('signup'))

            if not is_valid_email(email):
                flash('Email address is invalid. Use format name@example.com', 'error')
                return redirect(url_for('signup'))

            existing_username_user = User.query.filter(
                func.lower(User.username) == username.lower()
            ).first()
            if existing_username_user:
                flash('Username already registered.', 'error')
                return redirect(url_for('signup'))

            if password != confirm:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('signup'))

            ok, errors = is_strong_password(password)
            if not ok:
                flash('Password does not meet rules: ' + '; '.join(errors), 'error')
                return redirect(url_for('signup'))

            if User.query.filter(func.lower(User.email) == email.lower()).first():
                flash('Email already registered.', 'error')
                return redirect(url_for('signup'))

            # When verification is disabled, create account immediately and skip email flow.
            if not app.config.get('REQUIRE_EMAIL_VERIFICATION', True):
                stale_pending = PendingRegistration.query.filter(
                    or_(
                        func.lower(PendingRegistration.username) == username.lower(),
                        func.lower(PendingRegistration.email) == email.lower()
                    )
                ).all()
                for row in stale_pending:
                    db.session.delete(row)

                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password),
                    created_at=datetime.datetime.utcnow(),
                    email_verified=True
                )
                db.session.add(user)
                db.session.commit()
                session.pop('csrf_token', None)
                flash('Registration successful. You can now log in.', 'success')
                return redirect(url_for('login'))

            table_ok, table_err = _ensure_pending_registration_table()
            if not table_ok:
                flash(f'Email verification setup error: {table_err}', 'error')
                return redirect(url_for('signup'))

            # Replace any existing pending row for this username/email with a fresh token.
            pending_rows = PendingRegistration.query.filter(
                or_(
                    func.lower(PendingRegistration.username) == username.lower(),
                    func.lower(PendingRegistration.email) == email.lower()
                )
            ).all()
            for row in pending_rows:
                db.session.delete(row)

            verification_token = secrets.token_urlsafe(32)
            pending = PendingRegistration(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                token=verification_token,
                token_created_at=datetime.datetime.utcnow()
            )
            db.session.add(pending)
            db.session.commit()

            session.pop('csrf_token', None)
            _send_verification_email_async_for_pending(pending)
            flash('Registration is pending email verification. Verification email is being sent now; please check inbox/spam in a minute.', 'info')
            flash(f'Please verify your email within {_email_verification_expiry_minutes()} minutes to activate your account. You can log in only after verification.', 'warning')
            return redirect(url_for('login'))
        except Exception as exc:
            db.session.rollback()
            app.logger.exception(f'Signup failed: {exc}')
            flash('Unable to process signup right now. Please try again.', 'error')
            return redirect(url_for('signup'))

    # GET: set CSRF
    csrf_token = secrets.token_urlsafe(16)
    session['csrf_token'] = csrf_token
    return render_template('signup.html', csrf_token=csrf_token) 


@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    try:
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            flash('Form tampered or session expired. Please try again.', 'error')
            return redirect(url_for('login'))

        if not app.config.get('REQUIRE_EMAIL_VERIFICATION', True):
            flash('Email verification is currently disabled. You can log in directly.', 'info')
            return redirect(url_for('login'))

        table_ok, table_err = _ensure_pending_registration_table()
        if not table_ok:
            flash(f'Email verification setup error: {table_err}', 'error')
            return redirect(url_for('login'))

        identifier = request.form.get('identifier', '').strip()
        if not identifier:
            flash('Enter your username or email to resend verification.', 'warning')
            return redirect(url_for('login'))

        normalized_identifier = identifier.lower()
        identifier_looks_like_email = '@' in normalized_identifier

        if identifier_looks_like_email:
            pending = PendingRegistration.query.filter(
                func.lower(PendingRegistration.email) == normalized_identifier
            ).first()
            if not pending:
                pending = PendingRegistration.query.filter(
                    PendingRegistration.username == identifier
                ).first()
            if not pending:
                pending = PendingRegistration.query.filter(
                    func.lower(PendingRegistration.username) == normalized_identifier
                ).first()
        else:
            pending = PendingRegistration.query.filter(
                PendingRegistration.username == identifier
            ).first()
            if not pending:
                pending = PendingRegistration.query.filter(
                    func.lower(PendingRegistration.email) == normalized_identifier
                ).first()
            if not pending:
                pending = PendingRegistration.query.filter(
                    func.lower(PendingRegistration.username) == normalized_identifier
                ).first()

        if not pending:
            existing_user = User.query.filter(
                or_(
                    func.lower(User.username) == normalized_identifier,
                    func.lower(User.email) == normalized_identifier
                )
            ).first()
            if existing_user and existing_user.email_verified:
                flash('This account is already verified. Please log in.', 'info')
            else:
                flash('No pending verification found. Please sign up first.', 'warning')
            return redirect(url_for('login'))

        if _pending_registration_is_expired(pending):
            db.session.delete(pending)
            db.session.commit()
            flash('Your verification request expired. Please sign up again.', 'warning')
            return redirect(url_for('signup'))

        pending.token = secrets.token_urlsafe(32)
        pending.token_created_at = datetime.datetime.utcnow()
        db.session.commit()

        _send_verification_email_async_for_pending(pending)
        flash('A new verification email is being sent. Please check your inbox/spam shortly.', 'success')
        return redirect(url_for('login'))
    except Exception as exc:
        db.session.rollback()
        app.logger.exception(f'Resend verification failed: {exc}')
        flash('Unable to process resend verification right now. Please try again.', 'error')
        return redirect(url_for('login'))


@app.route('/admin/test-email', methods=['GET', 'POST'])
def admin_test_email():
    """Simple admin page to send a test email and report status inline."""
    msg = None
    status = ''
    init_to = os.environ.get('EMAIL_FROM', '') or os.environ.get('NODEMAILER_USER', '') or os.environ.get('SMTP_USER', '')
    if request.method == 'POST':
        to = request.form.get('to_email', '').strip()
        if not to:
            msg = 'Please provide an email address to send to.'
            status = 'warning'
        else:
            subject = 'SkillForge Email Test'
            body = f'This is a test message sent at {datetime.datetime.utcnow().isoformat()} UTC to verify email provider configuration.'
            try:
                sent, err = _send_email_detailed(to, subject, body)
                if sent:
                    msg = f'Test email sent to {to}.'
                    status = 'success'
                else:
                    msg = f'Failed to send test email to {to}. Error: {err}'
                    status = 'warning'
            except Exception as exc:
                app.logger.error(f'Error sending test email to {to}: {exc}')
                msg = f'Exception while sending: {exc}'
                status = 'warning'
    # set a fresh CSRF token for the admin form render
    csrf_token = secrets.token_urlsafe(16)
    session['csrf_token'] = csrf_token
    return render_template('admin_test_email.html', test_message=msg, test_status=status, default_to=init_to, csrf_token=csrf_token)


@app.route('/dashboard')
def dashboard():
    if not session.get('user'):
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session.get('user')).first()
    return render_template('dashboard.html', user=user) 


@app.route('/api/dashboard/metrics')
def dashboard_metrics():
    now = datetime.datetime.utcnow()
    total_users = User.query.count()
    signups_today = User.query.filter(User.created_at > now - datetime.timedelta(days=1)).count()
    last7 = []
    for i in range(6, -1, -1):
        day = now - datetime.timedelta(days=i)
        start = datetime.datetime(day.year, day.month, day.day)
        end = start + datetime.timedelta(days=1)
        count = User.query.filter(User.created_at >= start, User.created_at < end).count()
        last7.append({'date': day.strftime('%Y-%m-%d'), 'count': count})
    revenue = total_users * 10  # sample placeholder
    devices = {'desktop': 60, 'mobile': 35, 'tablet': 5}
    return jsonify({'total_users': total_users, 'signups_today': signups_today, 'last7': last7, 'revenue': revenue, 'devices': devices})

@app.route('/api/user/dashboard-stats')
def user_dashboard_stats():
    """Get current user's dashboard statistics"""
    if not session.get('user_id'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session.get('user_id')
    now = datetime.datetime.utcnow()
    
    # 1. Count total domains enrolled
    total_domains = DomainEnrollment.query.filter_by(user_id=user_id).count()
    
    # 2. Count domains enrolled this month
    month_start = datetime.datetime(now.year, now.month, 1)
    domains_this_month = DomainEnrollment.query.filter(
        DomainEnrollment.user_id == user_id,
        DomainEnrollment.created_at >= month_start
    ).count()
    
    # 3. Count challenges/quizzes completed
    challenges_completed = DomainCourseQuizAttempt.query.filter(
        DomainCourseQuizAttempt.user_id == user_id,
        DomainCourseQuizAttempt.completed_at != None
    ).count()
    
    # 4. Get overall completion percentage (average of all domain progress)
    domain_enrollments = DomainEnrollment.query.filter_by(user_id=user_id).all()
    if domain_enrollments:
        quiz_attempts = DomainCourseQuizAttempt.query.filter(
            DomainCourseQuizAttempt.user_id == user_id
        ).all()
        
        # Calculate completion based on passed quizzes
        if quiz_attempts:
            passed_quizzes = sum(1 for q in quiz_attempts if q.passed)
            completion_percent = int((passed_quizzes / len(quiz_attempts)) * 100) if quiz_attempts else 0
        else:
            completion_percent = 0
    else:
        completion_percent = 0
    
    # 5. Count certificates earned
    certificates_earned = DomainCertificate.query.filter_by(user_id=user_id, is_sample=False).count()
    
    # 6. Count AI recommendations (for now, return a fixed value based on user's enrollments)
    ai_recommendations = min(len(domain_enrollments) * 2, 10) if domain_enrollments else 0
    
    return jsonify({
        'domains_enrolled': total_domains,
        'domains_this_month': domains_this_month,
        'challenges_completed': challenges_completed,
        'completion_percent': completion_percent,
        'certificates_earned': certificates_earned,
        'ai_recommendations': ai_recommendations
    })

@app.route('/api/user/enrolled-domains')
def user_enrolled_domains():
    """Get user's enrolled domains with their selected course links and progress"""
    if not session.get('user_id'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session.get('user_id')
    
    # Get all domain enrollments for user
    enrollments = DomainEnrollment.query.filter_by(user_id=user_id).all()
    
    results = []
    for enrollment in enrollments:
        domain = Domain.query.get(enrollment.domain_id)
        if not domain:
            continue
        
        # Get progress for this domain
        progress_entries = DomainCourseProgress.query.filter_by(
            user_id=user_id,
            domain_id=enrollment.domain_id
        ).all()
        
        # Calculate completion percentage
        total_progress = 0
        if progress_entries:
            total_progress = sum(p.tutorial_minutes for p in progress_entries)
            # Max 300 minutes per course, let's say avg 150 for completion tracking
            completion_percent = min(int((total_progress / (len(progress_entries) * 150)) * 100), 100)
        else:
            completion_percent = 0
        
        # Get the preferred course link or the first available course
        if enrollment.preferred_course_link:
            # Parse the URL to get course link ID if stored in the string
            # For now, fetch the first course link for this domain
            course_link = CourseLink.query.filter_by(domain_id=enrollment.domain_id).first()
        else:
            course_link = CourseLink.query.filter_by(domain_id=enrollment.domain_id).first()
        
        # Create result object
        result = {
            'id': enrollment.id,
            'domain_id': domain.id,
            'domain_name': domain.name,
            'selected_level': enrollment.selected_level,
            'assessed_level': enrollment.assessed_level,
            'progress': completion_percent,
            'created_at': enrollment.created_at.strftime('%Y-%m-%d') if enrollment.created_at else '',
            'course_link': None
        }
        
        # Add course link if available
        if course_link:
            result['course_link'] = {
                'id': course_link.id,
                'title': course_link.title,
                'url': course_link.url,
                'source': course_link.source,
                'rating': course_link.rating
            }
        
        results.append(result)
    
    return jsonify({'domains': results})

@app.route('/api/courses')
def api_courses():
    courses = Course.query.order_by(Course.created_at.desc()).all()
    results = []
    for course in courses:
        results.append({
            'id': course.id,
            'title': course.title,
            'category': course.category,
            'instructor': course.instructor,
            'description': course.description,
            'progress': 0,
            'duration': course.duration,
            'lessons': course.lessons,
            'students': course.students,
            'rating': course.rating,
            'reviews': course.reviews,
            'thumbnail': course.thumbnail,
            'status': course.status
        })
    return jsonify({'courses': results})


@app.route('/api/domains')
def api_domains():
    """Get all learning domains"""
    ensure_domains_seeded_if_empty()
    domains = Domain.query.all()
    results = []
    for domain in domains:
        results.append({
            'id': domain.id,
            'name': domain.name,
            'description': domain.description,
            'icon': domain.icon,
            'keywords': domain.keywords
        })
    return jsonify({'domains': results})


@app.route('/api/domain/<int:domain_id>/enroll', methods=['POST'])
def api_domain_enroll(domain_id):
    """Enroll user in a domain with selected level"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    level = data.get('level')
    
    # Debug logging
    print(f"DEBUG: Received enrollment request - domain_id: {domain_id}, level: {level}, type: {type(level)}")
    print(f"DEBUG: Request data: {data}")
    
    if not level or level not in ['Zero', 'Beginner', 'Intermediate', 'Advanced']:
        return jsonify({'error': f'Invalid level: {level}. Must be one of: Zero, Beginner, Intermediate, Advanced'}), 400
    
    domain = Domain.query.get(domain_id)
    if not domain:
        return jsonify({'error': 'Domain not found'}), 404
    
    # Check if already enrolled
    enrollment = DomainEnrollment.query.filter_by(
        user_id=session['user_id'],
        domain_id=domain_id
    ).first()
    
    if not enrollment:
        enrollment = DomainEnrollment(
            user_id=session['user_id'],
            domain_id=domain_id,
            selected_level=level,
            learning_phase='level-quiz'
        )
        db.session.add(enrollment)
    else:
        enrollment.selected_level = level
        enrollment.learning_phase = 'level-quiz'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'enrollment_id': enrollment.id,
        'message': f'Enrolled in {domain.name} at {level} level'
    })


@app.route('/api/domain/<int:domain_id>/level-quiz')
def api_level_quiz(domain_id):
    """Get level assessment quiz for domain"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    domain = Domain.query.get(domain_id)
    if not domain:
        return jsonify({'error': 'Domain not found'}), 404
    
    # Get user's selected level
    enrollment = DomainEnrollment.query.filter_by(
        user_id=session['user_id'],
        domain_id=domain_id
    ).first()
    
    selected_level = enrollment.selected_level if enrollment else 'Zero'

    def generate_questions_with_ai(domain_name, level_name, num_questions=10):
        """Generate questions using AI based on domain and level"""
        if not gemini_model:
            return None
        
        try:
            if level_name == 'Zero':
                prompt = f"""Generate {num_questions} survey questions for assessing a user's background in {domain_name}.

For each question, provide:
1. A clear question text
2. Exactly 3-4 multiple choice options
3. Each option should have a 'label' (the text) and 'value' (a short identifier)

Return the response as a JSON array with this format:
[
  {{
    "question": "Question text here?",
    "options": [
      {{"label": "Option 1", "value": "value1"}},
      {{"label": "Option 2", "value": "value2"}},
      {{"label": "Option 3", "value": "value3"}}
    ]
  }}
]

Make the questions focused on their experience level, goals, time commitment, and related skills."""
            else:
                difficulty = {'Beginner': 'beginner/foundational', 'Intermediate': 'intermediate/practical', 'Advanced': 'advanced/expert'}[level_name]
                prompt = f"""Generate {num_questions} multiple-choice assessment questions for {domain_name} at {difficulty} level.

For each question:
1. Create a clear, specific question testing {difficulty} knowledge
2. Provide exactly 4 options: 1 correct answer and 3 plausible incorrect answers
3. Mark the correct answer with value='correct' and incorrect ones with value='incorrect'

Return as JSON array:
[
  {{
    "question": "Question text?",
    "options": [
      {{"label": "Correct answer", "value": "correct"}},
      {{"label": "Wrong answer 1", "value": "incorrect"}},
      {{"label": "Wrong answer 2", "value": "incorrect"}},
      {{"label": "Wrong answer 3", "value": "incorrect"}}
    ]
  }}
]

Make questions practical and relevant to real-world {domain_name} scenarios."""
            
            response = gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            questions_data = json.loads(response_text)
            
            # Format questions with IDs
            formatted_questions = []
            for idx, q in enumerate(questions_data[:num_questions], 1):
                formatted_questions.append({
                    'id': idx,
                    'question': q['question'],
                    'options': q['options']
                })
            
            return formatted_questions
        except Exception as e:
            print(f"AI generation error: {e}")
            return None
    
    def build_default_quiz(domain_name, level_name):
        """Generate quiz using AI, fallback to simple questions if AI unavailable"""
        
        # Try AI generation first
        ai_questions = generate_questions_with_ai(domain_name, level_name, 10)
        
        if ai_questions:
            # AI successfully generated questions
            if level_name == 'Zero':
                return {
                    'title': f'{domain_name} - Baseline Survey',
                    'description': f'Tell us about your background with {domain_name}',
                    'type': 'survey',
                    'questions': ai_questions
                }
            else:
                return {
                    'title': f'{domain_name} - {level_name} Assessment',
                    'description': f'Test your {level_name.lower()} knowledge of {domain_name}',
                    'type': 'assessment',
                    'questions': ai_questions
                }
        
        # Fallback: Generate simple generic questions if AI is unavailable
        domain_lower = domain_name.lower()
        
        if level_name == 'Zero':
            return {
                'title': f'{domain_name} - Baseline Survey',
                'description': f'Tell us about your background with {domain_name}',
                'type': 'survey',
                'questions': [
                    {
                        'id': 1,
                        'question': f'What is your current experience level with {domain_name}?',
                        'options': [
                            {'label': 'Complete beginner - never tried', 'value': 'beginner'},
                            {'label': 'Some exposure - basic knowledge', 'value': 'some'},
                            {'label': 'Intermediate - worked on projects', 'value': 'intermediate'},
                            {'label': 'Advanced - professional experience', 'value': 'advanced'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': f'What is your primary goal with {domain_name}?',
                        'options': [
                            {'label': 'Start a new career', 'value': 'career'},
                            {'label': 'Upskill for current job', 'value': 'upskill'},
                            {'label': 'Personal projects', 'value': 'personal'},
                            {'label': 'Academic/research purposes', 'value': 'academic'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': 'How much time can you dedicate to learning weekly?',
                        'options': [
                            {'label': '1-3 hours per week', 'value': 'low'},
                            {'label': '4-7 hours per week', 'value': 'medium'},
                            {'label': '8-15 hours per week', 'value': 'high'},
                            {'label': '15+ hours per week', 'value': 'very_high'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': f'Do you have related skills that complement {domain_name}?',
                        'options': [
                            {'label': 'No related experience', 'value': 'none'},
                            {'label': 'Some programming basics', 'value': 'basic_prog'},
                            {'label': 'Strong technical foundation', 'value': 'strong_tech'},
                            {'label': 'Industry experience', 'value': 'industry'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': f'Have you used similar tools or frameworks to {domain_name}?',
                        'options': [
                            {'label': 'No - completely new to me', 'value': 'new'},
                            {'label': 'Yes - used similar tools once or twice', 'value': 'familiar'},
                            {'label': 'Yes - used similar tools regularly', 'value': 'experienced'},
                            {'label': 'Yes - expert with similar tools', 'value': 'expert_similar'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': f'What best describes your learning style for {domain_name}?',
                        'options': [
                            {'label': 'Hands-on practice and projects', 'value': 'hands_on'},
                            {'label': 'Structured courses and tutorials', 'value': 'structured'},
                            {'label': 'Reading documentation', 'value': 'reading'},
                            {'label': 'Mix of all approaches', 'value': 'mixed'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': f'Do you have any formal training related to {domain_name}?',
                        'options': [
                            {'label': 'No formal training', 'value': 'no_formal'},
                            {'label': 'Online courses', 'value': 'online'},
                            {'label': 'University/College degree', 'value': 'degree'},
                            {'label': 'Professional certification', 'value': 'cert'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': f'What is your preferred learning pace for {domain_name}?',
                        'options': [
                            {'label': 'Self-paced, no rush', 'value': 'self_paced'},
                            {'label': 'Moderate pace with deadlines', 'value': 'moderate'},
                            {'label': 'Fast-paced and intensive', 'value': 'intensive'},
                            {'label': 'Project-based milestone approach', 'value': 'project_based'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': f'Have you completed any projects using {domain_name}?',
                        'options': [
                            {'label': 'No, not yet', 'value': 'no_projects'},
                            {'label': 'Yes, 1-2 small projects', 'value': 'small_projects'},
                            {'label': 'Yes, 3-5 projects', 'value': 'medium_projects'},
                            {'label': 'Yes, many projects (5+)', 'value': 'many_projects'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': f'What is your main challenge in learning {domain_name}?',
                        'options': [
                            {'label': 'Understanding concepts', 'value': 'concepts'},
                            {'label': 'Lack of practice opportunities', 'value': 'practice'},
                            {'label': 'Keeping up with updates', 'value': 'updates'},
                            {'label': 'Connecting theory to real-world use', 'value': 'application'}
                        ]
                    }
                ]
            }

        # Generate domain-specific questions based on domain name keywords
        if level_name == 'Beginner':
            # Customize questions based on domain type
            if 'programming' in domain_lower or 'python' in domain_lower or 'java' in domain_lower or 'javascript' in domain_lower:
                questions = [
                    {
                        'id': 1,
                        'question': f'What is a variable in {domain_name}?',
                        'options': [
                            {'label': 'A container for storing data', 'value': 'correct'},
                            {'label': 'A type of function', 'value': 'incorrect'},
                            {'label': 'A database table', 'value': 'incorrect'},
                            {'label': 'A network protocol', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': f'What is a function/method in {domain_name}?',
                        'options': [
                            {'label': 'Reusable block of code', 'value': 'correct'},
                            {'label': 'A data type', 'value': 'incorrect'},
                            {'label': 'A file format', 'value': 'incorrect'},
                            {'label': 'A design pattern', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': f'What are loops used for in {domain_name}?',
                        'options': [
                            {'label': 'Repeating code execution', 'value': 'correct'},
                            {'label': 'Storing data', 'value': 'incorrect'},
                            {'label': 'Connecting to databases', 'value': 'incorrect'},
                            {'label': 'Designing interfaces', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': 'What is a conditional statement?',
                        'options': [
                            {'label': 'Code that runs based on conditions', 'value': 'correct'},
                            {'label': 'A way to declare variables', 'value': 'incorrect'},
                            {'label': 'A network request', 'value': 'incorrect'},
                            {'label': 'A database query', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': f'What is an array or list in {domain_name}?',
                        'options': [
                            {'label': 'Collection of elements in sequence', 'value': 'correct'},
                            {'label': 'A single value', 'value': 'incorrect'},
                            {'label': 'A conditional statement', 'value': 'incorrect'},
                            {'label': 'A function parameter', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': f'What is a data type in {domain_name}?',
                        'options': [
                            {'label': 'Classification of data (int, string, etc)', 'value': 'correct'},
                            {'label': 'A variable name', 'value': 'incorrect'},
                            {'label': 'A looping mechanism', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': f'What is object-oriented programming (OOP)?',
                        'options': [
                            {'label': 'Programming using objects and classes', 'value': 'correct'},
                            {'label': 'Using only functions', 'value': 'incorrect'},
                            {'label': 'Writing code in lowercase', 'value': 'incorrect'},
                            {'label': 'A type of database', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': f'What does debugging mean in {domain_name}?',
                        'options': [
                            {'label': 'Finding and fixing errors in code', 'value': 'correct'},
                            {'label': 'Writing code faster', 'value': 'incorrect'},
                            {'label': 'Organizing files', 'value': 'incorrect'},
                            {'label': 'Testing performance', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': f'What is a library or module in {domain_name}?',
                        'options': [
                            {'label': 'Reusable code package for specific functionality', 'value': 'correct'},
                            {'label': 'A book about programming', 'value': 'incorrect'},
                            {'label': 'A file format', 'value': 'incorrect'},
                            {'label': 'A type of variable', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': f'What is version control (like Git)?',
                        'options': [
                            {'label': 'System to track code changes over time', 'value': 'correct'},
                            {'label': 'A way to run programs', 'value': 'incorrect'},
                            {'label': 'A text editor', 'value': 'incorrect'},
                            {'label': 'A database type', 'value': 'incorrect'}
                        ]
                    }
                ]
            elif 'web' in domain_lower or 'frontend' in domain_lower or 'react' in domain_lower or 'angular' in domain_lower or 'vue' in domain_lower:
                questions = [
                    {
                        'id': 1,
                        'question': 'What is HTML used for?',
                        'options': [
                            {'label': 'Structure of web pages', 'value': 'correct'},
                            {'label': 'Styling web pages', 'value': 'incorrect'},
                            {'label': 'Programming logic', 'value': 'incorrect'},
                            {'label': 'Database management', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': 'What is CSS used for?',
                        'options': [
                            {'label': 'Styling and layout', 'value': 'correct'},
                            {'label': 'Page structure', 'value': 'incorrect'},
                            {'label': 'Server logic', 'value': 'incorrect'},
                            {'label': 'Database queries', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': 'What is the DOM?',
                        'options': [
                            {'label': 'Document Object Model', 'value': 'correct'},
                            {'label': 'Data Object Manager', 'value': 'incorrect'},
                            {'label': 'Database Operation Method', 'value': 'incorrect'},
                            {'label': 'Design Output Module', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': 'What makes a website responsive?',
                        'options': [
                            {'label': 'Adapts to different screen sizes', 'value': 'correct'},
                            {'label': 'Loads quickly', 'value': 'incorrect'},
                            {'label': 'Has many features', 'value': 'incorrect'},
                            {'label': 'Uses animations', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': 'What is JavaScript used for?',
                        'options': [
                            {'label': 'Adding interactivity to web pages', 'value': 'correct'},
                            {'label': 'Styling elements', 'value': 'incorrect'},
                            {'label': 'Database management', 'value': 'incorrect'},
                            {'label': 'Server deployment', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': 'What is a CSS selector?',
                        'options': [
                            {'label': 'Way to target HTML elements for styling', 'value': 'correct'},
                            {'label': 'A database query', 'value': 'incorrect'},
                            {'label': 'A JavaScript function', 'value': 'incorrect'},
                            {'label': 'An HTML attribute', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': 'What is a framework like React used for?',
                        'options': [
                            {'label': 'Building user interfaces efficiently', 'value': 'correct'},
                            {'label': 'Database management', 'value': 'incorrect'},
                            {'label': 'Email sending', 'value': 'incorrect'},
                            {'label': 'File compression', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': 'What is the difference between static and dynamic websites?',
                        'options': [
                            {'label': 'Dynamic sites change content, static sites don\'t', 'value': 'correct'},
                            {'label': 'No difference', 'value': 'incorrect'},
                            {'label': 'Static is faster', 'value': 'incorrect'},
                            {'label': 'Dynamic uses only HTML', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': 'What is a web API?',
                        'options': [
                            {'label': 'Interface for web applications to communicate', 'value': 'correct'},
                            {'label': 'A website design', 'value': 'incorrect'},
                            {'label': 'A CSS framework', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': 'What is a browser?',
                        'options': [
                            {'label': 'Software for viewing web pages', 'value': 'correct'},
                            {'label': 'A text editor', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A server', 'value': 'incorrect'}
                        ]
                    }
                ]
            elif 'data' in domain_lower or 'analytics' in domain_lower or 'bi' in domain_lower:
                questions = [
                    {
                        'id': 1,
                        'question': 'What is a dataset?',
                        'options': [
                            {'label': 'Collection of data', 'value': 'correct'},
                            {'label': 'A database server', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A visualization tool', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': 'What does data cleaning mean?',
                        'options': [
                            {'label': 'Fixing errors and missing values', 'value': 'correct'},
                            {'label': 'Deleting all data', 'value': 'incorrect'},
                            {'label': 'Encrypting data', 'value': 'incorrect'},
                            {'label': 'Backing up data', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': 'What is data visualization?',
                        'options': [
                            {'label': 'Representing data graphically', 'value': 'correct'},
                            {'label': 'Storing data', 'value': 'incorrect'},
                            {'label': 'Collecting data', 'value': 'incorrect'},
                            {'label': 'Encrypting data', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': 'What is mean/average?',
                        'options': [
                            {'label': 'Sum divided by count', 'value': 'correct'},
                            {'label': 'Middle value', 'value': 'incorrect'},
                            {'label': 'Most frequent value', 'value': 'incorrect'},
                            {'label': 'Largest value', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': 'What is a database?',
                        'options': [
                            {'label': 'Organized storage for data', 'value': 'correct'},
                            {'label': 'A spreadsheet', 'value': 'incorrect'},
                            {'label': 'A chart', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': 'What is SQL?',
                        'options': [
                            {'label': 'Language for querying databases', 'value': 'correct'},
                            {'label': 'A type of chart', 'value': 'incorrect'},
                            {'label': 'A visualization tool', 'value': 'incorrect'},
                            {'label': 'A programming language for websites', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': 'What is an outlier in data?',
                        'options': [
                            {'label': 'Unusual data point that differs significantly', 'value': 'correct'},
                            {'label': 'The average value', 'value': 'incorrect'},
                            {'label': 'A missing value', 'value': 'incorrect'},
                            {'label': 'The median', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': 'What is correlation?',
                        'options': [
                            {'label': 'Relationship between two variables', 'value': 'correct'},
                            {'label': 'Cause and effect', 'value': 'incorrect'},
                            {'label': 'A type of average', 'value': 'incorrect'},
                            {'label': 'Data sorting', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': 'What does a histogram show?',
                        'options': [
                            {'label': 'Distribution of values in ranges', 'value': 'correct'},
                            {'label': 'Changes over time', 'value': 'incorrect'},
                            {'label': 'Comparison between categories', 'value': 'incorrect'},
                            {'label': 'Relationships between variables', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': 'What is a pivot table?',
                        'options': [
                            {'label': 'Table that reorganizes data for analysis', 'value': 'correct'},
                            {'label': 'A database table', 'value': 'incorrect'},
                            {'label': 'A chart type', 'value': 'incorrect'},
                            {'label': 'A spreadsheet column', 'value': 'incorrect'}
                        ]
                    }
                ]
            elif 'machine learning' in domain_lower or 'ai' in domain_lower or 'ml' in domain_lower or 'deep learning' in domain_lower:
                questions = [
                    {
                        'id': 1,
                        'question': 'What is machine learning?',
                        'options': [
                            {'label': 'Teaching computers to learn from data', 'value': 'correct'},
                            {'label': 'A type of database', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A web framework', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': 'What is supervised learning?',
                        'options': [
                            {'label': 'Learning with labeled data', 'value': 'correct'},
                            {'label': 'Learning without data', 'value': 'incorrect'},
                            {'label': 'Learning from errors only', 'value': 'incorrect'},
                            {'label': 'Manually programming rules', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': 'What is a dataset in ML?',
                        'options': [
                            {'label': 'Collection of training examples', 'value': 'correct'},
                            {'label': 'A single data point', 'value': 'incorrect'},
                            {'label': 'An algorithm', 'value': 'incorrect'},
                            {'label': 'A neural network', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': 'What is a feature in ML?',
                        'options': [
                            {'label': 'An input variable for prediction', 'value': 'correct'},
                            {'label': 'The output/target', 'value': 'incorrect'},
                            {'label': 'An algorithm', 'value': 'incorrect'},
                            {'label': 'A library', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': 'What is unsupervised learning?',
                        'options': [
                            {'label': 'Learning from unlabeled data to find patterns', 'value': 'correct'},
                            {'label': 'Learning with supervision', 'value': 'incorrect'},
                            {'label': 'Learning without computers', 'value': 'incorrect'},
                            {'label': 'Manual data labeling', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': 'What is training in machine learning?',
                        'options': [
                            {'label': 'Process of teaching model with data', 'value': 'correct'},
                            {'label': 'Testing the model', 'value': 'incorrect'},
                            {'label': 'Deploying the model', 'value': 'incorrect'},
                            {'label': 'Collecting data', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': 'What is a model in ML?',
                        'options': [
                            {'label': 'Mathematical function learned from data', 'value': 'correct'},
                            {'label': 'A database', 'value': 'incorrect'},
                            {'label': 'A visualization', 'value': 'incorrect'},
                            {'label': 'A dataset', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': 'What is overfitting?',
                        'options': [
                            {'label': 'Model memorizes training data but fails on new data', 'value': 'correct'},
                            {'label': 'Model doesn\'t learn enough', 'value': 'incorrect'},
                            {'label': 'Too many features', 'value': 'incorrect'},
                            {'label': 'Not enough training data', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': 'What is accuracy in ML?',
                        'options': [
                            {'label': 'Percentage of correct predictions', 'value': 'correct'},
                            {'label': 'Training time', 'value': 'incorrect'},
                            {'label': 'Model size', 'value': 'incorrect'},
                            {'label': 'Data quality', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': 'What is neural network?',
                        'options': [
                            {'label': 'Model inspired by brain\'s structure for learning', 'value': 'correct'},
                            {'label': 'A computer network', 'value': 'incorrect'},
                            {'label': 'A database schema', 'value': 'incorrect'},
                            {'label': 'An algorithm for sorting', 'value': 'incorrect'}
                        ]
                    }
                ]
            elif 'database' in domain_lower or 'sql' in domain_lower:
                questions = [
                    {
                        'id': 1,
                        'question': 'What is a database?',
                        'options': [
                            {'label': 'Organized collection of data', 'value': 'correct'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A web server', 'value': 'incorrect'},
                            {'label': 'An operating system', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': 'What is SQL?',
                        'options': [
                            {'label': 'Language for querying databases', 'value': 'correct'},
                            {'label': 'A database server', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A web framework', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': 'What is a table in a database?',
                        'options': [
                            {'label': 'Collection of rows and columns', 'value': 'correct'},
                            {'label': 'A query command', 'value': 'incorrect'},
                            {'label': 'A server', 'value': 'incorrect'},
                            {'label': 'A programming function', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': 'What is a primary key?',
                        'options': [
                            {'label': 'Unique identifier for a row', 'value': 'correct'},
                            {'label': 'A password', 'value': 'incorrect'},
                            {'label': 'The first column', 'value': 'incorrect'},
                            {'label': 'An encryption key', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': 'What is a foreign key?',
                        'options': [
                            {'label': 'Link to primary key in another table', 'value': 'correct'},
                            {'label': 'A password', 'value': 'incorrect'},
                            {'label': 'A database name', 'value': 'incorrect'},
                            {'label': 'A query result', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': 'What does a SELECT query do?',
                        'options': [
                            {'label': 'Retrieves data from database', 'value': 'correct'},
                            {'label': 'Inserts new data', 'value': 'incorrect'},
                            {'label': 'Deletes data', 'value': 'incorrect'},
                            {'label': 'Creates a table', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': 'What is an index in a database?',
                        'options': [
                            {'label': 'Structure that speeds up data retrieval', 'value': 'correct'},
                            {'label': 'A numbered list', 'value': 'incorrect'},
                            {'label': 'A type of table', 'value': 'incorrect'},
                            {'label': 'A column header', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': 'What is normalization in databases?',
                        'options': [
                            {'label': 'Organizing data to reduce redundancy', 'value': 'correct'},
                            {'label': 'Making data normal', 'value': 'incorrect'},
                            {'label': 'Backing up data', 'value': 'incorrect'},
                            {'label': 'Encrypting data', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': 'What is a transaction in database?',
                        'options': [
                            {'label': 'Unit of work that must complete fully or not at all', 'value': 'correct'},
                            {'label': 'A single query', 'value': 'incorrect'},
                            {'label': 'A database backup', 'value': 'incorrect'},
                            {'label': 'A user account', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': 'What is ACID in database?',
                        'options': [
                            {'label': 'Atomicity, Consistency, Isolation, Durability', 'value': 'correct'},
                            {'label': 'A chemical compound', 'value': 'incorrect'},
                            {'label': 'A type of database', 'value': 'incorrect'},
                            {'label': 'A query language', 'value': 'incorrect'}
                        ]
                    }
                ]
            elif 'cloud' in domain_lower or 'aws' in domain_lower or 'azure' in domain_lower or 'devops' in domain_lower:
                questions = [
                    {
                        'id': 1,
                        'question': 'What is cloud computing?',
                        'options': [
                            {'label': 'On-demand computing resources via internet', 'value': 'correct'},
                            {'label': 'Weather prediction', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A database type', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': 'What is a virtual machine?',
                        'options': [
                            {'label': 'Simulated computer on physical hardware', 'value': 'correct'},
                            {'label': 'A real computer', 'value': 'incorrect'},
                            {'label': 'A mobile app', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': 'What does scalability mean?',
                        'options': [
                            {'label': 'Ability to handle growing workload', 'value': 'correct'},
                            {'label': 'Making code smaller', 'value': 'incorrect'},
                            {'label': 'Measuring performance', 'value': 'incorrect'},
                            {'label': 'Encrypting data', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': 'What is deployment?',
                        'options': [
                            {'label': 'Making software available to users', 'value': 'correct'},
                            {'label': 'Writing code', 'value': 'incorrect'},
                            {'label': 'Testing software', 'value': 'incorrect'},
                            {'label': 'Designing UI', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': 'What is IaaS (Infrastructure as a Service)?',
                        'options': [
                            {'label': 'Cloud provider offers computing infrastructure', 'value': 'correct'},
                            {'label': 'Software provided by cloud', 'value': 'incorrect'},
                            {'label': 'Platform for development', 'value': 'incorrect'},
                            {'label': 'Database service', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': 'What is PaaS (Platform as a Service)?',
                        'options': [
                            {'label': 'Cloud provider offers platform for development', 'value': 'correct'},
                            {'label': 'Infrastructure service', 'value': 'incorrect'},
                            {'label': 'Software subscription', 'value': 'incorrect'},
                            {'label': 'Data storage only', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': 'What is SaaS (Software as a Service)?',
                        'options': [
                            {'label': 'Cloud-based software applications', 'value': 'correct'},
                            {'label': 'Infrastructure for servers', 'value': 'incorrect'},
                            {'label': 'Development platform', 'value': 'incorrect'},
                            {'label': 'Database hosting', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': 'What is AWS (Amazon Web Services)?',
                        'options': [
                            {'label': 'Major cloud computing platform', 'value': 'correct'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'},
                            {'label': 'A web browser', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': 'What is DevOps?',
                        'options': [
                            {'label': 'Integration of development and operations', 'value': 'correct'},
                            {'label': 'Database administration', 'value': 'incorrect'},
                            {'label': 'Cloud computing', 'value': 'incorrect'},
                            {'label': 'Software testing', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': 'What is availability in cloud computing?',
                        'options': [
                            {'label': 'System uptime and reliability', 'value': 'correct'},
                            {'label': 'Number of users', 'value': 'incorrect'},
                            {'label': 'Storage capacity', 'value': 'incorrect'},
                            {'label': 'Internet speed', 'value': 'incorrect'}
                        ]
                    }
                ]
            elif 'security' in domain_lower or 'cyber' in domain_lower or 'hacking' in domain_lower:
                questions = [
                    {
                        'id': 1,
                        'question': 'What is cybersecurity?',
                        'options': [
                            {'label': 'Protecting systems from digital attacks', 'value': 'correct'},
                            {'label': 'Building websites', 'value': 'incorrect'},
                            {'label': 'Data analysis', 'value': 'incorrect'},
                            {'label': 'Cloud computing', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': 'What is encryption?',
                        'options': [
                            {'label': 'Converting data to secure format', 'value': 'correct'},
                            {'label': 'Deleting data', 'value': 'incorrect'},
                            {'label': 'Compressing files', 'value': 'incorrect'},
                            {'label': 'Backing up data', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': 'What is a firewall?',
                        'options': [
                            {'label': 'Network security system', 'value': 'correct'},
                            {'label': 'A virus', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': 'What is a password policy?',
                        'options': [
                            {'label': 'Rules for creating secure passwords', 'value': 'correct'},
                            {'label': 'A list of passwords', 'value': 'incorrect'},
                            {'label': 'A hacking tool', 'value': 'incorrect'},
                            {'label': 'A database table', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': 'What is malware?',
                        'options': [
                            {'label': 'Malicious software designed to harm systems', 'value': 'correct'},
                            {'label': 'A security tool', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A database backup', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': 'What is phishing?',
                        'options': [
                            {'label': 'Deceptive attempt to get sensitive information', 'value': 'correct'},
                            {'label': 'A type of encryption', 'value': 'incorrect'},
                            {'label': 'A programming concept', 'value': 'incorrect'},
                            {'label': 'A network protocol', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': 'What is two-factor authentication (2FA)?',
                        'options': [
                            {'label': 'Two-step verification for login security', 'value': 'correct'},
                            {'label': 'Two passwords', 'value': 'incorrect'},
                            {'label': 'Double encryption', 'value': 'incorrect'},
                            {'label': 'Backup authentication', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': 'What is a VPN (Virtual Private Network)?',
                        'options': [
                            {'label': 'Secure tunnel for internet connections', 'value': 'correct'},
                            {'label': 'A database', 'value': 'incorrect'},
                            {'label': 'A firewall', 'value': 'incorrect'},
                            {'label': 'An antivirus', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': 'What is a vulnerability?',
                        'options': [
                            {'label': 'Weakness that can be exploited by attackers', 'value': 'correct'},
                            {'label': 'A security solution', 'value': 'incorrect'},
                            {'label': 'A firewall rule', 'value': 'incorrect'},
                            {'label': 'A backup system', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': 'What is penetration testing?',
                        'options': [
                            {'label': 'Authorized testing to find security weaknesses', 'value': 'correct'},
                            {'label': 'Hacking a system', 'value': 'incorrect'},
                            {'label': 'Deploying code', 'value': 'incorrect'},
                            {'label': 'Database backup', 'value': 'incorrect'}
                        ]
                    }
                ]
            elif 'mobile' in domain_lower or 'ios' in domain_lower or 'android' in domain_lower:
                questions = [
                    {
                        'id': 1,
                        'question': 'What is a mobile app?',
                        'options': [
                            {'label': 'Software for mobile devices', 'value': 'correct'},
                            {'label': 'A website', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'},
                            {'label': 'An operating system', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': 'What is a user interface (UI)?',
                        'options': [
                            {'label': 'Visual elements users interact with', 'value': 'correct'},
                            {'label': 'Backend code', 'value': 'incorrect'},
                            {'label': 'Database schema', 'value': 'incorrect'},
                            {'label': 'Server configuration', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': 'What is cross-platform development?',
                        'options': [
                            {'label': 'Building for multiple platforms with one codebase', 'value': 'correct'},
                            {'label': 'Using multiple programming languages', 'value': 'incorrect'},
                            {'label': 'Testing on different devices', 'value': 'incorrect'},
                            {'label': 'Deploying to app stores', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': 'What is an API in mobile development?',
                        'options': [
                            {'label': 'Interface for communicating with servers', 'value': 'correct'},
                            {'label': 'A UI component', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': 'What is Android?',
                        'options': [
                            {'label': 'Mobile operating system by Google', 'value': 'correct'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A web framework', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': 'What is iOS?',
                        'options': [
                            {'label': 'Mobile operating system by Apple', 'value': 'correct'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'An Android app', 'value': 'incorrect'},
                            {'label': 'An open-source OS', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': 'What is responsive design?',
                        'options': [
                            {'label': 'Design adapts to different screen sizes', 'value': 'correct'},
                            {'label': 'Design that loads fast', 'value': 'incorrect'},
                            {'label': 'Design with many colors', 'value': 'incorrect'},
                            {'label': 'Design for web only', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': 'What is mobile UX (User Experience)?',
                        'options': [
                            {'label': 'Overall experience users have with the app', 'value': 'correct'},
                            {'label': 'Visual design only', 'value': 'incorrect'},
                            {'label': 'App performance', 'value': 'incorrect'},
                            {'label': 'Marketing strategy', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': 'What is an app store?',
                        'options': [
                            {'label': 'Marketplace for downloading applications', 'value': 'correct'},
                            {'label': 'A physical store', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'},
                            {'label': 'A development tool', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': 'What is native app development?',
                        'options': [
                            {'label': 'Building apps specifically for one platform', 'value': 'correct'},
                            {'label': 'Building for all platforms', 'value': 'incorrect'},
                            {'label': 'Building web apps', 'value': 'incorrect'},
                            {'label': 'Building hybrid apps', 'value': 'incorrect'}
                        ]
                    }
                ]
            elif 'blockchain' in domain_lower or 'crypto' in domain_lower or 'web3' in domain_lower:
                questions = [
                    {
                        'id': 1,
                        'question': 'What is blockchain?',
                        'options': [
                            {'label': 'Distributed ledger technology', 'value': 'correct'},
                            {'label': 'A cryptocurrency', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'},
                            {'label': 'A database server', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': 'What is cryptocurrency?',
                        'options': [
                            {'label': 'Digital currency using cryptography', 'value': 'correct'},
                            {'label': 'Regular money', 'value': 'incorrect'},
                            {'label': 'A blockchain', 'value': 'incorrect'},
                            {'label': 'A smart contract', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': 'What is a smart contract?',
                        'options': [
                            {'label': 'Self-executing code on blockchain', 'value': 'correct'},
                            {'label': 'A legal document', 'value': 'incorrect'},
                            {'label': 'A cryptocurrency wallet', 'value': 'incorrect'},
                            {'label': 'A database', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': 'What is decentralization?',
                        'options': [
                            {'label': 'Distributed control across network', 'value': 'correct'},
                            {'label': 'Central authority control', 'value': 'incorrect'},
                            {'label': 'Cloud computing', 'value': 'incorrect'},
                            {'label': 'Data encryption', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': 'What is a block in blockchain?',
                        'options': [
                            {'label': 'Collection of transactions', 'value': 'correct'},
                            {'label': 'A cryptocurrency unit', 'value': 'incorrect'},
                            {'label': 'A security measure', 'value': 'incorrect'},
                            {'label': 'A smart contract', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': 'What is hashing in blockchain?',
                        'options': [
                            {'label': 'Algorithm that converts data to fixed-size code', 'value': 'correct'},
                            {'label': 'Dividing data', 'value': 'incorrect'},
                            {'label': 'Encryption method', 'value': 'incorrect'},
                            {'label': 'A type of blockchain', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': 'What is mining in cryptocurrency?',
                        'options': [
                            {'label': 'Solving mathematical problems to validate transactions', 'value': 'correct'},
                            {'label': 'Finding cryptocurrency in nature', 'value': 'incorrect'},
                            {'label': 'Buying cryptocurrency', 'value': 'incorrect'},
                            {'label': 'Stealing cryptocurrency', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': 'What is Web3?',
                        'options': [
                            {'label': 'Next generation of web with blockchain integration', 'value': 'correct'},
                            {'label': 'A website', 'value': 'incorrect'},
                            {'label': 'A cryptocurrency', 'value': 'incorrect'},
                            {'label': 'A programming language', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': 'What is a wallet in cryptocurrency?',
                        'options': [
                            {'label': 'Digital tool to store and manage cryptocurrency', 'value': 'correct'},
                            {'label': 'Physical money holder', 'value': 'incorrect'},
                            {'label': 'A bank account', 'value': 'incorrect'},
                            {'label': 'A trading platform', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': 'What is consensus in blockchain?',
                        'options': [
                            {'label': 'Agreement mechanism for validating transactions', 'value': 'correct'},
                            {'label': 'A voting system', 'value': 'incorrect'},
                            {'label': 'A security protocol', 'value': 'incorrect'},
                            {'label': 'A smart contract', 'value': 'incorrect'}
                        ]
                    }
                ]
            else:
                # Generic beginner questions for any domain
                questions = [
                    {
                        'id': 1,
                        'question': f'What is the main purpose of {domain_name}?',
                        'options': [
                            {'label': 'Core objective/benefit', 'value': 'correct'},
                            {'label': 'Secondary benefit', 'value': 'incorrect'},
                            {'label': 'Unrelated concept', 'value': 'incorrect'},
                            {'label': 'Opposite meaning', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': f'Which concept is fundamental to {domain_name}?',
                        'options': [
                            {'label': 'Basic foundational concept', 'value': 'correct'},
                            {'label': 'Advanced technique', 'value': 'incorrect'},
                            {'label': 'Expert-level pattern', 'value': 'incorrect'},
                            {'label': 'Unrelated concept', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': f'What should beginners focus on first in {domain_name}?',
                        'options': [
                            {'label': 'Core fundamentals and basics', 'value': 'correct'},
                            {'label': 'Advanced frameworks', 'value': 'incorrect'},
                            {'label': 'Production deployment', 'value': 'incorrect'},
                            {'label': 'Expert optimizations', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': f'Which tool/technology is essential for {domain_name} beginners?',
                        'options': [
                            {'label': 'Beginner-friendly essential tool', 'value': 'correct'},
                            {'label': 'Expert-only advanced tool', 'value': 'incorrect'},
                            {'label': 'Deprecated technology', 'value': 'incorrect'},
                            {'label': 'Unrelated tool', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': f'What are the prerequisites for learning {domain_name}?',
                        'options': [
                            {'label': 'Basic foundational knowledge', 'value': 'correct'},
                            {'label': 'Advanced expertise required', 'value': 'incorrect'},
                            {'label': 'No prior knowledge needed for some', 'value': 'incorrect'},
                            {'label': 'Must be a domain expert', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': f'How is {domain_name} commonly used in the real world?',
                        'options': [
                            {'label': 'Practical business applications', 'value': 'correct'},
                            {'label': 'Only in academic settings', 'value': 'incorrect'},
                            {'label': 'No real-world use', 'value': 'incorrect'},
                            {'label': 'Only for entertainment', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': f'What are the main benefits of learning {domain_name}?',
                        'options': [
                            {'label': 'Career advancement and skill development', 'value': 'correct'},
                            {'label': 'No real benefits', 'value': 'incorrect'},
                            {'label': 'Only for hobbyists', 'value': 'incorrect'},
                            {'label': 'Purely theoretical value', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': f'What is the typical timeline to become proficient in {domain_name}?',
                        'options': [
                            {'label': 'Several months to years with consistent practice', 'value': 'correct'},
                            {'label': 'One day', 'value': 'incorrect'},
                            {'label': 'Impossible to learn', 'value': 'incorrect'},
                            {'label': 'Decades of study', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': f'Which companies or industries heavily use {domain_name}?',
                        'options': [
                            {'label': 'Major tech and professional organizations', 'value': 'correct'},
                            {'label': 'Only startups', 'value': 'incorrect'},
                            {'label': 'No companies use it', 'value': 'incorrect'},
                            {'label': 'Only educational institutions', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': f'What projects can beginners build with {domain_name}?',
                        'options': [
                            {'label': 'Simple to moderately complex projects', 'value': 'correct'},
                            {'label': 'Only complex enterprise systems', 'value': 'incorrect'},
                            {'label': 'Nothing practical at beginner level', 'value': 'incorrect'},
                            {'label': 'Only theoretical exercises', 'value': 'incorrect'}
                        ]
                    }
                ]
            
            return {
                'title': f'{domain_name} - Beginner Assessment',
                'description': f'Test your foundational knowledge of {domain_name}',
                'type': 'assessment',
                'questions': questions
            }
        
        if level_name == 'Intermediate':
            return {
                'title': f'{domain_name} - Intermediate Assessment',
                'description': f'Check your practical skills in {domain_name}',
                'type': 'assessment',
                'questions': [
                    {
                        'id': 1,
                        'question': f'How would you approach a medium-complexity problem in {domain_name}?',
                        'options': [
                            {'label': 'Methodical approach with best practices', 'value': 'correct'},
                            {'label': 'Quick fix without planning', 'value': 'incorrect'},
                            {'label': 'Over-engineered solution', 'value': 'incorrect'},
                            {'label': 'Avoid the problem', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': f'What is an important intermediate concept in {domain_name}?',
                        'options': [
                            {'label': 'Core architectural/design pattern', 'value': 'correct'},
                            {'label': 'Basic syntax', 'value': 'incorrect'},
                            {'label': 'Installation steps', 'value': 'incorrect'},
                            {'label': 'Unrelated concept', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': f'How do you optimize performance in {domain_name}?',
                        'options': [
                            {'label': 'Apply proven optimization techniques', 'value': 'correct'},
                            {'label': 'Ignore performance', 'value': 'incorrect'},
                            {'label': 'Premature optimization', 'value': 'incorrect'},
                            {'label': 'Random trial and error', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': f'What is crucial for scalability in {domain_name}?',
                        'options': [
                            {'label': 'Proper architecture and design', 'value': 'correct'},
                            {'label': 'More hardware only', 'value': 'incorrect'},
                            {'label': 'Ignoring architecture', 'value': 'incorrect'},
                            {'label': 'Quick hacks', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': f'What testing strategy is important for intermediate developers in {domain_name}?',
                        'options': [
                            {'label': 'Unit and integration testing', 'value': 'correct'},
                            {'label': 'No testing needed', 'value': 'incorrect'},
                            {'label': 'Only manual testing', 'value': 'incorrect'},
                            {'label': 'Testing after deployment', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': f'How do you handle errors in {domain_name}?',
                        'options': [
                            {'label': 'Comprehensive error handling and logging', 'value': 'correct'},
                            {'label': 'Ignore errors', 'value': 'incorrect'},
                            {'label': 'Print error messages only', 'value': 'incorrect'},
                            {'label': 'Crash the application', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': f'What is important for maintainability in {domain_name}?',
                        'options': [
                            {'label': 'Clean code and documentation', 'value': 'correct'},
                            {'label': 'Code golfing', 'value': 'incorrect'},
                            {'label': 'Minimal comments', 'value': 'incorrect'},
                            {'label': 'Complex solutions', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': f'How do you collaborate on {domain_name} projects?',
                        'options': [
                            {'label': 'Using version control and code reviews', 'value': 'correct'},
                            {'label': 'Direct file sharing', 'value': 'incorrect'},
                            {'label': 'No collaboration needed', 'value': 'incorrect'},
                            {'label': 'Manual merging', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': f'What security considerations matter for intermediate developers in {domain_name}?',
                        'options': [
                            {'label': 'Input validation and secure practices', 'value': 'correct'},
                            {'label': 'Security is not important', 'value': 'incorrect'},
                            {'label': 'Only worry about passwords', 'value': 'incorrect'},
                            {'label': 'Security is only for experts', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': f'What is the next step after mastering intermediate {domain_name} concepts?',
                        'options': [
                            {'label': 'Move to advanced concepts and specializations', 'value': 'correct'},
                            {'label': 'Stay at intermediate level', 'value': 'incorrect'},
                            {'label': 'Go back to basics', 'value': 'incorrect'},
                            {'label': 'Stop learning', 'value': 'incorrect'}
                        ]
                    }
                ]
            }
        
        if level_name == 'Advanced':
            return {
                'title': f'{domain_name} - Advanced Assessment',
                'description': f'Expert-level concepts and best practices in {domain_name}',
                'type': 'assessment',
                'questions': [
                    {
                        'id': 1,
                        'question': f'How do you architect production-grade systems in {domain_name}?',
                        'options': [
                            {'label': 'Follow industry best practices and patterns', 'value': 'correct'},
                            {'label': 'Copy-paste solutions', 'value': 'incorrect'},
                            {'label': 'Reinvent everything', 'value': 'incorrect'},
                            {'label': 'Avoid patterns', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 2,
                        'question': f'What advanced technique is critical in {domain_name}?',
                        'options': [
                            {'label': 'Expert-level optimization/pattern', 'value': 'correct'},
                            {'label': 'Basic loops and conditions', 'value': 'incorrect'},
                            {'label': 'Simple variables', 'value': 'incorrect'},
                            {'label': 'Unrelated concept', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 3,
                        'question': f'How do you handle complex edge cases in {domain_name}?',
                        'options': [
                            {'label': 'Comprehensive error handling and testing', 'value': 'correct'},
                            {'label': 'Ignore edge cases', 'value': 'incorrect'},
                            {'label': 'Hope they don\'t occur', 'value': 'incorrect'},
                            {'label': 'Basic try-catch only', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 4,
                        'question': f'What separates experts from intermediates in {domain_name}?',
                        'options': [
                            {'label': 'Deep understanding and experience', 'value': 'correct'},
                            {'label': 'Knowing syntax', 'value': 'incorrect'},
                            {'label': 'Following tutorials', 'value': 'incorrect'},
                            {'label': 'Using latest tools', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 5,
                        'question': f'How do you make architectural decisions in {domain_name}?',
                        'options': [
                            {'label': 'Based on trade-offs and system requirements', 'value': 'correct'},
                            {'label': 'Random choices', 'value': 'incorrect'},
                            {'label': 'Following trends blindly', 'value': 'incorrect'},
                            {'label': 'Avoiding decisions', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 6,
                        'question': f'What is advanced optimization in {domain_name}?',
                        'options': [
                            {'label': 'Data-driven improvements with profiling', 'value': 'correct'},
                            {'label': 'Random optimizations', 'value': 'incorrect'},
                            {'label': 'Premature optimization', 'value': 'incorrect'},
                            {'label': 'No optimization needed', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 7,
                        'question': f'How do you ensure system reliability in {domain_name}?',
                        'options': [
                            {'label': 'Monitoring, logging, and incident response', 'value': 'correct'},
                            {'label': 'Hoping nothing breaks', 'value': 'incorrect'},
                            {'label': 'Only testing locally', 'value': 'incorrect'},
                            {'label': 'No monitoring needed', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 8,
                        'question': f'What is your approach to technical debt in {domain_name}?',
                        'options': [
                            {'label': 'Manage and strategically pay down over time', 'value': 'correct'},
                            {'label': 'Ignore it completely', 'value': 'incorrect'},
                            {'label': 'Accumulate without management', 'value': 'incorrect'},
                            {'label': 'Avoid any technical debt', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 9,
                        'question': f'How do you contribute to open source or community in {domain_name}?',
                        'options': [
                            {'label': 'Sharing knowledge and contributing code', 'value': 'correct'},
                            {'label': 'Never sharing knowledge', 'value': 'incorrect'},
                            {'label': 'Only taking without contributing', 'value': 'incorrect'},
                            {'label': 'Working in isolation', 'value': 'incorrect'}
                        ]
                    },
                    {
                        'id': 10,
                        'question': f'What is your vision for mastery in {domain_name}?',
                        'options': [
                            {'label': 'Continuous learning and pushing boundaries', 'value': 'correct'},
                            {'label': 'Stagnating at current level', 'value': 'incorrect'},
                            {'label': 'Giving up when it gets hard', 'value': 'incorrect'},
                            {'label': 'Never asking for help', 'value': 'incorrect'}
                        ]
                    }
                ]
            }
        
        # Default fallback
        return {
            'title': f'{domain_name} - Assessment',
            'description': 'General assessment',
            'type': 'assessment',
            'questions': []
        }

    # Try to get from AI-generated questions
    quiz_data = build_default_quiz(domain.name, selected_level)
    return jsonify(quiz_data)


def get_top_10_courses(domain_name, level):
    """Generate curated list of top 10 free courses for domain and level"""
    domain_lower = domain_name.lower()
    
    # Comprehensive course database by domain
    courses_db = {
        'programming': {
                'Zero': [
                    {'title': 'Python for Beginners', 'source': 'Microsoft Learn', 'rating': '4.8', 'url': 'https://learn.microsoft.com/en-us/training/modules/python-beginner/', 'price': 'Free'},
                    {'title': 'Introduction to Programming', 'source': 'Khan Academy', 'rating': '4.7', 'url': 'https://www.khanacademy.org/computing/computer-programming', 'price': 'Free'},
                    {'title': 'The Complete Python Course', 'source': 'Udemy', 'rating': '4.6', 'url': 'https://www.udemy.com/course/the-complete-python-course/', 'price': '$49.99'},
                    {'title': 'Python Basics for Data Analysis', 'source': 'Coursera', 'rating': '4.5', 'url': 'https://www.coursera.org/learn/python-data-analysis', 'price': '$49/month'},
                    {'title': 'Programming Fundamentals', 'source': 'edX', 'rating': '4.7', 'url': 'https://www.edx.org/course/programming-fundamentals', 'price': 'Free'},
                    {'title': 'Code.org - Python for Everyone', 'source': 'Code.org', 'rating': '4.9', 'url': 'https://code.org/', 'price': 'Free'},
                    {'title': 'Codecademy - Learn Python', 'source': 'Codecademy', 'rating': '4.6', 'url': 'https://www.codecademy.com/learn/learn-python-3', 'price': '$19.99/month'},
                    {'title': 'W3Schools Python Tutorial', 'source': 'W3Schools', 'rating': '4.8', 'url': 'https://www.w3schools.com/python/', 'price': 'Free'},
                    {'title': 'FreeCodeCamp Python Course', 'source': 'FreeCodeCamp', 'rating': '4.9', 'url': 'https://www.freecodecamp.org/learn/scientific-computing-with-python/', 'price': 'Free'},
                    {'title': 'Python Tutorial - GeeksforGeeks', 'source': 'GeeksforGeeks', 'rating': '4.7', 'url': 'https://www.geeksforgeeks.org/python-tutorial/', 'price': 'Free'}
                ],
                'Beginner': [
                    {'title': 'Python Programming Masterclass', 'source': 'Udemy', 'rating': '4.7', 'url': 'https://www.udemy.com/course/python-the-complete-python-developer-course/', 'price': '$84.99'},
                    {'title': 'Complete Python Bootcamp', 'source': 'Coursera', 'rating': '4.6', 'url': 'https://www.coursera.org/specializations/python', 'price': '$49/month'},
                    {'title': 'Learn Python 3', 'source': 'Codecademy', 'rating': '4.6', 'url': 'https://www.codecademy.com/learn/learn-python-3', 'price': '$19.99/month'},
                    {'title': 'Python for Data Analysis', 'source': 'edX', 'rating': '4.5', 'url': 'https://www.edx.org/course/python-data-analysis-3', 'price': 'Free'},
                    {'title': 'JavaScript Basics', 'source': 'Codecademy', 'rating': '4.7', 'url': 'https://www.codecademy.com/learn/learn-javascript', 'price': '$19.99/month'},
                    {'title': 'Java Programming Basics', 'source': 'Udacity', 'rating': '4.6', 'url': 'https://www.udacity.com/course/java-for-developers--ud282', 'price': 'Free'},
                    {'title': 'Introduction to Computer Science', 'source': 'Harvard (CS50)', 'rating': '4.9', 'url': 'https://cs50.harvard.edu/', 'price': 'Free'},
                    {'title': 'The Odin Project', 'source': 'The Odin Project', 'rating': '4.8', 'url': 'https://www.theodinproject.com/', 'price': 'Free'},
                    {'title': 'FreeCodeCamp Responsive Web Design', 'source': 'FreeCodeCamp', 'rating': '4.8', 'url': 'https://www.freecodecamp.org/learn/responsive-web-design/', 'price': 'Free'},
                    {'title': 'Automate the Boring Stuff', 'source': 'PracticePython', 'rating': '4.7', 'url': 'https://automatetheboringstuff.com/', 'price': 'Free'}
                ],
                'Intermediate': [
                    {'title': 'Advanced Python Programming', 'source': 'Udemy', 'rating': '4.7', 'url': 'https://www.udemy.com/course/advanced-python-programming/', 'price': '$89.99'},
                    {'title': 'Software Engineering Principles', 'source': 'Coursera', 'rating': '4.6', 'url': 'https://www.coursera.org/learn/software-engineering', 'price': '$49/month'},
                    {'title': 'Design Patterns in Python', 'source': 'Pluralsight', 'rating': '4.7', 'url': 'https://www.pluralsight.com/courses/python-design-patterns', 'price': '$29/month'},
                    {'title': 'Object-Oriented Programming', 'source': 'edX', 'rating': '4.6', 'url': 'https://www.edx.org/course/object-oriented-programming', 'price': 'Free'},
                    {'title': 'Data Structures & Algorithms', 'source': 'GeeksforGeeks', 'rating': '4.8', 'url': 'https://www.geeksforgeeks.org/data-structures/', 'price': 'Free'},
                    {'title': 'System Design Primer', 'source': 'GitHub', 'rating': '4.9', 'url': 'https://github.com/donnemartin/system-design-primer', 'price': 'Free'},
                    {'title': 'Coding Interview Prep', 'source': 'LeetCode', 'rating': '4.7', 'url': 'https://leetcode.com/', 'price': '$35/month'},
                    {'title': 'Clean Code Principles', 'source': 'Pluralsight', 'rating': '4.6', 'url': 'https://www.pluralsight.com/courses/writing-clean-code', 'price': '$29/month'},
                    {'title': 'Testing & Debugging', 'source': 'Udemy', 'rating': '4.6', 'url': 'https://www.udemy.com/course/testing-debugging/', 'price': '$59.99'},
                    {'title': 'Python Web Development', 'source': 'FreeCodeCamp', 'rating': '4.8', 'url': 'https://www.freecodecamp.org/learn/back-end-development-and-apis/', 'price': 'Free'}
                ],
                'Advanced': [
                    {'title': 'Distributed Systems', 'source': 'MIT OpenCourseWare', 'rating': '4.9', 'url': 'https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-824-distributed-computer-systems-engineering-spring-2006/', 'price': 'Free'},
                    {'title': 'Advanced Software Architecture', 'source': 'Coursera', 'rating': '4.8', 'url': 'https://www.coursera.org/learn/advanced-software-architecture', 'price': '$49/month'},
                    {'title': 'Microservices Architecture', 'source': 'Udemy', 'rating': '4.7', 'url': 'https://www.udemy.com/course/microservices-architecture/', 'price': '$89.99'},
                    {'title': 'System Design Interview', 'source': 'ByteByteGo', 'rating': '4.8', 'url': 'https://bytebytego.com/', 'price': '$39/year'},
                    {'title': 'High Performance Computing', 'source': 'edX', 'rating': '4.7', 'url': 'https://www.edx.org/course/high-performance-computing', 'price': 'Free'},
                    {'title': 'Advanced Algorithms', 'source': 'Stanford Online', 'rating': '4.9', 'url': 'https://online.stanford.edu/courses/soe-ycscs1-algorithms-analysis', 'price': 'Free'},
                    {'title': 'Compiler Design', 'source': 'Coursera', 'rating': '4.6', 'url': 'https://www.coursera.org/learn/compilers', 'price': '$49/month'},
                    {'title': 'Operating Systems', 'source': 'Berkeley (CS162)', 'rating': '4.8', 'url': 'https://cs162.eecs.berkeley.edu/', 'price': 'Free'},
                    {'title': 'Database Systems', 'source': 'CMU (15-445)', 'rating': '4.9', 'url': 'https://15445.courses.cs.cmu.edu/', 'price': 'Free'},
                    {'title': 'Machine Learning Engineering', 'source': 'Coursera', 'rating': '4.7', 'url': 'https://www.coursera.org/learn/machine-learning-engineering', 'price': '$49/month'}
                ]
            },
            'web development': {
                'Zero': [
                    {'title': 'HTML Basics', 'source': 'W3Schools', 'rating': '4.9', 'url': 'https://www.w3schools.com/html/', 'price': 'Free'},
                    {'title': 'CSS Fundamentals', 'source': 'MDN Web Docs', 'rating': '4.8', 'url': 'https://developer.mozilla.org/en-US/docs/Learn/CSS', 'price': 'Free'},
                    {'title': 'Intro to Web Development', 'source': 'Codecademy', 'rating': '4.7', 'url': 'https://www.codecademy.com/learn/learn-how-to-code', 'price': '$19.99/month'},
                    {'title': 'FreeCodeCamp Responsive Web', 'source': 'FreeCodeCamp', 'rating': '4.9', 'url': 'https://www.freecodecamp.org/learn/responsive-web-design/', 'price': 'Free'},
                    {'title': 'Khan Academy - Web Dev', 'source': 'Khan Academy', 'rating': '4.6', 'url': 'https://www.khanacademy.org/computing/computer-programming/html-css', 'price': 'Free'},
                    {'title': 'The Odin Project', 'source': 'The Odin Project', 'rating': '4.8', 'url': 'https://www.theodinproject.com/', 'price': 'Free'},
                    {'title': 'Udemy Web Dev Bootcamp', 'source': 'Udemy', 'rating': '4.7', 'url': 'https://www.udemy.com/course/the-web-developer-bootcamp/', 'price': '$79.99'},
                    {'title': 'Coursera Web Design', 'source': 'Coursera', 'rating': '4.6', 'url': 'https://www.coursera.org/learn/web-design', 'price': '$49/month'},
                    {'title': 'LinkedIn Learning Web Dev', 'source': 'LinkedIn Learning', 'rating': '4.6', 'url': 'https://www.linkedin.com/learning/paths/become-a-web-developer', 'price': '$39.99/month'},
                    {'title': 'Scrimba Frontend Path', 'source': 'Scrimba', 'rating': '4.7', 'url': 'https://scrimba.com/learn/frontend', 'price': '$20/month'}
                ],
                'Beginner': [
                    {'title': 'JavaScript for Beginners', 'source': 'Codecademy', 'rating': '4.6', 'url': 'https://www.codecademy.com/learn/learn-javascript', 'price': '$19.99/month'},
                    {'title': 'React Basics', 'source': 'Scrimba', 'rating': '4.7', 'url': 'https://scrimba.com/learn/learnreact', 'price': '$20/month'},
                    {'title': 'Web Design Fundamentals', 'source': 'Udacity', 'rating': '4.6', 'url': 'https://www.udacity.com/course/intro-to-html-and-css--ud304', 'price': 'Free'},
                    {'title': 'FreeCodeCamp JavaScript', 'source': 'FreeCodeCamp', 'rating': '4.8', 'url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 'price': 'Free'},
                    {'title': 'Vue.js Essentials', 'source': 'Coursera', 'rating': '4.5', 'url': 'https://www.coursera.org/learn/vue-essentials', 'price': '$49/month'},
                    {'title': 'Angular Fundamentals', 'source': 'Udemy', 'rating': '4.6', 'url': 'https://www.udemy.com/course/angular-fundamentals/', 'price': '$59.99'},
                    {'title': 'Frontend Development', 'source': 'edX', 'rating': '4.6', 'url': 'https://www.edx.org/course/front-end-web-development', 'price': 'Free'},
                    {'title': 'CSS Grid & Flexbox', 'source': 'Wes Bos', 'rating': '4.8', 'url': 'https://cssgrid.io/', 'price': 'Free'},
                    {'title': 'JavaScript DOM Manipulation', 'source': 'Traversy Media', 'rating': '4.7', 'url': 'https://www.youtube.com/watch?v=0ik6X7ZrIM4', 'price': 'Free'},
                    {'title': 'Web Performance', 'source': 'Pluralsight', 'rating': '4.6', 'url': 'https://www.pluralsight.com/courses/web-performance', 'price': '$29/month'}
                ],
                'Intermediate': [
                    {'title': 'Advanced React Patterns', 'source': 'Scrimba', 'rating': '4.7', 'url': 'https://scrimba.com/learn/advancedreact', 'price': '$20/month'},
                    {'title': 'Next.js Fundamentals', 'source': 'Vercel', 'rating': '4.8', 'url': 'https://nextjs.org/learn', 'price': 'Free'},
                    {'title': 'State Management', 'source': 'Udemy', 'rating': '4.6', 'url': 'https://www.udemy.com/course/redux-saga/', 'price': '$69.99'},
                    {'title': 'REST API Design', 'source': 'Coursera', 'rating': '4.7', 'url': 'https://www.coursera.org/learn/api-design', 'price': '$49/month'},
                    {'title': 'GraphQL Fundamentals', 'source': 'Apollo', 'rating': '4.7', 'url': 'https://www.apollographql.com/docs/apollo-server/getting-started/', 'price': 'Free'},
                    {'title': 'Testing Web Applications', 'source': 'Udemy', 'rating': '4.6', 'url': 'https://www.udemy.com/course/testing-javascript/', 'price': '$74.99'},
                    {'title': 'Web Security Essentials', 'source': 'Pluralsight', 'rating': '4.7', 'url': 'https://www.pluralsight.com/courses/web-security-essentials', 'price': '$29/month'},
                    {'title': 'Build Tools & Webpack', 'source': 'Frontend Masters', 'rating': '4.7', 'url': 'https://frontendmasters.com/courses/webpack/', 'price': '$39/month'},
                    {'title': 'TypeScript for JavaScript', 'source': 'Scrimba', 'rating': '4.6', 'url': 'https://scrimba.com/learn/typescript', 'price': '$20/month'},
                    {'title': 'Accessibility (a11y)', 'source': 'WebAIM', 'rating': '4.8', 'url': 'https://webaim.org/', 'price': 'Free'}
                ],
                'Advanced': [
                    {'title': 'Advanced TypeScript', 'source': 'Frontend Masters', 'rating': '4.8', 'url': 'https://frontendmasters.com/courses/advanced-typescript/', 'price': '$39/month'},
                    {'title': 'Architecture Patterns', 'source': 'Udemy', 'rating': '4.7', 'url': 'https://www.udemy.com/course/web-architecture-fundamentals/', 'price': '$89.99'},
                    {'title': 'Performance Optimization', 'source': 'Coursera', 'rating': '4.7', 'url': 'https://www.coursera.org/learn/web-performance', 'price': '$49/month'},
                    {'title': 'Advanced Node.js', 'source': 'Pluralsight', 'rating': '4.7', 'url': 'https://www.pluralsight.com/courses/nodejs-advanced', 'price': '$29/month'},
                    {'title': 'Serverless Architecture', 'source': 'AWS', 'rating': '4.8', 'url': 'https://aws.amazon.com/getting-started/serverless/', 'price': 'Free'},
                    {'title': 'Microservices Frontend', 'source': 'Frontend Masters', 'rating': '4.7', 'url': 'https://frontendmasters.com/courses/web-components/', 'price': '$39/month'},
                    {'title': 'Advanced WebGL', 'source': 'Udacity', 'rating': '4.6', 'url': 'https://www.udacity.com/course/interactive-3d-graphics--cs291', 'price': 'Free'},
                    {'title': 'Web Assembly Basics', 'source': 'Mozilla', 'rating': '4.7', 'url': 'https://developer.mozilla.org/en-US/docs/WebAssembly', 'price': 'Free'},
                    {'title': 'Progressive Web Apps', 'source': 'Google', 'rating': '4.8', 'url': 'https://web.dev/progressive-web-apps/', 'price': 'Free'},
                    {'title': 'Advanced CSS', 'source': 'Frontend Masters', 'rating': '4.8', 'url': 'https://frontendmasters.com/courses/advanced-css/', 'price': '$39/month'}
                ]
            },
            'data science': {
                'Zero': [
                    {'title': 'Data Science for Beginners', 'source': 'Microsoft Learn', 'rating': '4.7', 'url': 'https://github.com/microsoft/Data-Science-For-Beginners', 'price': 'Free'},
                    {'title': 'Python for Data Analysis', 'source': 'DataCamp', 'rating': '4.6', 'url': 'https://www.datacamp.com/courses/intro-to-python-for-data-science', 'price': '$25/month'},
                    {'title': 'Statistics Fundamentals', 'source': 'Khan Academy', 'rating': '4.8', 'url': 'https://www.khanacademy.org/math/statistics-probability', 'price': 'Free'},
                    {'title': 'Pandas Tutorial', 'source': 'W3Schools', 'rating': '4.7', 'url': 'https://www.w3schools.com/python/pandas/', 'price': 'Free'},
                    {'title': 'Intro to Data Viz', 'source': 'Coursera', 'rating': '4.6', 'url': 'https://www.coursera.org/learn/datavis', 'price': '$49/month'},
                    {'title': 'Excel for Data Analysis', 'source': 'Udemy', 'rating': '4.7', 'url': 'https://www.udemy.com/course/excel-data-analysis/', 'price': '$54.99'},
                    {'title': 'FreeCodeCamp Data Science', 'source': 'FreeCodeCamp', 'rating': '4.8', 'url': 'https://www.freecodecamp.org/learn/data-analysis-with-python/', 'price': 'Free'},
                    {'title': 'SQL for Data Analysis', 'source': 'DataCamp', 'rating': '4.7', 'url': 'https://www.datacamp.com/courses/sql-basics', 'price': '$25/month'},
                    {'title': 'Tableau Public', 'source': 'Tableau', 'rating': '4.6', 'url': 'https://public.tableau.com/', 'price': 'Free'},
                    {'title': 'Google Analytics', 'source': 'Google', 'rating': '4.7', 'url': 'https://analytics.google.com/analytics/web/', 'price': 'Free'}
                ],
                'Beginner': [
                    {'title': 'Data Science with Python', 'source': 'DataCamp', 'rating': '4.7', 'url': 'https://www.datacamp.com/', 'price': '$25/month'},
                    {'title': 'Machine Learning Basics', 'source': 'Coursera', 'rating': '4.8', 'url': 'https://www.coursera.org/learn/machine-learning', 'price': '$49/month'},
                    {'title': 'NumPy Fundamentals', 'source': 'DataCamp', 'rating': '4.6', 'url': 'https://www.datacamp.com/courses/numpy-basics', 'price': '$25/month'},
                    {'title': 'Matplotlib Visualization', 'source': 'Udemy', 'rating': '4.6', 'url': 'https://www.udemy.com/course/data-visualization-with-matplotlib/', 'price': '$64.99'},
                    {'title': 'Statistics with Python', 'source': 'Udacity', 'rating': '4.7', 'url': 'https://www.udacity.com/course/statistics-for-business--ud132', 'price': 'Free'},
                    {'title': 'SQL Bootcamp', 'source': 'Udemy', 'rating': '4.7', 'url': 'https://www.udemy.com/course/the-complete-sql-bootcamp/', 'price': '$74.99'},
                    {'title': 'Scikit-learn Basics', 'source': 'DataCamp', 'rating': '4.6', 'url': 'https://www.datacamp.com/courses/machine-learning-with-scikit-learn', 'price': '$25/month'},
                    {'title': 'Data Wrangling', 'source': 'Coursera', 'rating': '4.6', 'url': 'https://www.coursera.org/learn/data-wrangling', 'price': '$49/month'},
                    {'title': 'Power BI Essentials', 'source': 'Microsoft', 'rating': '4.7', 'url': 'https://learn.microsoft.com/en-us/training/modules/power-bi/', 'price': 'Free'},
                    {'title': 'Statistics Foundation', 'source': 'LinkedIn Learning', 'rating': '4.6', 'url': 'https://www.linkedin.com/learning/topics/statistics', 'price': '$39.99/month'}
                ],
                'Intermediate': [
                    {'title': 'Advanced ML Algorithms', 'source': 'Coursera', 'rating': '4.7', 'url': 'https://www.coursera.org/learn/advanced-machine-learning', 'price': '$49/month'},
                    {'title': 'Deep Learning Fundamentals', 'source': 'Udacity', 'rating': '4.8', 'url': 'https://www.udacity.com/course/deep-learning--ud730', 'price': 'Free'},
                    {'title': 'Feature Engineering', 'source': 'Udemy', 'rating': '4.7', 'url': 'https://www.udemy.com/course/feature-engineering/', 'price': '$79.99'},
                    {'title': 'TensorFlow for ML', 'source': 'Coursera', 'rating': '4.7', 'url': 'https://www.coursera.org/learn/introduction-tensorflow', 'price': '$49/month'},
                    {'title': 'PyTorch Essentials', 'source': 'Udacity', 'rating': '4.7', 'url': 'https://www.udacity.com/course/intro-to-machine-learning-with-pytorch--ud187', 'price': 'Free'},
                    {'title': 'NLP Fundamentals', 'source': 'Coursera', 'rating': '4.6', 'url': 'https://www.coursera.org/learn/natural-language-processing', 'price': '$49/month'},
                    {'title': 'Time Series Forecasting', 'source': 'Udemy', 'rating': '4.6', 'url': 'https://www.udemy.com/course/time-series-analysis-and-forecasting/', 'price': '$84.99'},
                    {'title': 'Statistical Learning', 'source': 'Stanford', 'rating': '4.8', 'url': 'https://www.statlearning.com/', 'price': 'Free'},
                    {'title': 'Tableau Advanced', 'source': 'Udemy', 'rating': '4.6', 'url': 'https://www.udemy.com/course/tableau-2021-advanced-training/', 'price': '$69.99'},
                    {'title': 'Data Ethics', 'source': 'Coursera', 'rating': '4.6', 'url': 'https://www.coursera.org/learn/data-ethics', 'price': '$49/month'}
                ],
                'Advanced': [
                    {'title': 'Advanced Deep Learning', 'source': 'MIT', 'rating': '4.9', 'url': 'https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-s191-introduction-to-deep-learning-january-iap-2020/', 'price': 'Free'},
                    {'title': 'Reinforcement Learning', 'source': 'DeepMind', 'rating': '4.8', 'url': 'https://deepmind.com/learning-resources/', 'price': 'Free'},
                    {'title': 'Large Language Models', 'source': 'Coursera', 'rating': '4.8', 'url': 'https://www.coursera.org/learn/generative-ai-with-llms', 'price': '$49/month'},
                    {'title': 'Computer Vision', 'source': 'Stanford', 'rating': '4.8', 'url': 'http://cs231n.stanford.edu/', 'price': 'Free'},
                    {'title': 'Advanced NLP', 'source': 'CMU', 'rating': '4.8', 'url': 'https://phontron.com/teaching.html', 'price': 'Free'},
                    {'title': 'Bayesian Methods', 'source': 'Coursera', 'rating': '4.7', 'url': 'https://www.coursera.org/learn/bayesian-statistics', 'price': '$49/month'},
                    {'title': 'MLOps Fundamentals', 'source': 'Databricks', 'rating': '4.7', 'url': 'https://databricks.com/training/', 'price': '$300'},
                    {'title': 'Causal Inference', 'source': 'Udacity', 'rating': '4.6', 'url': 'https://www.udacity.com/course/causal-inference--ud905', 'price': 'Free'},
                    {'title': 'Research Paper Writing', 'source': 'Stanford', 'rating': '4.7', 'url': 'https://web.stanford.edu/class/ee376a/', 'price': 'Free'},
                    {'title': 'Advanced Statistics', 'source': 'MIT', 'rating': '4.8', 'url': 'https://ocw.mit.edu/courses/mathematics/18-650-statistics-for-applications-fall-2016/', 'price': 'Free'}
                ]
            }
        }
        
    # Get domain-specific courses or use generic ones
    domain_courses = None
    for key in courses_db:
        if key in domain_lower:
            domain_courses = courses_db[key].get(level, courses_db[key].get('Beginner', []))
            break
    
    # If no specific domain found, use generic courses
    if not domain_courses:
        domain_courses = [
            {'title': f'{domain_name} Basics on Udemy', 'source': 'Udemy', 'rating': '4.6', 'url': f'https://www.udemy.com/courses/search/?q={domain_name.replace(" ", "+")}', 'price': '$79.99'},
            {'title': f'{domain_name} on Coursera', 'source': 'Coursera', 'rating': '4.7', 'url': f'https://www.coursera.org/search?query={domain_name.replace(" ", "+")}', 'price': '$49/month'},
            {'title': f'{domain_name} on edX', 'source': 'edX', 'rating': '4.6', 'url': f'https://www.edx.org/search?q={domain_name.replace(" ", "+")}', 'price': 'Free'},
            {'title': f'{domain_name} Tutorial - GeeksforGeeks', 'source': 'GeeksforGeeks', 'rating': '4.7', 'url': 'https://www.geeksforgeeks.org/', 'price': 'Free'},
            {'title': f'{domain_name} on YouTube', 'source': 'YouTube', 'rating': '4.5', 'url': f'https://www.youtube.com/results?search_query={domain_name.replace(" ", "+")}+tutorial', 'price': 'Free'},
            {'title': f'{domain_name} on DataCamp', 'source': 'DataCamp', 'rating': '4.6', 'url': 'https://www.datacamp.com/', 'price': '$25/month'},
            {'title': f'{domain_name} on FreeCodeCamp', 'source': 'FreeCodeCamp', 'rating': '4.8', 'url': 'https://www.freecodecamp.org/', 'price': 'Free'},
            {'title': f'{domain_name} on Codecademy', 'source': 'Codecademy', 'rating': '4.6', 'url': 'https://www.codecademy.com/', 'price': '$19.99/month'},
            {'title': f'{domain_name} on LinkedIn Learning', 'source': 'LinkedIn Learning', 'rating': '4.6', 'url': 'https://www.linkedin.com/learning/search?keywords=' + domain_name.replace(" ", "+"), 'price': '$39.99/month'},
            {'title': f'{domain_name} on Pluralsight', 'source': 'Pluralsight', 'rating': '4.7', 'url': 'https://www.pluralsight.com/', 'price': '$29/month'}
        ]
    
    # Return exactly 10 courses
    return domain_courses[:10] if len(domain_courses) >= 10 else (domain_courses + [
        {'title': 'More Resources Available', 'source': 'Various', 'rating': '4.5', 'url': 'https://www.google.com/search?q=learn+' + domain_name.replace(" ", "+")}
    ] * (10 - len(domain_courses)))[:10]


def generate_certificate_code(domain_name, course_title):
    prefix = re.sub(r'[^A-Za-z]', '', domain_name)[:2].upper() or 'SF'
    course_hint = re.sub(r'[^A-Za-z]', '', course_title)[:2].upper() or 'CR'
    return f"SF-{prefix}{course_hint}-{secrets.token_hex(3).upper()}"


def score_to_grade(score):
    if score >= 95:
        return 'A+'
    if score >= 90:
        return 'A'
    if score >= 85:
        return 'A-'
    if score >= 80:
        return 'B+'
    if score >= 75:
        return 'B'
    return 'C'


def build_course_quiz(domain_name, course_title, num_questions=10):
    """Create a quiz payload for a domain course link"""
    questions = []
    for idx in range(1, num_questions + 1):
        options = [
            f"{domain_name} concept related to {course_title}",
            f"Alternative concept {idx}",
            f"Common misconception {idx}",
            f"Unrelated option {idx}"
        ]
        questions.append({
            'id': idx,
            'question': f"Q{idx}: Which statement best fits the topic of {course_title}?",
            'options': options,
            'correct_index': 0
        })
    return {
        'title': f"{course_title} - Final Quiz",
        'description': f"Complete the quiz to unlock your {domain_name} certificate.",
        'questions': questions
    }


@app.route('/api/domain/<int:domain_id>/submit-level-quiz', methods=['POST'])
def api_submit_level_quiz(domain_id):
    """Submit level assessment and get custom course links"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        answers = data.get('answers', [])
        
        # Score the quiz - normalize answer values
        level_scores = {'zero': 0, 'beginner': 0, 'intermediate': 0, 'advanced': 0}
        for answer in answers:
            value = answer.get('value', 'zero').lower()
            # Map various answer types to levels
            if 'advanced' in value or value == 'advanced':
                level_scores['advanced'] += 1
            elif 'intermediate' in value or value == 'intermediate':
                level_scores['intermediate'] += 1
            elif 'beginner' in value or value == 'beginner':
                level_scores['beginner'] += 1
            else:
                # Default to zero for any other value
                level_scores['zero'] += 1
        
        # Determine final level
        if level_scores['advanced'] >= 2:
            final_level = 'Advanced'
        elif level_scores['intermediate'] >= 2:
            final_level = 'Intermediate'
        elif level_scores['beginner'] >= 2:
            final_level = 'Beginner'
        else:
            final_level = 'Zero'
        
        # Get domain name
        domain = Domain.query.get(domain_id)
        if not domain:
            return jsonify({'error': 'Domain not found'}), 404
        
        print(f"DEBUG: Submitting assessment - Domain: {domain.name}, Level: {final_level}, Answers: {len(answers)}")
        
        # Update user's enrollment
        enrollment = DomainEnrollment.query.filter_by(
            user_id=session['user_id'],
            domain_id=domain_id
        ).first()
        if enrollment:
            enrollment.assessed_level = final_level
            db.session.commit()
            print(f"DEBUG: Updated enrollment for user {session['user_id']}, domain {domain_id}")
        
        # Get top 10 courses for the domain and assessed level
        top_courses = get_top_10_courses(domain.name, final_level)
        
        print(f"DEBUG: Generated {len(top_courses)} courses for {domain.name} at {final_level} level")

        # Persist course links and attach IDs
        enriched_courses = []
        for course in top_courses:
            inferred_duration = infer_course_duration_minutes(course.get('title'), course.get('source'))
            existing = CourseLink.query.filter_by(url=course['url']).first()
            if not existing:
                existing = CourseLink(
                    domain_id=domain.id,
                    title=course['title'],
                    url=course['url'],
                    source=course.get('source'),
                    rating=float(course.get('rating') or 0),
                    duration_minutes=inferred_duration,
                    price=course.get('price', 'Free'),
                    language=course.get('language', 'English'),
                    difficulty=final_level
                )
                db.session.add(existing)
                db.session.flush()
            elif not existing.duration_minutes:
                existing.duration_minutes = inferred_duration
            enriched = dict(course)
            enriched['course_link_id'] = existing.id
            enriched['duration_minutes'] = existing.duration_minutes
            enriched_courses.append(enriched)

        db.session.commit()
        
        # Return assessment results with courses
        response = {
            'success': True,
            'assessed_level': final_level,
            'message': f'Assessment complete! You\'ve been placed at {final_level} level.',
            'domain': domain.name,
            'top_courses': enriched_courses
        }
        
        print(f"DEBUG: Returning response with {len(response['top_courses'])} courses")
        return jsonify(response)
        
    except Exception as e:
        print(f"ERROR in api_submit_level_quiz: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/domain/<int:domain_id>/course/<int:course_link_id>/progress', methods=['GET', 'POST'])
def api_domain_course_progress(domain_id, course_link_id):
    print(f"📊 Progress API called: domain_id={domain_id}, course_link_id={course_link_id}, method={request.method}")
    
    if 'user_id' not in session:
        print("❌ User not logged in")
        return jsonify({'error': 'Not logged in'}), 401

    print(f"✅ User ID: {session['user_id']}")

    progress = DomainCourseProgress.query.filter_by(
        user_id=session['user_id'],
        domain_id=domain_id,
        course_link_id=course_link_id
    ).first()

    if request.method == 'GET':
        required_minutes = get_required_minutes_for_course(course_link_id)
        if not progress:
            print("📝 No progress record found, returning zeros")
            return jsonify({'tutorial_minutes': 0, 'completed': False, 'quiz_unlocked': False, 'quiz_passed': False, 'required_minutes': required_minutes, 'required_label': format_duration_label(required_minutes)})
        print(f"📝 Found progress: {progress.tutorial_minutes} minutes")
        return jsonify({
            'tutorial_minutes': progress.tutorial_minutes,
            'completed': progress.completed_at is not None,
            'quiz_unlocked': progress.quiz_unlocked,
            'quiz_passed': progress.quiz_passed,
            'required_minutes': required_minutes,
            'required_label': format_duration_label(required_minutes)
        })

    data = request.get_json() or {}
    minutes = int(data.get('minutes', 0))
    mark_complete = bool(data.get('mark_complete'))
    
    print(f"💾 POST request: minutes={minutes}, mark_complete={mark_complete}")

    try:
        newly_completed = False
        required_minutes = get_required_minutes_for_course(course_link_id)
        if not progress:
            print("🆕 Creating new progress record")
            progress = DomainCourseProgress(
                user_id=session['user_id'],
                domain_id=domain_id,
                course_link_id=course_link_id,
                tutorial_minutes=0
            )
            db.session.add(progress)

        if minutes > 0:
            old_minutes = progress.tutorial_minutes or 0
            current_minutes = old_minutes + minutes
            progress.tutorial_minutes = min(current_minutes, required_minutes)
            print(f"⏱️ Updated minutes: {old_minutes} -> {progress.tutorial_minutes}")

        if mark_complete or progress.tutorial_minutes >= required_minutes:
            progress.tutorial_minutes = required_minutes
            if not progress.completed_at:
                progress.completed_at = datetime.datetime.utcnow()
                newly_completed = True
            progress.quiz_unlocked = True
            print(f"🔓 Quiz unlocked! Tutorial complete.")

        schedule = None
        if newly_completed and progress.completed_at:
            schedule = ensure_test_alert_schedule(
                user_id=session['user_id'],
                domain_id=domain_id,
                course_link_id=course_link_id,
                completed_at=progress.completed_at
            )

        progress.updated_at = datetime.datetime.utcnow()
        print("💾 Committing to database...")
        db.session.commit()
        print("✅ Progress saved successfully!")

        if newly_completed and schedule:
            user = User.query.get(session['user_id'])
            domain = Domain.query.get(domain_id)
            course_link = CourseLink.query.get(course_link_id)

            completion_payload = {
                'user_id': session['user_id'],
                'username': user.username if user else None,
                'email': user.email if user else None,
                'domain_id': domain_id,
                'domain_name': domain.name if domain else None,
                'course_link_id': course_link_id,
                'course_title': course_link.title if course_link else None,
                'completed_at': progress.completed_at.isoformat() + 'Z' if progress.completed_at else None
            }
            scheduling_payload = {
                'user_id': session['user_id'],
                'domain_id': domain_id,
                'domain_name': domain.name if domain else None,
                'course_link_id': course_link_id,
                'course_title': course_link.title if course_link else None,
                'alert_interval_minutes': get_alert_interval_minutes(),
                'required_minutes': required_minutes,
                'next_alert_at': schedule.next_alert_at.isoformat() + 'Z' if schedule.next_alert_at else None,
                'active': schedule.active
            }

            completion_sent = notify_launch_pipeline('course_completed', completion_payload)
            scheduling_sent = notify_launch_pipeline('test_scheduling_initiated', scheduling_payload)

            if completion_sent or scheduling_sent:
                db.session.refresh(schedule)
                if completion_sent:
                    schedule.completion_notified = True
                if scheduling_sent:
                    schedule.scheduling_notified = True
                schedule.updated_at = datetime.datetime.utcnow()
                db.session.commit()

        response_data = {
            'tutorial_minutes': progress.tutorial_minutes,
            'completed': progress.completed_at is not None,
            'quiz_unlocked': progress.quiz_unlocked,
            'quiz_passed': progress.quiz_passed,
            'required_minutes': required_minutes,
            'required_label': format_duration_label(required_minutes)
        }
        print(f"📤 Returning: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving progress: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@app.route('/api/domain/<int:domain_id>/course/<int:course_link_id>/quiz/start', methods=['POST'])
def api_domain_course_quiz_start(domain_id, course_link_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    progress = DomainCourseProgress.query.filter_by(
        user_id=session['user_id'],
        domain_id=domain_id,
        course_link_id=course_link_id
    ).first()

    if not progress or not progress.quiz_unlocked:
        return jsonify({'error': tutorial_requirement_text(get_required_minutes_for_course(course_link_id))}), 403

    course_link = CourseLink.query.get(course_link_id)
    domain = Domain.query.get(domain_id)
    if not course_link or not domain:
        return jsonify({'error': 'Course link not found'}), 404

    quiz = DomainCourseQuiz.query.filter_by(domain_id=domain_id, course_link_id=course_link_id).first()
    if not quiz:
        quiz_payload = build_course_quiz(domain.name, course_link.title)
        quiz = DomainCourseQuiz(
            domain_id=domain_id,
            course_link_id=course_link_id,
            title=quiz_payload['title'],
            quiz_data=json.dumps(quiz_payload)
        )
        db.session.add(quiz)
        db.session.commit()
    else:
        quiz_payload = json.loads(quiz.quiz_data)

    attempt = DomainCourseQuizAttempt(
        user_id=session['user_id'],
        domain_id=domain_id,
        course_link_id=course_link_id,
        quiz_data=json.dumps(quiz_payload),
        session_token=secrets.token_urlsafe(32),
        started_at=datetime.datetime.utcnow(),
        last_heartbeat_at=datetime.datetime.utcnow(),
        invalidated=False
    )
    db.session.add(attempt)
    db.session.commit()

    stop_test_alert_schedule(
        user_id=session['user_id'],
        domain_id=domain_id,
        course_link_id=course_link_id
    )

    return jsonify({
        'quiz': quiz_payload,
        'session_token': attempt.session_token
    })


@app.route('/api/domain/<int:domain_id>/course/<int:course_link_id>/duration', methods=['POST'])
def api_domain_course_duration(domain_id, course_link_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    enrollment = DomainEnrollment.query.filter_by(
        user_id=session['user_id'],
        domain_id=domain_id
    ).first()
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this domain'}), 403

    course_link = CourseLink.query.filter_by(id=course_link_id, domain_id=domain_id).first()
    if not course_link:
        return jsonify({'error': 'Course link not found'}), 404

    data = request.get_json() or {}
    minutes = data.get('duration_minutes')
    hours = data.get('duration_hours')

    if minutes is None and hours is None:
        return jsonify({'error': 'duration_minutes or duration_hours is required'}), 400

    try:
        if minutes is not None:
            required_minutes = int(minutes)
        else:
            required_minutes = int(round(float(hours) * 60))
    except Exception:
        return jsonify({'error': 'Invalid duration value'}), 400

    required_minutes = max(15, min(required_minutes, 1200))
    course_link.duration_minutes = required_minutes
    db.session.commit()

    return jsonify({
        'course_link_id': course_link.id,
        'duration_minutes': course_link.duration_minutes,
        'required_label': format_duration_label(course_link.duration_minutes)
    })


@app.route('/api/domain/<int:domain_id>/course/<int:course_link_id>/quiz/heartbeat', methods=['POST'])
def api_domain_course_quiz_heartbeat(domain_id, course_link_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json() or {}
    token = data.get('session_token')
    attempt = DomainCourseQuizAttempt.query.filter_by(
        user_id=session['user_id'],
        domain_id=domain_id,
        course_link_id=course_link_id,
        session_token=token
    ).first()

    if not attempt or attempt.invalidated:
        return jsonify({'error': 'Quiz session invalid'}), 403

    attempt.last_heartbeat_at = datetime.datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/domain/<int:domain_id>/course/<int:course_link_id>/quiz/violation', methods=['POST'])
def api_domain_course_quiz_violation(domain_id, course_link_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json() or {}
    token = data.get('session_token')
    reason = data.get('reason', 'focus_lost')
    attempt = DomainCourseQuizAttempt.query.filter_by(
        user_id=session['user_id'],
        domain_id=domain_id,
        course_link_id=course_link_id,
        session_token=token
    ).first()

    if not attempt:
        return jsonify({'error': 'Quiz session not found'}), 404

    if attempt.completed_at:
        return jsonify({'ok': True, 'violations': int(attempt.violation_count or 0), 'invalidated': bool(attempt.invalidated)}), 200

    max_violations = int(app.config.get('QUIZ_MAX_VIOLATIONS', 3))
    attempt.violation_count = int(attempt.violation_count or 0) + 1
    attempt.violation_reason = reason

    if attempt.violation_count >= max_violations:
        attempt.invalidated = True
        attempt.completed_at = datetime.datetime.utcnow()

    db.session.commit()
    return jsonify({
        'ok': True,
        'violations': attempt.violation_count,
        'max_violations': max_violations,
        'invalidated': bool(attempt.invalidated)
    })


@app.route('/api/domain/<int:domain_id>/course/<int:course_link_id>/quiz/submit', methods=['POST'])
def api_domain_course_quiz_submit(domain_id, course_link_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json() or {}
    token = data.get('session_token')
    answers = data.get('answers', [])

    attempt = DomainCourseQuizAttempt.query.filter_by(
        user_id=session['user_id'],
        domain_id=domain_id,
        course_link_id=course_link_id,
        session_token=token
    ).first()

    if not attempt:
        return jsonify({'error': 'Quiz session not found'}), 404

    if attempt.invalidated:
        return jsonify({'error': 'Quiz invalidated due to proctoring violation.'}), 403

    timeout_seconds = int(app.config.get('QUIZ_HEARTBEAT_TIMEOUT_SECONDS', 90))
    if attempt.last_heartbeat_at and (datetime.datetime.utcnow() - attempt.last_heartbeat_at).total_seconds() > timeout_seconds:
        attempt.invalidated = True
        attempt.violation_reason = 'heartbeat_timeout'
        attempt.completed_at = datetime.datetime.utcnow()
        db.session.commit()
        return jsonify({'error': 'Quiz session expired.'}), 403

    quiz_payload = json.loads(attempt.quiz_data)
    questions = quiz_payload.get('questions', [])
    total = len(questions)

    if isinstance(answers, dict):
        answers = [answers.get(str(i), answers.get(i)) for i in range(total)]
    elif not isinstance(answers, list):
        answers = []

    correct = 0
    for idx, q in enumerate(questions):
        expected = q.get('correct_index')
        selected = answers[idx] if idx < len(answers) else None
        try:
            if selected is not None and expected is not None and int(selected) == int(expected):
                correct += 1
        except (TypeError, ValueError):
            continue

    score_pct = int(round((correct / total) * 100)) if total > 0 else 0
    pass_threshold = int(app.config.get('QUIZ_PASS_THRESHOLD', 70))
    passed = score_pct >= pass_threshold

    attempt.score = score_pct
    attempt.total_questions = total
    attempt.passed = passed
    attempt.completed_at = datetime.datetime.utcnow()
    db.session.commit()

    progress = DomainCourseProgress.query.filter_by(
        user_id=session['user_id'],
        domain_id=domain_id,
        course_link_id=course_link_id
    ).first()

    if progress:
        progress.quiz_passed = passed
        progress.updated_at = datetime.datetime.utcnow()

    certificate = None
    if passed:
        course_link = CourseLink.query.get(course_link_id)
        domain = Domain.query.get(domain_id)
        existing_cert = DomainCertificate.query.filter_by(
            user_id=session['user_id'],
            domain_id=domain_id,
            course_link_id=course_link_id
        ).first()
        if existing_cert:
            certificate = existing_cert
        elif course_link and domain:
            code = generate_certificate_code(domain.name, course_link.title)
            certificate = DomainCertificate(
                user_id=session['user_id'],
                domain_id=domain_id,
                course_link_id=course_link_id,
                title=f"{domain.name} - Certificate of Completion",
                certificate_code=code,
                grade=score_to_grade(score_pct),
                score=score_pct
            )
            db.session.add(certificate)

    db.session.commit()

    stop_test_alert_schedule(
        user_id=session['user_id'],
        domain_id=domain_id,
        course_link_id=course_link_id
    )

    user = User.query.get(session['user_id'])
    domain = Domain.query.get(domain_id)
    course_link = CourseLink.query.get(course_link_id)

    eval_payload = {
        'user_id': session['user_id'],
        'username': user.username if user else None,
        'email': user.email if user else None,
        'domain_id': domain_id,
        'domain_name': domain.name if domain else None,
        'course_link_id': course_link_id,
        'course_title': course_link.title if course_link else None,
        'score': score_pct,
        'threshold': pass_threshold,
        'passed': passed,
        'attempted_at': attempt.completed_at.isoformat() + 'Z' if attempt.completed_at else None
    }
    notify_launch_pipeline('test_evaluated', eval_payload)

    if passed and certificate:
        cert_payload = {
            'user_id': session['user_id'],
            'username': user.username if user else None,
            'email': user.email if user else None,
            'domain_id': domain_id,
            'domain_name': domain.name if domain else None,
            'course_link_id': course_link_id,
            'course_title': course_link.title if course_link else None,
            'certificate_id': certificate.id,
            'certificate_code': certificate.certificate_code,
            'certificate_title': certificate.title,
            'score': certificate.score,
            'issued_at': certificate.issued_at.isoformat() + 'Z' if certificate.issued_at else None
        }
        notify_launch_pipeline('certificate_generated', cert_payload)

    return jsonify({
        'score': score_pct,
        'passed': passed,
        'certificate_id': certificate.id if certificate else None
    })


@app.route('/domain/<int:domain_id>/course/<int:course_link_id>/quiz')
def domain_course_quiz(domain_id, course_link_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    domain = Domain.query.get(domain_id)
    course_link = CourseLink.query.get(course_link_id)
    if not domain or not course_link:
        flash('Course not found', 'error')
        return redirect(url_for('domains'))
    return render_template('domain_quiz.html', domain=domain, course=course_link)


@app.route('/api/certificates')
def api_certificates():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    certs = DomainCertificate.query.filter_by(user_id=session['user_id']).order_by(DomainCertificate.issued_at.desc()).all()
    results = []
    for cert in certs:
        results.append({
            'id': cert.id,
            'domain': cert.domain.name if cert.domain else 'Domain',
            'course_title': cert.course_link.title if cert.course_link else 'Course',
            'title': cert.title,
            'issuer': cert.issuer,
            'date': cert.issued_at.strftime('%B %d, %Y'),
            'certificateId': cert.certificate_code,
            'grade': cert.grade,
            'score': cert.score,
            'duration': '5 hours',
            'icon': cert.domain.icon if cert.domain else '🏆',
            'isSample': False
        })

    sample = {
        'id': 'sample',
        'domain': 'Sample Domain',
        'course_title': 'Sample Course',
        'title': 'Sample Certificate',
        'issuer': 'SkillForge Academy',
        'date': datetime.datetime.utcnow().strftime('%B %d, %Y'),
        'certificateId': 'SF-SAMPLE-0001',
        'grade': 'A',
        'score': 90,
        'duration': '5 hours',
        'icon': '🏆',
        'isSample': True
    }

    results.insert(0, sample)
    return jsonify({'certificates': results})


@app.route('/api/certificates/<cert_id>')
def api_certificate_detail(cert_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    if cert_id == 'sample':
        cert_data = {
            'id': 'sample',
            'domain': 'Sample Domain',
            'title': 'Sample Certificate',
            'issuer': 'SkillForge Academy',
            'issued_at': datetime.datetime.utcnow().isoformat(),
            'certificate_code': 'SF-SAMPLE-0001',
            'grade': 'A',
            'score': 90
        }
        return jsonify({
            'certificate': cert_data,
            'user_name': session.get('username', 'User')
        })
    else:
        cert = DomainCertificate.query.get(cert_id)
        if not cert or cert.user_id != session['user_id']:
            return jsonify({'error': 'Certificate not found'}), 404

        cert_data = {
            'id': cert.id,
            'domain': cert.domain.name if cert.domain else 'Domain',
            'title': cert.title,
            'issuer': cert.issuer,
            'issued_at': cert.issued_at.isoformat(),
            'certificate_code': cert.certificate_code,
            'grade': cert.grade,
            'score': cert.score
        }
        return jsonify({
            'certificate': cert_data,
            'user_name': session.get('username', 'User')
        })


@app.route('/certificates/<cert_id>/view')
def certificate_view(cert_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cert = DomainCertificate.query.get(cert_id) if cert_id != 'sample' else None
    if cert_id != 'sample' and (not cert or cert.user_id != session['user_id']):
        flash('Certificate not found', 'error')
        return redirect(url_for('certificates'))

    cert_data = {
        'id': cert.id if cert else 'sample',
        'domain': cert.domain.name if cert else 'Sample Domain',
        'course_title': cert.course_link.title if cert else 'Sample Course',
        'title': cert.title if cert else 'Sample Certificate',
        'issuer': cert.issuer if cert else 'SkillForge Academy',
        'issued_at': cert.issued_at.isoformat() if cert else datetime.datetime.utcnow().isoformat(),
        'certificate_code': cert.certificate_code if cert else 'SF-SAMPLE-0001',
        'grade': cert.grade if cert else 'A',
        'score': cert.score if cert else 90
    }

    return render_template(
        'certificate_view.html',
        cert=cert_data,
        user_name=session.get('username', 'User Name'),
        app_base_url=request.url_root.rstrip('/')
    )


@app.route('/certificates/<cert_id>/download')
def certificate_download(cert_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cert = DomainCertificate.query.get(cert_id) if cert_id != 'sample' else None
    if cert_id != 'sample' and (not cert or cert.user_id != session['user_id']):
        flash('Certificate not found', 'error')
        return redirect(url_for('certificates'))

    if cert_id == 'sample':
        filename = 'sample-certificate.html'
    else:
        filename = f"certificate-{cert.certificate_code}.html"

    cert_data = {
        'id': cert.id if cert else 'sample',
        'domain': cert.domain.name if cert else 'Sample Domain',
        'course_title': cert.course_link.title if cert else 'Sample Course',
        'title': cert.title if cert else 'Sample Certificate',
        'issuer': cert.issuer if cert else 'SkillForge Academy',
        'issued_at': cert.issued_at.isoformat() if cert else datetime.datetime.utcnow().isoformat(),
        'date': cert.issued_at.strftime('%B %d, %Y') if cert else datetime.datetime.utcnow().strftime('%B %d, %Y'),
        'certificateId': cert.certificate_code if cert else 'SF-SAMPLE-0001',
        'certificate_code': cert.certificate_code if cert else 'SF-SAMPLE-0001',
        'grade': cert.grade if cert else 'A',
        'score': cert.score if cert else 90
    }

    owner_username = cert.user.username if cert and cert.user else session.get('username', 'User')
    verification_url = url_for(
        'certificate_verify',
        code=cert_data['certificate_code'],
        user=owner_username,
        _external=True
    )
    app_url = url_for('certificates', _external=True)

    html = render_template(
        'certificate_download.html',
        cert=cert_data,
        user_name=owner_username,
        verification_url=verification_url,
        app_url=app_url
    )
    response = app.make_response(html)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/html'
    return response


@app.route('/certificates/verify')
def certificate_verify():
    code = (request.args.get('code') or '').strip()
    username = (request.args.get('user') or '').strip()
    sample_code = 'SF-SAMPLE-0001'

    cert = None
    is_valid = False
    message = 'Invalid verification link.'

    if code and username:
        if code == sample_code:
            # Sample certificates are not persisted in DB, so validate by known sample code.
            is_valid = True
            message = 'Sample certificate is valid for demonstration purposes.'
        else:
            cert = DomainCertificate.query.join(User).filter(
                DomainCertificate.certificate_code == code,
                User.username == username
            ).first()

            if cert:
                is_valid = True
                message = 'Certificate is valid and belongs to this user.'
            else:
                cert_with_code = DomainCertificate.query.filter_by(certificate_code=code).first()
                if cert_with_code:
                    message = 'Certificate code exists but does not belong to this user.'
                else:
                    message = 'Certificate code was not found.'
    elif code:
        if code == sample_code:
            message = 'Certificate exists. Provide a username to validate ownership.'
        else:
            cert_with_code = DomainCertificate.query.filter_by(certificate_code=code).first()
            if cert_with_code:
                message = 'Certificate exists. Provide a username to validate ownership.'
            else:
                message = 'Certificate code was not found.'

    cert_data = None
    if code == sample_code and is_valid:
        cert_data = {
            'domain': 'Sample Domain',
            'course_title': 'Sample Course',
            'title': 'Sample Certificate',
            'issuer': 'SkillForge Academy',
            'issued_at': datetime.datetime.utcnow(),
            'certificate_code': sample_code,
            'grade': 'A',
            'score': 90,
            'username': username
        }
    elif cert:
        cert_data = {
            'domain': cert.domain.name if cert.domain else 'Domain',
            'course_title': cert.course_link.title if cert.course_link else 'Course',
            'title': cert.title,
            'issuer': cert.issuer,
            'issued_at': cert.issued_at,
            'certificate_code': cert.certificate_code,
            'grade': cert.grade,
            'score': cert.score,
            'username': cert.user.username if cert.user else username
        }

    return render_template(
        'certificate_verify.html',
        is_valid=is_valid,
        message=message,
        cert=cert_data,
        checked_code=code,
        checked_user=username
    )


# ==================================================================
# Enrollment Routes
# ==================================================================

@app.route('/api/enroll', methods=['POST'])
def api_enroll():
    """Save enrollment after quiz completion"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    course_id = data.get('course_id')
    level_assessed = data.get('level_assessed')
    recommended_lesson_id = data.get('recommended_lesson_id')
    
    try:
        # Create/update enrollment
        enrollment = DomainEnrollment.query.filter_by(
            user_id=user_id,
            domain_id=course_id
        ).first()
        
        if enrollment:
            enrollment.assessed_level = level_assessed
            enrollment.learning_phase = 'course-selection'
        else:
            enrollment = DomainEnrollment(
                user_id=user_id,
                domain_id=course_id,
                assessed_level=level_assessed,
                learning_phase='course-selection'
            )
            db.session.add(enrollment)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Enrollment saved'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



# ==================================================================
# Continue with remaining API Routes
# ==================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            flash('Form tampered or session expired. Please try again.', 'error')
            return redirect(url_for('login'))

        _ensure_pending_registration_table()

        identifier = request.form.get('identifier', '').strip()
        normalized_identifier = identifier.lower()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash('Please provide both identifier and password.', 'error')
            return redirect(url_for('login'))

        identifier_looks_like_email = '@' in normalized_identifier

        # If identifier looks like an email, prefer email lookup first.
        # This avoids accidental username collisions causing false "incorrect password" errors.
        if identifier_looks_like_email:
            user = User.query.filter(func.lower(User.email) == normalized_identifier).first()
            if not user:
                user = User.query.filter(User.username == identifier).first()
            if not user:
                user = User.query.filter(func.lower(User.username) == normalized_identifier).first()
        else:
            # For non-email identifiers, keep username-first behavior.
            user = User.query.filter(User.username == identifier).first()
            if not user:
                user = User.query.filter(func.lower(User.email) == normalized_identifier).first()
            if not user:
                user = User.query.filter(func.lower(User.username) == normalized_identifier).first()

        pending_account = None
        if not user:
            if identifier_looks_like_email:
                pending_account = PendingRegistration.query.filter(
                    func.lower(PendingRegistration.email) == normalized_identifier
                ).first()
                if not pending_account:
                    pending_account = PendingRegistration.query.filter(
                        PendingRegistration.username == identifier
                    ).first()
                if not pending_account:
                    pending_account = PendingRegistration.query.filter(
                        func.lower(PendingRegistration.username) == normalized_identifier
                    ).first()
            else:
                pending_account = PendingRegistration.query.filter(
                    PendingRegistration.username == identifier
                ).first()
                if not pending_account:
                    pending_account = PendingRegistration.query.filter(
                        func.lower(PendingRegistration.email) == normalized_identifier
                    ).first()
                if not pending_account:
                    pending_account = PendingRegistration.query.filter(
                        func.lower(PendingRegistration.username) == normalized_identifier
                    ).first()

        if user is None and pending_account:
            if not app.config.get('REQUIRE_EMAIL_VERIFICATION', True):
                # In no-verification mode, pending rows should transparently become real users.
                if _pending_registration_is_expired(pending_account):
                    db.session.delete(pending_account)
                    db.session.commit()
                    flash('Your pending registration expired. Please sign up again.', 'warning')
                    return redirect(url_for('signup'))

                pending_ok, _pending_was_legacy = _password_matches(pending_account.password_hash, password)
                if not pending_ok:
                    flash('Incorrect password. Please try again.', 'error')
                    return redirect(url_for('login'))

                collision = User.query.filter(
                    or_(
                        func.lower(User.username) == pending_account.username.lower(),
                        func.lower(User.email) == pending_account.email.lower()
                    )
                ).first()
                if collision:
                    db.session.delete(pending_account)
                    db.session.commit()
                    flash('Account already exists. Please log in.', 'info')
                    return redirect(url_for('login'))

                user = User(
                    username=pending_account.username,
                    email=pending_account.email,
                    password_hash=pending_account.password_hash,
                    created_at=datetime.datetime.utcnow(),
                    email_verified=True
                )
                db.session.add(user)
                db.session.delete(pending_account)
                db.session.commit()
                pending_account = None

            if pending_account and _pending_registration_is_expired(pending_account):
                db.session.delete(pending_account)
                db.session.commit()
                flash('Your verification link has expired. Please register again.', 'warning')
                return redirect(url_for('signup'))

            if pending_account:
                pending_ok, pending_was_legacy = _password_matches(pending_account.password_hash, password)
                if not pending_ok:
                    flash('Incorrect password. Please try again.', 'error')
                    return redirect(url_for('login'))

                flash('Your account is pending email verification. Please check your inbox and verify your email before logging in.', 'warning')
                return redirect(url_for('login'))

        if user is None:
            flash('Account not found. Please sign up first.', 'error')
            return redirect(url_for('login'))

        password_ok, upgraded_hash = _verify_user_password(user, password)
        if not password_ok:
            flash('Incorrect password. Please try again.', 'error')
            return redirect(url_for('login'))
        if upgraded_hash:
            db.session.commit()

        if app.config.get('REQUIRE_EMAIL_VERIFICATION', True) and not user.email_verified:
            flash('Please verify your email first. Check your inbox for the verification link.', 'warning')
            return redirect(url_for('login'))

        # clear CSRF after successful POST
        session.pop('csrf_token', None)
        session['user'] = user.username
        session['username'] = user.username
        session['email'] = user.email
        session['user_id'] = user.id

        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('dashboard'))
    
    # GET request - show login form
    csrf_token = secrets.token_hex(32)
    session['csrf_token'] = csrf_token
    return render_template('login.html', csrf_token=csrf_token)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/verify-email/<token>')
def verify_email(token):
    """Verify user email using the token sent in registration email."""
    table_ok, table_err = _ensure_pending_registration_table()
    if not table_ok:
        flash(f'Email verification setup error: {table_err}', 'error')
        return redirect(url_for('login'))

    pending = PendingRegistration.query.filter_by(token=token).first()

    if not pending:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('login'))
    
    # Check if token is expired
    if _pending_registration_is_expired(pending):
        flash(f'Verification link has expired after {_email_verification_expiry_minutes()} minutes. Please register again.', 'error')
        db.session.delete(pending)
        db.session.commit()
        return redirect(url_for('signup'))

    if User.query.filter(func.lower(User.username) == pending.username.lower()).first() or User.query.filter(func.lower(User.email) == pending.email.lower()).first():
        db.session.delete(pending)
        db.session.commit()
        flash('Account already exists. Please log in.', 'info')
        return redirect(url_for('login'))

    # Create user only after verification
    user = User(
        username=pending.username,
        email=pending.email,
        password_hash=pending.password_hash,
        created_at=datetime.datetime.utcnow(),
        email_verified=True
    )
    db.session.add(user)
    db.session.delete(pending)
    db.session.commit()
    
    flash(f'Email verified successfully! You have successfully registered. Now you can log in.', 'success')
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET','POST'])
def profile():
    if not session.get('user'):
        flash('Please log in to edit your profile.', 'error')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session.get('user')).first()
    if request.method == 'POST':
        if 'avatar' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('profile'))
        file = request.files['avatar']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('profile'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{user.username}_{int(datetime.datetime.utcnow().timestamp())}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            user.avatar = filename
            db.session.commit()
            flash('Avatar uploaded', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid file type', 'error')
            return redirect(url_for('profile'))
    return render_template('profile.html', user=user)


@app.route('/api/remove-avatar', methods=['POST'])
def remove_avatar():
    if not session.get('user'):
        flash('Please log in to remove your avatar.', 'error')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session.get('user')).first()
    if user and user.avatar:
        # Delete the file from disk
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], user.avatar)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
        
        # Clear avatar from database
        user.avatar = None
        db.session.commit()
        flash('Profile picture removed', 'success')
    return redirect(url_for('profile'))


@app.route('/api/users/recent')
def api_users_recent():
    items = []
    users_q = User.query.order_by(User.created_at.desc()).limit(5).all()
    for u in users_q:
        items.append({'username': u.username, 'email': u.email, 'joined': u.created_at.isoformat()})
    return jsonify(items)


@app.route('/domains')
def domains():
    if not session.get('user'):
        flash('Please log in to choose a domain.', 'error')
        return redirect(url_for('login'))
    ensure_domains_seeded_if_empty()
    user = User.query.filter_by(username=session.get('user')).first()
    domain_rows = Domain.query.order_by(Domain.id.asc()).all()
    initial_domains = [
        {
            'id': d.id,
            'name': d.name,
            'description': d.description,
            'icon': d.icon,
            'keywords': d.keywords or ''
        }
        for d in domain_rows
    ]
    return render_template('domains.html', user=user, initial_domains=initial_domains)


@app.route('/domain/<int:domain_id>/learn')
def domain_learn(domain_id):
    """Learning page for a domain - displays selected course link"""
    if not session.get('user'):
        flash('Please log in to access this domain.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session.get('user')).first()
    domain = Domain.query.get(domain_id)
    
    if not domain:
        flash('Domain not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if user is enrolled in this domain
    enrollment = DomainEnrollment.query.filter_by(
        user_id=user.id,
        domain_id=domain_id
    ).first()
    
    if not enrollment:
        flash('You are not enrolled in this domain.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get course links available for this domain
    course_links = CourseLink.query.filter_by(domain_id=domain_id).all()
    durations_backfilled = False
    pricing_backfilled = False
    for link in course_links:
        if not link.duration_minutes:
            link.duration_minutes = infer_course_duration_minutes(link.title, link.source)
            durations_backfilled = True
        if (link.source or '').strip().lower() == 'udemy' and (not link.price or str(link.price).strip().lower() == 'free'):
            link.price = '$79.99'
            pricing_backfilled = True
        if (link.source or '').strip().lower() == 'coursera' and (not link.price or str(link.price).strip().lower() == 'free'):
            link.price = '$49/month'
            pricing_backfilled = True
    if durations_backfilled or pricing_backfilled:
        db.session.commit()
    
    # Get or pick the preferred course link
    selected_course = None
    
    # Check if course_id is provided in query parameters
    course_id = request.args.get('course', type=int)
    if course_id:
        selected_course = CourseLink.query.filter_by(
            id=course_id,
            domain_id=domain_id
        ).first()
    
    # If not found by query param, try stored preference
    if not selected_course and enrollment.preferred_course_link:
        selected_course = CourseLink.query.filter_by(
            domain_id=domain_id,
            url=enrollment.preferred_course_link
        ).first()
    
    return render_template(
        'domain_learn.html',
        user=user,
        domain=domain,
        enrollment=enrollment,
        selected_course=selected_course,
        course_links=course_links,
        default_required_minutes=get_course_completion_minutes()
    )


@app.route('/courses')
def courses():
    return redirect(url_for('domains'))


@app.route('/challenges')
def challenges():
    if not session.get('user'):
        flash('Please log in to access challenges.', 'error')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session.get('user')).first()
    return render_template('challenges.html', user=user)


@app.route('/certificates')
def certificates():
    if not session.get('user'):
        flash('Please log in to access certificates.', 'error')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session.get('user')).first()
    return render_template('certificates.html', user=user)


@app.route('/ai-guidance')
def ai_guidance():
    if not session.get('user'):
        flash('Please log in to access AI guidance.', 'error')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session.get('user')).first()
    return render_template('ai_guidance.html', user=user)


@app.route('/admin/promote', methods=['GET', 'POST'])
def admin_promote():
    if not session.get('user'):
        flash('Please log in to continue.', 'error')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session.get('user')).first()
    has_admin = User.query.filter_by(role='admin').count() > 0

    if has_admin and (not user or user.role != 'admin'):
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        target_username = request.form.get('username', '').strip()
        target = User.query.filter_by(username=target_username).first()
        if not target:
            flash('User not found.', 'error')
            return redirect(url_for('admin_promote'))
        target.role = 'admin'
        db.session.commit()
        flash(f'{target.username} is now an admin.', 'success')
        return redirect(url_for('admin_courses'))

    return render_template('admin_promote.html', user=user, has_admin=has_admin)


@app.route('/admin/courses')
def admin_courses():
    user, redirect_resp = require_admin()
    if redirect_resp:
        return redirect_resp
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('admin_courses.html', user=user, courses=courses)


@app.route('/admin/courses/new', methods=['GET', 'POST'])
def admin_course_new():
    user, redirect_resp = require_admin()
    if redirect_resp:
        return redirect_resp
    if request.method == 'POST':
        course = Course(
            title=request.form.get('title', '').strip(),
            category=request.form.get('category', '').strip(),
            instructor=request.form.get('instructor', '').strip(),
            description=request.form.get('description', '').strip(),
            level=request.form.get('level', 'Beginner'),
            duration=request.form.get('duration', '').strip(),
            lessons=int(request.form.get('lessons') or 0),
            students=int(request.form.get('students') or 0),
            rating=float(request.form.get('rating') or 0),
            reviews=int(request.form.get('reviews') or 0),
            thumbnail=request.form.get('thumbnail', 'ðŸ“š').strip() or 'ðŸ“š',
            status=request.form.get('status', 'bookmarked')
        )
        db.session.add(course)
        db.session.commit()
        flash('Course created.', 'success')
        return redirect(url_for('admin_courses'))
    return render_template('admin_course_form.html', user=user, course=None)


@app.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])
def admin_course_edit(course_id):
    user, redirect_resp = require_admin()
    if redirect_resp:
        return redirect_resp
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        course.title = request.form.get('title', '').strip()
        course.category = request.form.get('category', '').strip()
        course.instructor = request.form.get('instructor', '').strip()
        course.description = request.form.get('description', '').strip()
        course.level = request.form.get('level', 'Beginner')
        course.duration = request.form.get('duration', '').strip()
        course.lessons = int(request.form.get('lessons') or 0)
        course.students = int(request.form.get('students') or 0)
        course.rating = float(request.form.get('rating') or 0)
        course.reviews = int(request.form.get('reviews') or 0)
        course.thumbnail = request.form.get('thumbnail', 'ðŸ“š').strip() or 'ðŸ“š'
        course.status = request.form.get('status', 'bookmarked')
        db.session.commit()
        flash('Course updated.', 'success')
        return redirect(url_for('admin_courses'))
    return render_template('admin_course_form.html', user=user, course=course)


@app.route('/admin/courses/<int:course_id>/delete', methods=['POST'])
def admin_course_delete(course_id):
    user, redirect_resp = require_admin()
    if redirect_resp:
        return redirect_resp
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted.', 'success')
    return redirect(url_for('admin_courses'))


@app.route('/admin/courses/<int:course_id>/lessons')
def admin_lessons(course_id):
    user, redirect_resp = require_admin()
    if redirect_resp:
        return redirect_resp
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course.id).order_by(Lesson.order_index.asc()).all()
    return render_template('admin_lessons.html', user=user, course=course, lessons=lessons)


@app.route('/admin/courses/<int:course_id>/lessons/new', methods=['GET', 'POST'])
def admin_lesson_new(course_id):
    user, redirect_resp = require_admin()
    if redirect_resp:
        return redirect_resp
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        lesson = Lesson(
            course_id=course.id,
            title=request.form.get('title', '').strip(),
            video_url=request.form.get('video_url', '').strip(),
            summary=request.form.get('summary', '').strip(),
            order_index=int(request.form.get('order_index') or 1),
            duration_minutes=int(request.form.get('duration_minutes') or 0),
            level=request.form.get('level', 'Beginner'),
            is_free=True if request.form.get('is_free') == 'on' else False
        )
        db.session.add(lesson)
        db.session.commit()
        flash('Lesson created.', 'success')
        return redirect(url_for('admin_lessons', course_id=course.id))
    return render_template('admin_lesson_form.html', user=user, course=course, lesson=None)


@app.route('/admin/lessons/<int:lesson_id>/edit', methods=['GET', 'POST'])
def admin_lesson_edit(lesson_id):
    user, redirect_resp = require_admin()
    if redirect_resp:
        return redirect_resp
    lesson = Lesson.query.get_or_404(lesson_id)
    course = Course.query.get_or_404(lesson.course_id)
    if request.method == 'POST':
        lesson.title = request.form.get('title', '').strip()
        lesson.video_url = request.form.get('video_url', '').strip()
        lesson.summary = request.form.get('summary', '').strip()
        lesson.order_index = int(request.form.get('order_index') or 1)
        lesson.duration_minutes = int(request.form.get('duration_minutes') or 0)
        lesson.level = request.form.get('level', 'Beginner')
        lesson.is_free = True if request.form.get('is_free') == 'on' else False
        db.session.commit()
        flash('Lesson updated.', 'success')
        return redirect(url_for('admin_lessons', course_id=course.id))
    return render_template('admin_lesson_form.html', user=user, course=course, lesson=lesson)


@app.route('/admin/lessons/<int:lesson_id>/delete', methods=['POST'])
def admin_lesson_delete(lesson_id):
    user, redirect_resp = require_admin()
    if redirect_resp:
        return redirect_resp
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    db.session.delete(lesson)
    db.session.commit()
    flash('Lesson deleted.', 'success')
    return redirect(url_for('admin_lessons', course_id=course_id))


@app.route('/settings')
def settings():
    if not session.get('user'):
        flash('Please log in to access settings.', 'error')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session.get('user')).first()
    return render_template('settings.html', user=user)


@app.route('/update-email', methods=['POST'])
def update_email():
    if not session.get('user'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    new_email = data.get('newEmail', '').strip()
    password = data.get('password', '')
    
    if not new_email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    if not is_valid_email(new_email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    user = User.query.filter_by(username=session.get('user')).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Verify current password
    ok, _ = _verify_user_password(user, password)
    if not ok:
        return jsonify({'error': 'Incorrect password'}), 401
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user and existing_user.id != user.id:
        return jsonify({'error': 'Email already in use'}), 400
    
    # Update email
    user.email = new_email
    db.session.commit()
    session['email'] = new_email
    
    return jsonify({'message': 'Email updated successfully'}), 200


@app.route('/update-password', methods=['POST'])
def update_password():
    if not session.get('user'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    current_password = data.get('currentPassword', '')
    new_password = data.get('newPassword', '')
    
    if not current_password or not new_password:
        return jsonify({'error': 'All fields are required'}), 400
    
    user = User.query.filter_by(username=session.get('user')).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Verify current password
    ok, _ = _verify_user_password(user, current_password)
    if not ok:
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Validate new password strength
    is_strong, errors = is_strong_password(new_password)
    if not is_strong:
        return jsonify({'error': 'Password requirements: ' + ', '.join(errors)}), 400
    
    # Update password
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password updated successfully'}), 200


@app.route('/update-username', methods=['POST'])
def update_username():
    if not session.get('user'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    new_username = data.get('newUsername', '').strip()
    password = data.get('password', '')
    
    if not new_username or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    # Validate username format
    if len(new_username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    
    if not re.match(r'^[a-zA-Z0-9_]+$', new_username):
        return jsonify({'error': 'Username can only contain letters, numbers, and underscores'}), 400
    
    user = User.query.filter_by(username=session.get('user')).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Verify password
    ok, _ = _verify_user_password(user, password)
    if not ok:
        return jsonify({'error': 'Incorrect password'}), 401
    
    # Check if username already exists
    existing_user = User.query.filter_by(username=new_username).first()
    if existing_user and existing_user.id != user.id:
        return jsonify({'error': 'Username already taken'}), 400
    
    # Update username
    user.username = new_username
    db.session.commit()
    session['user'] = new_username
    session['username'] = new_username
    
    return jsonify({'message': 'Username updated successfully'}), 200


@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    if not session.get('user'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Mock AI response (in production, integrate with actual AI service)
    response = get_ai_response(message)
    
    return jsonify({'response': response, 'timestamp': datetime.datetime.utcnow().isoformat()})


def get_ai_response(message):
    """Generate AI response based on user message"""
    message_lower = message.lower()
    
    if 'recommend' in message_lower or 'course' in message_lower:
        return "Based on your progress, I recommend 'Advanced Python Programming' and 'Data Structures & Algorithms'. These will complement your current skills perfectly!"
    elif 'progress' in message_lower or 'doing' in message_lower:
        return "You're doing great! You've completed 72% of your challenges and are on a 15-day streak. Keep it up!"
    elif 'next' in message_lower or 'learn' in message_lower:
        return "I suggest focusing on System Design next. It's a crucial skill that builds on your current knowledge of Python and Data Structures."
    elif 'help' in message_lower or 'challenge' in message_lower:
        return "I'd be happy to help! Which specific challenge are you working on? I can provide hints, explain concepts, or walk you through the solution."
    elif 'hello' in message_lower or 'hi' in message_lower:
        return "Hello! How can I assist you with your learning journey today?"
    else:
        return "That's a great question! I'm here to help you with course recommendations, progress tracking, learning guidance, and answering questions about your courses. What would you like to know more about?"


@app.route('/learn/<int:course_id>')
def learn_course(course_id):
    """Display course lessons and learning interface"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    course = Course.query.get(course_id)
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('courses'))
    
    # Get all lessons for this course
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order_index).all()
    
    # Get user's enrollment for this course
    enrollment = Enrollment.query.filter_by(user_id=user.id, course_id=course_id).first()
    
    return render_template('learn.html', course=course, lessons=lessons, enrollment=enrollment, user=user)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
