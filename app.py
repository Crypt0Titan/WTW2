import os
from flask import Flask
from extensions import db, socketio  # Import db and socketio from extensions.py

app = Flask(__name__)

# Use the DATABASE_URL environment variable directly
database_url = os.environ.get("DATABASE_URL")
if database_url is None:
    raise ValueError("DATABASE_URL environment variable is not set")

# Configurations
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SECRET_KEY"] = os.urandom(24)

# Initialize extensions (database and socketio)
db.init_app(app)
socketio.init_app(app)

# Create database tables on app start-up
with app.app_context():
    db.create_all()  # Creates tables for all models

# Import and register blueprints for routes
from routes import main, admin
app.register_blueprint(main)  # Main blueprint without a URL prefix
app.register_blueprint(admin, url_prefix='/admin')  # Admin blueprint with /admin URL prefix

# Run the app with socketio support
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
