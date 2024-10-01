from flask import render_template, redirect, url_for, flash, request, jsonify, session
from models import Game, Player, Question, Admin
from forms import CreateGameForm, JoinGameForm
from app import db, socketio
from utils import check_answers
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime
from sqlalchemy.orm import joinedload
import logging
from routes import main, admin

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def index():
    try:
        logging.info('Entering index route')
        
        # Fetch games with eager loading for players
        games = Game.query.filter_by(is_complete=False).options(joinedload(Game.players)).order_by(Game.start_time).all()
        logging.info(f'Number of games fetched: {len(games)}')
        
        games_data = []
        
        for game in games:
            # Use defaults or handle potential None or empty values
            pot_size = float(game.pot_size) if game.pot_size else 0.0
            entry_value = float(game.entry_value) if game.entry_value else 0.0
            max_players = int(game.max_players) if game.max_players else 0
            
            # Handle start_time more robustly
            start_time = game.start_time
            if isinstance(start_time, str):
                try:
                    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    start_time = datetime.utcnow()  # Fallback to current time if parsing fails
            elif not isinstance(start_time, datetime):
                start_time = datetime.utcnow()  # Fallback to current time for any other case
            
            game_data = {
                'id': game.id,
                'pot_size': pot_size,
                'entry_value': entry_value,
                'max_players': max_players,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'players_count': len(game.players) if game.players else 0
            }
            
            games_data.append(game_data)
            logging.info(f'Game data: {game_data}')
        
        # Pass processed games data to the template
        return render_template('index.html', games=games_data, now=datetime.utcnow())
    
    except Exception as e:
        logging.error(f'Error in index route: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin.route('/dashboard')
@admin_required
def dashboard():
    games = Game.query.order_by(Game.created_at.desc()).all()
    return render_template('admin/dashboard.html', games=games, now=datetime.utcnow())
