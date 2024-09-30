from models import Player

def check_answers(questions, submitted_answers):
    score = 0
    for question, answer in zip(questions, submitted_answers):
        if question.answer.lower() == answer.lower():
            score += 1
    return score

def determine_winner(game):
    players = Player.query.filter_by(game_id=game.id).order_by(Player.score.desc()).all()
    if players:
        return players[0]
    return None
