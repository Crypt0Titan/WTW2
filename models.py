from extensions import db
from datetime import datetime

# Game Model
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_limit = db.Column(db.Integer, nullable=False)
    max_players = db.Column(db.Integer, nullable=False)
    pot_size = db.Column(db.Float, nullable=False)
    entry_value = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    is_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with Player model
    players = db.relationship('Player', back_populates='game', lazy=True)


# Player Model
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    ethereum_address = db.Column(db.String(42), nullable=False)
    score = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Reverse relationship with Game model
    game = db.relationship('Game', back_populates='players')

    # Unique constraint to prevent the same player from joining the same game twice
    __table_args__ = (db.UniqueConstraint('game_id', 'ethereum_address', name='_game_ethereum_uc'),)


# Question Model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    phrase = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)


# Admin Model
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
