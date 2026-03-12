from app import create_app
from app.extensions import db
from app.models.user import User

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()

        # Create default admin user
        admin_email = "admin@example.com"
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            print("Creating default admin user...")
            admin = User(
                username="admin",
                email=admin_email,
                role="admin"
            )
            admin.set_password("admin123")  # Default password, you should change this in production
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully. Use email 'admin@example.com' and password 'admin123' to login.")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    init_db()
