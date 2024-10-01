from app import app, db, socketio
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from models import Game, Player, Question, Admin
from utils import check_answers
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime
from sqlalchemy.orm import joinedload
from forms import JoinGameForm, CreateGameForm

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    games = Game.query.filter_by(is_complete=False).options(joinedload(Game.players)).order_by(Game.start_time).all()
    return render_template('index.html', games=games, len=len, now=datetime.utcnow())

@app.route('/game/<int:game_id>/join', methods=['GET', 'POST'])
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
        
        return redirect(url_for('game_lobby', game_id=game.id))

    return render_template('game/join.html', game=game, form=form)

@app.route('/game/<int:game_id>/lobby')
def game_lobby(game_id):
    game = Game.query.get_or_404(game_id)
    return render_template('game/lobby.html', game=game)

@app.route('/game/<int:game_id>/play')
def play_game(game_id):
    game = Game.query.get_or_404(game_id)
    questions = Question.query.filter_by(game_id=game.id).all()
    return render_template('game/play.html', game=game, questions=questions)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    games = Game.query.options(joinedload(Game.players)).order_by(Game.created_at.desc()).all()
    return render_template('admin/dashboard.html', games=games, now=datetime.utcnow())

@app.route('/admin/create_game', methods=['GET', 'POST'])
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
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/create_game.html', form=form)

@app.route('/game/<int:game_id>/submit', methods=['POST'])
def submit_answers(game_id):
    app.logger.info(f"Received submission for game {game_id}")
    app.logger.info(f"Form data: {request.form}")
    
    game = Game.query.get_or_404(game_id)
    player = Player.query.filter_by(game_id=game.id, ethereum_address=request.form['ethereum_address']).first()
    
    if not player:
        app.logger.error(f"Player not found for game {game_id} and ethereum_address {request.form['ethereum_address']}")
        return jsonify({'error': 'Player not found'}), 404

    answers = request.form.getlist('answers[]')
    questions = Question.query.filter_by(game_id=game.id).all()
    
    app.logger.info(f"Number of questions: {len(questions)}, Number of answers: {len(answers)}")
    
    score = check_answers(questions, answers)
    player.score = score
    db.session.commit()

    app.logger.info(f"Player {player.id} submitted answers for game {game_id}. Score: {score}")

    socketio.emit('player_score_update', {'game_id': game.id, 'player_id': player.id, 'score': score}, namespace='/game')

    if score == len(questions):
        game.is_complete = True
        db.session.commit()
        socketio.emit('game_complete', {'game_id': game.id, 'winner_id': player.id}, namespace='/game')
        return jsonify({'message': 'Congratulations! You won the game!', 'score': score, 'game_complete': True})
    
    return jsonify({'message': 'Answers submitted successfully', 'score': score, 'game_complete': False})
