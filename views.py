import os
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import Admin, Game, Question, Player
from forms import CreateGameForm, JoinGameForm
from utils import check_answers, determine_winner
from app import app, db, socketio

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in as admin to access this page.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    games = Game.query.filter_by(is_complete=False).order_by(Game.start_time).all()
    return render_template('index.html', games=games)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    games = Game.query.order_by(Game.created_at.desc()).all()
    return render_template('admin/dashboard.html', games=games)

@app.route('/admin/create_game', methods=['GET', 'POST'])
@admin_required
def create_game():
    form = CreateGameForm()
    if request.method == 'POST':
        app.logger.info(f"Received POST request: {request.form}")
        if form.validate_on_submit():
            app.logger.info("Form validated successfully")
            try:
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
                socketio.emit('new_game', {'game_id': game.id, 'pot_size': game.pot_size, 'start_time': game.start_time.isoformat()}, namespace='/game')
                flash('Game created successfully', 'success')
                return redirect(url_for('admin_dashboard'))
            except Exception as e:
                app.logger.error(f"Error creating game: {str(e)}")
                db.session.rollback()
                flash('An error occurred while creating the game. Please try again.', 'error')
        else:
            app.logger.error(f"Form validation failed. Errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'error')
    return render_template('admin/create_game.html', form=form)

@app.route('/game/<int:game_id>/join', methods=['GET', 'POST'])
def join_game(game_id):
    game = Game.query.get_or_404(game_id)
    form = JoinGameForm()
    if form.validate_on_submit():
        player = Player(game_id=game.id, ethereum_address=form.ethereum_address.data)
        db.session.add(player)
        db.session.commit()
        socketio.emit('player_joined', {'game_id': game.id, 'player_count': len(game.players)}, namespace='/game')
        return redirect(url_for('game_lobby', game_id=game.id))
    return render_template('game/join.html', game=game, form=form)

@app.route('/game/<int:game_id>/lobby')
def game_lobby(game_id):
    game = Game.query.get_or_404(game_id)
    players = Player.query.filter_by(game_id=game.id).all()
    return render_template('game/lobby.html', game=game, players=players)

@app.route('/game/<int:game_id>/play')
def play_game(game_id):
    game = Game.query.get_or_404(game_id)
    questions = Question.query.filter_by(game_id=game.id).all()
    return render_template('game/play.html', game=game, questions=questions)

@app.route('/game/<int:game_id>/submit', methods=['POST'])
def submit_answers(game_id):
    game = Game.query.get_or_404(game_id)
    player = Player.query.filter_by(game_id=game.id, ethereum_address=request.form['ethereum_address']).first()
    
    if not player:
        return jsonify({'error': 'Player not found'}), 404

    answers = request.form.getlist('answers[]')
    questions = Question.query.filter_by(game_id=game.id).all()
    
    score = check_answers(questions, answers)
    player.score = score
    db.session.commit()

    socketio.emit('player_score_update', {'game_id': game.id, 'player_id': player.id, 'score': score}, namespace='/game')

    if score == len(questions):
        game.is_complete = True
        db.session.commit()
        socketio.emit('game_complete', {'game_id': game.id, 'winner_id': player.id}, namespace='/game')
        return jsonify({'message': 'Congratulations! You won the game!', 'score': score})
    
    return jsonify({'message': 'Answers submitted successfully', 'score': score})

@app.route('/game/<int:game_id>/result')
def game_result(game_id):
    game = Game.query.get_or_404(game_id)
    winner = determine_winner(game)
    players = Player.query.filter_by(game_id=game.id).order_by(Player.score.desc()).all()
    return render_template('game/result.html', game=game, winner=winner, players=players)

@app.route('/admin/start_game/<int:game_id>')
@admin_required
def start_game(game_id):
    game = Game.query.get_or_404(game_id)
    game.start_time = datetime.utcnow()
    db.session.commit()
    socketio.emit('game_started', {'game_id': game.id}, namespace='/game')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/game_stats/<int:game_id>')
@admin_required
def game_stats(game_id):
    game = Game.query.get_or_404(game_id)
    players = Player.query.filter_by(game_id=game.id).order_by(Player.score.desc()).all()
    return render_template('admin/game_stats.html', game=game, players=players)

@socketio.on('connect', namespace='/game')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/game')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join', namespace='/game')
def handle_join(data):
    game_id = data['game_id']
    join_room(f'game_{game_id}')
    emit('join_success', {'message': f'Joined game {game_id}'}, room=f'game_{game_id}')

@socketio.on('leave', namespace='/game')
def handle_leave(data):
    game_id = data['game_id']
    leave_room(f'game_{game_id}')
    emit('leave_success', {'message': f'Left game {game_id}'}, room=f'game_{game_id}')

@app.route('/api/games')
def api_games():
    games = Game.query.filter_by(is_complete=False).order_by(Game.start_time).all()
    return jsonify([{
        'id': game.id,
        'pot_size': game.pot_size,
        'entry_value': game.entry_value,
        'max_players': game.max_players,
        'players': [{'id': p.id, 'ethereum_address': p.ethereum_address} for p in game.players],
        'start_time': game.start_time.isoformat() if game.start_time else None,
    } for game in games])

@app.route('/api/games/<int:game_id>')
def api_game_details(game_id):
    game = Game.query.get_or_404(game_id)
    return jsonify({
        'id': game.id,
        'pot_size': game.pot_size,
        'entry_value': game.entry_value,
        'max_players': game.max_players,
        'players': [{'id': p.id, 'ethereum_address': p.ethereum_address} for p in game.players],
        'start_time': game.start_time.isoformat() if game.start_time else None,
        'time_limit': game.time_limit,
    })

@app.route('/api/games/<int:game_id>/questions')
def api_game_questions(game_id):
    questions = Question.query.filter_by(game_id=game_id).all()
    return jsonify([{
        'id': q.id,
        'phrase': q.phrase,
    } for q in questions])

@app.route('/api/games/<int:game_id>/submit', methods=['POST'])
def api_submit_answers(game_id):
    game = Game.query.get_or_404(game_id)
    data = request.json
    player = Player.query.filter_by(game_id=game.id, ethereum_address=data['ethereum_address']).first()
    
    if not player:
        return jsonify({'error': 'Player not found'}), 404

    answers = {int(a['question_id']): a['answer'] for a in data['answers']}
    questions = Question.query.filter_by(game_id=game.id).all()
    
    score = check_answers(questions, [answers.get(q.id, '') for q in questions])
    player.score = score
    db.session.commit()

    socketio.emit('player_score_update', {'game_id': game.id, 'player_id': player.id, 'score': score}, namespace='/game')

    if score == len(questions):
        game.is_complete = True
        db.session.commit()
        socketio.emit('game_complete', {'game_id': game.id, 'winner_id': player.id}, namespace='/game')
        return jsonify({'message': 'Congratulations! You won the game!', 'score': score, 'game_complete': True})
    
    return jsonify({'message': 'Answers submitted successfully', 'score': score, 'game_complete': False})