from flask_wtf import Form
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired

class createGame(Form):
	game = SelectField(u'', choices=())
	num_players = SelectField(u'', choices=())
	"""
	num_players = SelectField(choices = [
	    ('00', 'Select'),
	    ('02', '02'),
	    ('03', '03'),
	    ('04', '04')])
	player2 = SelectField(coerce=int)
	player3 = SelectField(coerce=int)
	player4 = SelectField(coerce=int)
	"""


class playTurnForm(Form):
	draw = SubmitField(label='Draw Card')
	play = SelectField(coerce=int)