from app import db
from datetime import datetime

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_limit = db.Column(db.Integer, nullable=False)
    max_players = db.Column(db.Integer, nullable=False)
    pot_size = db.Column(db.Float, nullable=False)
    entry_value = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    is_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    phrase = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    ethereum_address = db.Column(db.String(42), nullable=False)
    score = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)