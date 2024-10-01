from flask import render_template, redirect, url_for, flash, request, jsonify, session
from app import db, socketio
from models import Game, Player, Question, Admin
from utils import check_answers
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime
from sqlalchemy.orm import joinedload
from forms import JoinGameForm, CreateGameForm
import logging
from routes import main, admin

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('main.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def index():
    games = Game.query.filter_by(is_complete=False).options(joinedload(Game.players)).order_by(Game.start_time).all()
    return render_template('index.html', games=games, len=len, now=datetime.utcnow())

@main.route('/game/<int:game_id>/join', methods=['GET', 'POST'])
def join_game(game_id):
    game = Game.query.get_or_404(game_id)
    form = JoinGameForm()

    if form.validate_on_submit():
        ethereum_address = form.ethereum_address.data
        existing_player = Player.query.filter_by(game_id=game.id, ethereum_address=ethereum_address).first()
        
        if existing_player:
            flash('You have already joined this game.', 'info')
        elif len(game.players) >= game.max_players:
            flash('This game is already full.', 'error')
        else:
            new_player = Player(game_id=game.id, ethereum_address=ethereum_address)
            db.session.add(new_player)
            db.session.commit()
            flash('You have successfully joined the game!', 'success')
            socketio.emit('player_joined', {'game_id': game.id, 'player_count': len(game.players)}, namespace='/game')
        
        return redirect(url_for('main.game_lobby', game_id=game.id))

    return render_template('game/join.html', game=game, form=form)

@main.route('/game/<int:game_id>/lobby')
def game_lobby(game_id):
    game = Game.query.get_or_404(game_id)
    return render_template('game/lobby.html', game=game)

@main.route('/game/<int:game_id>/play')
def play_game(game_id):
    game = Game.query.get_or_404(game_id)
    questions = Question.query.filter_by(game_id=game.id).all()
    return render_template('game/play.html', game=game, questions=questions)

@admin.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin_user = Admin.query.filter_by(username=username).first()
        if admin_user and check_password_hash(admin_user.password_hash, password):
            session['admin_id'] = admin_user.id
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('admin/login.html')

@admin.route('/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@admin.route('/dashboard')
@admin_required
def dashboard():
    try:
        games = Game.query.options(joinedload(Game.players)).order_by(Game.created_at.desc()).all()
        for game in games:
            try:
                stats_url = url_for('admin.game_stats', game_id=game.id)
                logging.info(f"Generated URL for game {game.id}: {stats_url}")
            except Exception as e:
                logging.error(f"Error generating URL for game {game.id}: {str(e)}")
        return render_template('admin/dashboard.html', games=games, now=datetime.utcnow())
    except Exception as e:
        logging.error(f"Error in admin_dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard.', 'error')
        return redirect(url_for('main.index'))

@admin.route('/create_game', methods=['GET', 'POST'])
@admin_required
def create_game():
    form = CreateGameForm()
    if form.validate_on_submit():
        game = Game(
            time_limit=form.time_limit.data,
            max_players=form.max_players.data,
            pot_size=form.pot_size.data,
            entry_value=form.entry_value.data,
            start_time=form.start_time.data
        )
        db.session.add(game)
        db.session.commit()

        for i in range(12):
            phrase = getattr(form, f'phrase_{i}').data
            answer = getattr(form, f'answer_{i}').data
            if phrase and answer:
                question = Question(game_id=game.id, phrase=phrase, answer=answer)
                db.session.add(question)
        
        db.session.commit()
        flash('New game created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/create_game.html', form=form)

@main.route('/game/<int:game_id>/submit', methods=['POST'])
def submit_answers(game_id):
    logging.info(f"Received submission for game {game_id}")
    logging.info(f"Form data: {request.form}")
    
    game = Game.query.get_or_404(game_id)
    player = Player.query.filter_by(game_id=game.id, ethereum_address=request.form['ethereum_address']).first()
    
    if not player:
        logging.error(f"Player not found for game {game_id} and ethereum_address {request.form['ethereum_address']}")
        return jsonify({'error': 'Player not found'}), 404

    answers = request.form.getlist('answers[]')
    questions = Question.query.filter_by(game_id=game.id).all()
    
    logging.info(f"Number of questions: {len(questions)}, Number of answers: {len(answers)}")
    
    score = check_answers(questions, answers)
    player.score = score
    db.session.commit()

    logging.info(f"Player {player.id} submitted answers for game {game_id}. Score: {score}")

    socketio.emit('player_score_update', {'game_id': game.id, 'player_id': player.id, 'score': score}, namespace='/game')

    if score == len(questions):
        game.is_complete = True
        db.session.commit()
        socketio.emit('game_complete', {'game_id': game.id, 'winner_id': player.id}, namespace='/game')
        return jsonify({'message': 'Congratulations! You won the game!', 'score': score, 'game_complete': True})
    
    return jsonify({'message': 'Answers submitted successfully', 'score': score, 'game_complete': False})

@admin.route('/game_stats/<int:game_id>')
@admin_required
def game_stats(game_id):
    try:
        logging.info(f"Accessing game stats for game_id: {game_id}")
        game = Game.query.get_or_404(game_id)
        players = Player.query.filter_by(game_id=game_id).order_by(Player.score.desc()).all()
        return render_template('admin/game_stats.html', game=game, players=players)
    except Exception as e:
        logging.error(f"Error in game_stats for game_id {game_id}: {str(e)}")
        flash('An error occurred while loading the game stats.', 'error')
        return redirect(url_for('admin.dashboard'))
