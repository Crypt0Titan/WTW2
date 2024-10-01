import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = Flask(__name__)

# Use the DATABASE_URL environment variable directly
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SECRET_KEY"] = os.urandom(24)

db = SQLAlchemy(app)
socketio = SocketIO(app)

with app.app_context():
    db.create_all()

# Import and register blueprints
from routes import main, admin
app.register_blueprint(main)
app.register_blueprint(admin)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
