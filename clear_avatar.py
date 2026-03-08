from app import app, db, User

with app.app_context():
    user = User.query.first()
    if user:
        print(f"User: {user.username}")
        print(f"Current avatar: {user.avatar}")
        user.avatar = None
        db.session.commit()
        print("Avatar cleared from database!")
    else:
        print("No user found")
