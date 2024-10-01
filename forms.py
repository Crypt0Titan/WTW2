from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, DateTimeField
from wtforms.validators import DataRequired, NumberRange, Length, ValidationError
from datetime import datetime
import pytz  # Required for timezone conversions

class CreateGameForm(FlaskForm):
    time_limit = IntegerField('Time Limit (seconds)', validators=[
        DataRequired(message="Time limit is required."),
        NumberRange(min=60, max=3600, message="Time limit must be between 60 and 3600 seconds.")
    ])
    max_players = IntegerField('Max Players', validators=[
        DataRequired(message="Maximum number of players is required."),
        NumberRange(min=2, max=100, message="Number of players must be between 2 and 100.")
    ])
    pot_size = FloatField('Pot Size', validators=[
        DataRequired(message="Pot size is required."),
        NumberRange(min=1, message="Pot size must be at least 1.")
    ])
    entry_value = FloatField('Entry Value', validators=[
        DataRequired(message="Entry value is required."),
        NumberRange(min=0, message="Entry value must be at least 0.")
    ])
    start_time = DateTimeField('Start Time', validators=[DataRequired(message="Start time is required.")])

    def validate_start_time(form, field):
        # Convert UAE time to UTC (UAE is UTC+4)
        uae_timezone = pytz.timezone('Asia/Dubai')
        current_time_utc = datetime.now(pytz.utc)

        # Localize the start_time to UAE timezone
        start_time_uae = uae_timezone.localize(field.data)

        # Convert the start time to UTC
        start_time_utc = start_time_uae.astimezone(pytz.utc)

        if start_time_utc <= current_time_utc:
            raise ValidationError("Start time must be in the future.")

    for i in range(12):
        vars()[f'phrase_{i}'] = StringField(f'Phrase {i+1}', validators=[Length(max=255)])
        vars()[f'answer_{i}'] = StringField(f'Answer {i+1}', validators=[Length(max=255)])

    def validate(self, extra_validators=None):
        # Call the parent class validate method with extra_validators
        if not super().validate(extra_validators=extra_validators):
            return False

        phrase_answer_pairs = [(getattr(self, f'phrase_{i}').data, getattr(self, f'answer_{i}').data) for i in range(12)]
        valid_pairs = [pair for pair in phrase_answer_pairs if pair[0] and pair[1]]

        if len(valid_pairs) < 1:
            self.errors['phrases'] = ["At least one phrase-answer pair is required."]
            return False

        return True


class JoinGameForm(FlaskForm):
    ethereum_address = StringField('Ethereum Address', validators=[
        DataRequired(message="Ethereum address is required."),
        Length(min=42, max=42, message="Ethereum address must be exactly 42 characters long.")
    ])
