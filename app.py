from flask import Flask, render_template, session, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from userForm import userForm, gameForm, acceptForm, playTurnForm
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

from uno.uno import Uno

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

@app.route("/winner", methods = ['GET', 'POST'])
def winner():
	passedUserName = session['username']
	return render_template('winner.html', passedUserName=passedUserName)

@app.route("/playturn/<game_id>", methods = ['GET', 'POST'])
def playturn(game_id):
	dump = ''
	passedUserName = session['username']
	existingUser = User.query.filter_by(username=passedUserName).first()
	playersThisGame = PlayersInGame.query.filter_by(game_instance=game_id).order_by(PlayersInGame.turn_order).all()
	users = User.query.all()
	usersPlaying = []
	for p in playersThisGame:
		for u in users:
			if p.user_id == u.id:
				usersPlaying.append(u)
    # GameInstance/Game object
	gameInfo = GameFunctions.getGameInstance(game_id)
	thisGame = GameFunctions.gamePlay(game_id)
	turnForm = playTurnForm()
    # Invalid Game ID
	if not gameInfo:
		dump = "Game Instance not found."
		return redirect(url_for('login'))

    # GameInstance is Uno 
	if gameInfo.Game.name == 'Uno':
		game = Uno(game_id)
		active_player = game.getCurrentPlayerID()
		if request.method == 'POST':
			if turnForm.draw.data:
				game.draw(active_player)
				active_player = game.getCurrentPlayerID()
			elif 'playCard' in request.form:
				wc = None
				active_player = game.getCurrentPlayerID()
				# Wild card was played, get color
				if 'wildColor' in request.form:
					if 'wildColor' == 'Select':
						flash('You must choose a color to play a wild card.')
					else:
						wc = request.form["wildColor"]
						active_player = game.getCurrentPlayerID()
				# playCard returned false; move is illegal
				if not game.playCard(active_player, request.form["cid"], wildColor=wc):
					flash('Can\'t play that card')

		g = game.getThisGame(active_player)

		discard = g["Discard Top"]

		players = g["Players"]

		hand = g["Player Hand"]
		turnForm.play.choices = [(c.id, c.Card.name, c.Card.img_front) for c in hand]

		deck_count = g["Deck Count"]
		discard_count = g["Discard Count"]

		logs = game.getLogs()

	else:
		dump = "That is not a game we have right now."
		return redirect(url_for('login'))

	return render_template('playturn.html', existingUser=existingUser, players=players, usersPlaying=usersPlaying, dump=dump, logs=logs, discard=discard, deck=True, deck_count=deck_count, discard_count=discard_count, hand=hand, active=active_player, endgame=True)

if __name__ == "__main__":
	#db.create_all()
	if 'liveconsole' not in gethostname():
		app.run(debug = True)
    #app.run()
