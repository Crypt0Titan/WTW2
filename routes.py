from flask import Blueprint, render_template, redirect, url_for, flash
from views import main_routes, admin_routes
from models import Game, Question  # Import models as needed
from datetime import datetime  # Import datetime for time comparisons

# Define Blueprints
main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__, url_prefix='/admin')

# Register routes from views.py
main_routes(main)  # Register all routes under 'main'
admin_routes(admin)  # Register all routes under 'admin'

# Define play_game route to avoid conflicts
@main.route('/game/<int:game_id>/play')
def play_game_route(game_id):
    game = Game.query.get_or_404(game_id)
    if game.start_time and game.start_time <= datetime.utcnow() and not game.is_complete:
        # Fetch the game's questions
        questions = Question.query.filter_by(game_id=game.id).all()
        return render_template('game/play.html', game=game, questions=questions)
    else:
        flash('The game has not started yet or has already been completed.', 'warning')
        return redirect(url_for('main.index'))
