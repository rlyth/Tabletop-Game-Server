from flask_wtf import Form
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired

class createUser(Form):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	password2 = PasswordField('Password2')

class updatePassword(Form):
	PW = StringField('Password', validators=[DataRequired()])
	NewPW = StringField('NewPassword', validators=[DataRequired()])
	NewPW2 = StringField('NewPassword2')






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

