from flask_wtf import Form
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired

class userForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    password2 = StringField('Password2')

class gameForm(Form):
	game = StringField('Game')
	numberOfPlayers = SelectField(choices = [('00', 'Select'), ('02', '02'), ('03', '03'), ('04', '04')])
	player2 = SelectField(coerce=int)
	player3 = SelectField(coerce=int)
	player4 = SelectField(coerce=int)

class acceptForm(Form):
	status = SelectField(choices = [('00', 'Select'), ('Accept', 'Accept'), ('Decline', 'Decline')])

class playTurnForm(Form):
	draw = SubmitField(label='Draw Card')
	play = SelectField(coerce=int)

class updatePassword(Form):
	PW = StringField('Password', validators=[DataRequired()])
	NewPW = StringField('NewPassword', validators=[DataRequired()])
    newPW2 = StringField('NewPassword2')