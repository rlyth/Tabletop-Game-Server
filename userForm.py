from flask_wtf import Form
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import DataRequired

class userForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    password2 = StringField('Password2')

class gameForm(Form):
	game = StringField('Game')
	numberOfPlayers = SelectField(choices = [('00', 'Select'), ('02', '02'), ('03', '03'), ('04', '04')])
	player2 = SelectField(choices=[('00', 'Select')], coerce=int)
	player3 = SelectField(choices=[('00', 'Select')], coerce=int)
	player4 = SelectField(choices=[('00', 'Select')], coerce=int)