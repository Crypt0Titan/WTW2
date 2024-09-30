from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class CreateGameForm(FlaskForm):
    time_limit = IntegerField('Time Limit (seconds)', validators=[DataRequired(), NumberRange(min=1)])
    max_players = IntegerField('Max Players', validators=[DataRequired(), NumberRange(min=1)])
    pot_size = FloatField('Pot Size', validators=[DataRequired(), NumberRange(min=0)])
    entry_value = FloatField('Entry Value', validators=[DataRequired(), NumberRange(min=0)])
    start_time = DateTimeField('Start Time', validators=[DataRequired()])
    
    for i in range(12):
        vars()[f'phrase_{i}'] = StringField(f'Phrase {i+1}', validators=[Length(max=255)])
        vars()[f'answer_{i}'] = StringField(f'Answer {i+1}', validators=[Length(max=255)])
    
    submit = SubmitField('Create Game')

class JoinGameForm(FlaskForm):
    ethereum_address = StringField('Ethereum Address', validators=[DataRequired(), Length(min=42, max=42)])
    submit = SubmitField('Join Game')
