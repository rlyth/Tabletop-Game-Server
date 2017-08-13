from flask import Flask, render_template, session, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from userForm import userForm, gameForm, acceptForm
from socket import gethostname

app = Flask(__name__)

app.config.from_object('config')

CSRFProtect(app)

db = SQLAlchemy(app)

###Creates Local database for testing##################
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/testuser.db'
#db = SQLAlchemy(app)

#class User(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    username = db.Column(db.String(80), unique=True)
#    password = db.Column(db.String(120))

#    def __init__(self, username, password):
#        self.username = username
#        self.password = password

#    def __repr__(self):
#        return '<User %r>' % self.username


#db.create_all()

#dmin = User('admin', 'test')
#db.session.add(admin)
#db.session.commit()

#users = User.query.all()
#print(users[0].password)       

#def addUserToDB(userName, password):
#	user = User(userName, password)
#	db.session.add(user)
#	db.session.commit()
###REMOVE THIS PURELY FOR TESTING##################

#db.init_app(app)

# Register blueprints
from gameDB import gameDB
app.register_blueprint(gameDB)

from gameDB import GameFunctions
from gameDB import PlayersInGame, Game, GameInstance, Card, CardInstance, CardsInGame, Pile, GameLog

from userDB import userDB
app.register_blueprint(userDB)

from userDB import User

from uno import uno
app.register_blueprint(uno)

passedUserName = None

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/newgame", methods = ['GET', 'POST'])
def newGame():
	passedUserName = session['username']
	users = User.query.filter(User.username != passedUserName).all()
	existingUser = User.query.filter_by(username=passedUserName).first()
	newGameForm = gameForm()

	newGameForm.player2.choices = [(u.id, u.username) for u in User.query.filter(User.username != passedUserName)]
	newGameForm.player3.choices = [(u.id, u.username) for u in User.query.filter(User.username != passedUserName)]
	newGameForm.player4.choices = [(u.id, u.username) for u in User.query.filter(User.username != passedUserName)]

	newGameForm.player2.choices.insert(0, ('0', 'Select'))
	newGameForm.player3.choices.insert(0, ('0', 'Select'))
	newGameForm.player4.choices.insert(0, ('0', 'Select'))

	if request.method == 'POST':
		gameName = newGameForm.game.data
		#THIS IS WHERE WE KEEP TRACK OF WHICH GAME IS STARTING MODIFY FOR FUTURE GAMES
		baseGameID = 2
		if gameName == 'uno':
			baseGameID = 2
		gamePlayers = newGameForm.numberOfPlayers.data
		playerNum2 = newGameForm.player2.data
		playerNum3 = newGameForm.player3.data
		playerNum4 = newGameForm.player4.data
		if gamePlayers == '03':
			if playerNum2 == 0 or playerNum3 == 0:
				return render_template('newgame.html')
			else:
				inviteList = [playerNum2, playerNum3]
				GameFunctions.initGameInstance(baseGameID, existingUser.id, inviteList)
				return redirect(url_for('login'))

		if gamePlayers == '04':
			if playerNum2 == 0 or playerNum3 == 0 or playerNum4 == 0:				
				return render_template('newgame.html')
			else:
				inviteList = [playerNum2, playerNum3, playerNum4]
				GameFunctions.initGameInstance(baseGameID, existingUser.id, inviteList)
				return redirect(url_for('login'))
		else:
			if playerNum2 == 0:				
				return render_template('newgame.html')
			else:
				inviteList = [playerNum2]
				GameFunctions.initGameInstance(baseGameID, existingUser.id, inviteList)
				return redirect(url_for('login'))

	return render_template('newgame.html', passedUserName=passedUserName, users=users, newGameForm=newGameForm)

@app.route("/newuser", methods = ['GET', 'POST'])
def newUser():
	logInForm = userForm()
	if request.method == 'POST':
		if logInForm.validate() == False:
			return render_template('newuser.html', form = logInForm)
		else:
			#will want to replace with calls to user object
			existingUser = User.query.filter_by(username=logInForm.username.data).first()
			if(existingUser):
				flash('Sorry, username already exists.')
				return render_template('newuser.html', form = logInForm)
			else:
				#check entered passwords and if they match add user to the database
				if(logInForm.password.data != logInForm.password2.data):
					flash('The passwords do not match.')
					return render_template('newuser.html', form = logInForm)
				else:
					#addUserToDB(logInForm.username.data, logInForm.password.data)
					newUser = User(logInForm.username.data, logInForm.password.data)
					db.session.add(newUser)
					db.session.commit()

					session['username'] = logInForm.username.data
					return redirect(url_for('login'))
	else:
		return render_template('newuser.html', form = logInForm)

@app.route("/profile")
def profile():
	passedUserName = session['username']
	return render_template('profile.html', passedUserName=passedUserName)

@app.route("/signedin", methods = ['GET', 'POST'])
def signIn():
	logInForm = userForm()
	if request.method == 'POST':
		if logInForm.validate() == False:
			flash('There was a problem with data that was entered.')
			return render_template('signedin.html', form = logInForm)
		else:
			existingUser = User.query.filter_by(username=logInForm.username.data).first()

			if(not existingUser.check_password(logInForm.password.data)):

				flash('There was a problem with the password you entered.')
				return render_template('signedin.html', form = logInForm)

			if(existingUser):
				session['username'] = existingUser.username
				return redirect(url_for('login'))
			else:
				flash('Username does not exist.')

				return render_template('signedin.html', form = logInForm)
	else:
		return render_template('signedin.html', form = logInForm)

@app.route("/statistics")
def statistics():
	if('username' in session):
		passedUserName = session['username']
		existingUser = User.query.filter_by(username=passedUserName).first()
		userGames = existingUser.games_played
		userWins = existingUser.wins
		if (userGames > 0):
			userRecord = 100 * (userWins/userGames)
		else:
			userRecord = 0		
	return render_template('statistics.html', existingUser=existingUser, userRecord=userRecord)

@app.route("/login")
def login():
	if('username' in session):
		passedUserName = session['username']
		existingUser = User.query.filter_by(username=passedUserName).first()
		gameids = PlayersInGame.query.filter(PlayersInGame.user_id == existingUser.id).all()
		playableGame = []
		for game in gameids:
			thisGame = GameFunctions.gamePlay(game.game_instance)
			if(thisGame.isPendingInvites() == False):
				playableGame.append(game)
		if(existingUser.role == 'Admin'):
			return render_template('adminLogin.html', passedUserName=passedUserName, gameids=gameids, playableGame=playableGame)
		else:
			return render_template('login.html', passedUserName=passedUserName, gameids=gameids, playableGame=playableGame)
	else:
		return render_template('index.html')

@app.route("/delete", methods = ['DELETE'])
def adminDelete():
	passedUserName = session['username']
	users = User.query.all()
	return render_template('delete.html', passedUserName=passedUserName, users=users)

@app.route("/logout")
def logout():
	session['username'] = None
	return render_template('index.html')

@app.route("/acceptgame/<game_id>", methods = ['GET', 'POST'])
def acceptgame(game_id):
	acceptGameForm = acceptForm()
	passedUserName = session['username']
	existingUser = User.query.filter_by(username=passedUserName).first()

	if request.method == 'POST':
		inviteStatus = acceptGameForm.status.data
		thisGame = GameFunctions.gamePlay(game_id)

		if inviteStatus == 'Accept':
			#thisGame = PlayersInGame.query.filter(game_id).first()
			thisGame.acceptInvite(existingUser.id)
			return redirect(url_for('login'))
		elif inviteStatus == 'Decline':
			thisGame.declineInvite(existingUser.id)
			return redirect(url_for('login'))
		else:
			return redirect(url_for('login'))
	else:
		return render_template('acceptgame.html', passedUserName=passedUserName, acceptGameForm=acceptGameForm, game_id=game_id)

@app.route("/playturn/<game_id>", methods = ['GET', 'POST'])
def playturn(game_id):
	passedUserName = session['username']
	thisGame = GameFunctions.gamePlay(game_id)
	games = Game.query.all()
	ginstance = GameInstance.query.all()
	pgame = PlayersInGame.query.order_by(models.PlayersInGame.game_instance, models.PlayersInGame.turn_order).all()
	cards = Card.query.all(),
	icard = CardInstance.query.order_by(models.CardInstance.in_pile, models.CardInstance.pile_order).all()
	gcard = CardsInGame.query.all()
	piles = Pile.query.all()
	log = GameLog.query \
		.order_by(
			models.GameLog.game_instance,
			models.GameLog.timestamp.desc()
		) \
		.all()
	dump=dumps
	return render_template('playturn.html', passedUserName=passedUserName, games=games, ginstance=ginstance, pgame=pgame, cards=cards, icard=icard, gcard=gcard, piles=piles, log=log, dumps=dumps)

if __name__ == "__main__":
	#db.create_all()
	if 'liveconsole' not in gethostname():
		app.run(debug = True)
    #app.run()
