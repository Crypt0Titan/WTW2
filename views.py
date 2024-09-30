from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Admin, Game, Question, Player
from forms import CreateGameForm, JoinGameForm
from utils import check_answers, determine_winner
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime, timedelta

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
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
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password')
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
        flash('Game created successfully')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_game.html', form=form)

@app.route('/game/<int:game_id>/join', methods=['GET', 'POST'])
def join_game(game_id):
    game = Game.query.get_or_404(game_id)
    form = JoinGameForm()
    if form.validate_on_submit():
        player = Player(game_id=game.id, ethereum_address=form.ethereum_address.data)
        db.session.add(player)
        db.session.commit()
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

    if score == len(questions):
        game.is_complete = True
        db.session.commit()
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
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/game_stats/<int:game_id>')
@admin_required
def game_stats(game_id):
    game = Game.query.get_or_404(game_id)
    players = Player.query.filter_by(game_id=game.id).order_by(Player.score.desc()).all()
    return render_template('admin/game_stats.html', game=game, players=players)
