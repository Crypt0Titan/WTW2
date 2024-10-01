from flask import render_template, redirect, url_for, flash, request, jsonify, session
from models import Game, Player, Question, Admin
from forms import CreateGameForm, JoinGameForm
from extensions import db, socketio
from werkzeug.security import check_password_hash
from datetime import datetime
from sqlalchemy.orm import joinedload
import pytz

def update_game_statuses():
    current_time = datetime.utcnow()
    games = Game.query.filter_by(is_complete=False).all()

    for game in games:
        if game.start_time:
            elapsed_time = current_time - game.start_time

            if elapsed_time.total_seconds() >= game.time_limit:
                game.is_complete = True
                db.session.commit()

def main_routes(main):
    @main.route('/')
    def index():
        update_game_statuses()
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
                return redirect(url_for('main.game_lobby', game_id=game.id))

        return render_template('game/join.html', game=game, form=form)

    @main.route('/game/<int:game_id>/lobby')
    def game_lobby(game_id):
        game = Game.query.get_or_404(game_id)
        players = Player.query.filter_by(game_id=game_id).all()
        return render_template('game/lobby.html', game=game, players=players)

    @main.route('/game/<int:game_id>/play', endpoint='play_game')
    def play_game(game_id):
        game = Game.query.get_or_404(game_id)
        update_game_statuses()
        if game.start_time and game.start_time <= datetime.utcnow() and not game.is_complete:
            questions = Question.query.filter_by(game_id=game.id).all()
            player_address = request.args.get('address', '')
            return render_template('game/play.html', game=game, questions=questions, player_address=player_address)
        else:
            flash('The game has not started yet or has already been completed.', 'warning')
            return redirect(url_for('main.game_lobby', game_id=game_id))

    @main.route('/game/<int:game_id>/result')
    def game_result(game_id):
        game = Game.query.get_or_404(game_id)
        players = Player.query.filter_by(game_id=game_id).order_by(Player.score.desc()).all()
        return render_template('game/result.html', game=game, players=players)

    @main.route('/game/<int:game_id>/submit', methods=['POST'])
    def submit_answers(game_id):
        game = Game.query.get_or_404(game_id)
        answers = request.form.getlist('answers[]')
        ethereum_address = request.form.get('ethereum_address')

        score = 0
        questions = Question.query.filter_by(game_id=game.id).all()

        for question, answer in zip(questions, answers):
            if answer.strip().lower() == question.answer.strip().lower():
                score += 1

        player = Player.query.filter_by(ethereum_address=ethereum_address, game_id=game.id).first()
        if player:
            player.score = score
        else:
            player = Player(ethereum_address=ethereum_address, game_id=game.id, score=score)
            db.session.add(player)

        db.session.commit()

        socketio.emit('player_score_update', {
            'game_id': game.id,
            'player_address': ethereum_address,
            'score': score
        }, namespace='/game')

        if game.start_time:
            elapsed_time = datetime.utcnow() - game.start_time
            if elapsed_time.total_seconds() >= game.time_limit:
                game.is_complete = True
                db.session.commit()

        return jsonify({
            'message': 'Answers submitted successfully!',
            'score': score,
            'game_complete': game.is_complete
        })

def admin_routes(admin):
    @admin.route('/dashboard')
    def dashboard():
        update_game_statuses()
        games = Game.query.order_by(Game.created_at.desc()).all()
        current_time = datetime.utcnow()
        return render_template('admin/dashboard.html', games=games, now=current_time)

    @admin.route('/start_game/<int:game_id>', methods=['POST'])
    def start_game(game_id):
        game = Game.query.get_or_404(game_id)
        if game.start_time and game.start_time <= datetime.utcnow():
            flash('Game has already started or is in progress!', 'error')
        else:
            game.start_time = datetime.utcnow()
            db.session.commit()
            flash(f'Game {game_id} has started!', 'success')

            socketio.emit('game_started', {'game_id': game.id}, namespace='/game')

        return redirect(url_for('admin.dashboard'))

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

    @admin.route('/create_game', methods=['GET', 'POST'])
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

    @admin.route('/game_stats/<int:game_id>')
    def game_stats(game_id):
        game = Game.query.get_or_404(game_id)
        players = Player.query.filter_by(game_id=game_id).order_by(Player.score.desc()).all()
        current_time = datetime.utcnow()
        return render_template('admin/game_stats.html', game=game, players=players, now=current_time)