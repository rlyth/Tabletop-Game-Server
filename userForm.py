from flask_wtf import Form
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

class userForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    password2 = StringField('Password2')

class gameForm(Form):
	game = StringField('Game')
	players = StringField('Players')
	player2 = IntegerField('P2')
	player3 = IntegerField('P3')
	player4 = IntegerField('P4')