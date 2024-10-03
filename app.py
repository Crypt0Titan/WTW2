import os
from flask import Flask
from extensions import db, socketio  # Import db and socketio from extensions.py

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SECRET_KEY"] = os.urandom(24)

db.init_app(app)
socketio.init_app(app)

with app.app_context():
    db.create_all()

from routes import main, admin
app.register_blueprint(main)
app.register_blueprint(admin, url_prefix='/admin')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
