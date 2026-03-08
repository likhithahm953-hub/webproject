"""
Database Initialization Script
Initializes all database tables for SkillForge application
Run this script to create missing tables without losing existing data
"""

from app import app, db

def init_db():
    """Initialize database tables"""
    with app.app_context():
        print("🔧 Initializing database tables...")
        try:
            # Create all tables defined in models
            db.create_all()
            print("✅ Database tables created successfully!")
            print("\nTables created:")
            print("  - user")
            print("  - domain")
            print("  - domain_enrollment")
            print("  - course_link")
            print("  - domain_course_progress (NEW)")
            print("  - domain_course_quiz")
            print("  - domain_course_quiz_attempt")
            print("  - domain_certificate")
            print("  - and more...")
            print("\n✨ Database is ready!")
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            raise

if __name__ == '__main__':
    init_db()
