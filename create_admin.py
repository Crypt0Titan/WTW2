from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)

def create_admin_user():
    with app.app_context():
        try:
            # Check if admin user already exists
            admin = Admin.query.filter_by(username='admin').first()
            if not admin:
                # Create a new admin user
                new_admin = Admin(username='admin', password_hash=generate_password_hash('adminpassword'))
                db.session.add(new_admin)
                db.session.commit()
                logging.info("Admin user created successfully.")
            else:
                logging.info("Admin user already exists.")
        except Exception as e:
            logging.error(f"Error creating admin user: {str(e)}")

if __name__ == "__main__":
    create_admin_user()
