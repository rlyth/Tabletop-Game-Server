from flask import Flask, render_template, session, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from userForm import userForm, gameForm, acceptForm, playTurnForm, updatePassword
from socket import gethostname
import random

app = Flask(__name__)

app.config.from_object('config')

CSRFProtect(app)

db = SQLAlchemy(app)

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
	if('username' in session):
		passedUserName = session['username']
	else:
		passedUserName = None
	return render_template('index.html', passedUserName=passedUserName)

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
			if playerNum2 == 0 or playerNum3 == 0 or playerNum2 == playerNum3:
				return render_template('error.html')
			else:
				inviteList = [playerNum2, playerNum3]
				GameFunctions.initGameInstance(baseGameID, existingUser.id, inviteList)
				return redirect(url_for('login'))

		if gamePlayers == '04':
			if playerNum2 == 0 or playerNum3 == 0 or playerNum4 == 0 or playerNum2 == playerNum3 or playerNum2 == playerNum4 or playerNum4 == playerNum3:
				return render_template('error.html')
			else:
				inviteList = [playerNum2, playerNum3, playerNum4]
				GameFunctions.initGameInstance(baseGameID, existingUser.id, inviteList)
				return redirect(url_for('login'))
		else:
			if playerNum2 == 0:
				return render_template('error.html')
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

@app.route("/profile", methods = ['GET', 'POST'])
def profile():
	passedUserName = session['username']
	updatePW = updatePassword()
	if request.method == 'POST':
		if updatePW.validate() == False:
			return render_template('profile.html', updatePW=updatePW)
		else:
			existingUser = User.query.filter_by(username=passedUserName).one()

			if(not existingUser.check_password(updatePW.PW.data)):

				flash('There was a problem with the password you entered.')
				return render_template('profile.html', updatePW=updatePW)
			else:
				#check entered passwords match
				if(updatePW.NewPW.data != updatePW.NewPW2.data):
					flash('The passwords do not match.')
					return render_template('profile.html', updatePW=updatePW)
				else:
					existingUser.set_password(updatePW.NewPW.data)
					db.session.commit()
					flash('Password sucessfully updated.')
					return render_template('profile.html', updatePW=updatePW)

	return render_template('profile.html', passedUserName=passedUserName, updatePW=updatePW)

@app.route("/signin", methods = ['GET', 'POST'])
def signIn():
	logInForm = userForm()
	if request.method == 'POST':
		if logInForm.validate() == False:
			flash('There was a problem with data that was entered.')
			return render_template('signin.html', form = logInForm)
		else:
			existingUser = User.query.filter_by(username=logInForm.username.data).first()

			if(not existingUser.check_password(logInForm.password.data)):

				flash('There was a problem with the password you entered.')
				return render_template('signin.html', form = logInForm)

			if(existingUser):
				session['username'] = existingUser.username
				return redirect(url_for('login'))
			else:
				flash('Username does not exist.')

				return render_template('signin.html', form = logInForm)
	else:
		return render_template('signin.html', form = logInForm)

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

@app.route("/rules")
def rules():
	if('username' in session):
		passedUserName = session['username']
	else:
		passedUserName = None
	return render_template('rules.html', passedUserName=passedUserName)

@app.route("/login")
def login():
	if('username' in session):
		passedUserName = session['username']
		existingUser = User.query.filter_by(username=passedUserName).first()
		gameids = PlayersInGame.query.filter(PlayersInGame.user_id == existingUser.id).all()
		users = User.query.all()
		players = PlayersInGame.query.all()
		playableGame = []
		gname = ''
		for game in gameids:
			thisGame = GameFunctions.gamePlay(game.game_instance)
			gameInfo = GameFunctions.getGameInstance(game.game_instance)
			gname = gameInfo.Game.name
			if(thisGame.isPendingInvites() == False and gameInfo.status != 'Ended'):
				playableGame.append(game)
		if(existingUser.role == 'Admin'):
			return render_template('adminLogin.html', passedUserName=passedUserName, gname=gname, gameids=gameids, playableGame=playableGame, users=users, players=players)
		else:
			return render_template('login.html', passedUserName=passedUserName, gname=gname, gameids=gameids, playableGame=playableGame, users=users, players=players)
	else:
		return render_template('index.html')

@app.route("/delete", methods = ['DELETE'])
def adminDelete():
	passedUserName = session['username']
	users = User.query.all()
	games = GameFunctions.getGameInstance(game_id)

	return render_template('delete.html', passedUserName=passedUserName, users=users)

@app.route("/logout")
def logout():
	session['username'] = None
	return redirect(url_for('main'))

@app.route("/acceptgame/<game_id>", methods = ['GET', 'POST'])
def acceptgame(game_id):
	acceptGameForm = acceptForm()
	passedUserName = session['username']
	existingUser = User.query.filter_by(username=passedUserName).first()
	game = GameInstance.query.filter_by(id=game_id).first()
	gname = Game.query.filter_by(id=game.base_game).first()

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
		return render_template('acceptgame.html', passedUserName=passedUserName, gname=gname, acceptGameForm=acceptGameForm, game_id=game_id)

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
			if 'drawCard' in request.form:
				game.draw(active_player)
				active_player = game.getCurrentPlayerID()
			elif 'playCard' in request.form:
				wc = None
				# Wild card was played, get color
				if 'wildColor' in request.form:
					wc = request.form["wildColor"]
					if wc == 'Select':
						#Mif the player doesn't pick the computer picks.
						colors = ['Red', 'Yellow', 'Green', 'Blue']
						wc = random.choice(colors)

				# playCard returned false; move is illegal
				if game.playCard(active_player, request.form["cid"], wildColor=wc):
					active_player = game.getCurrentPlayerID()
				else:
					flash('Can\'t play that card')

		g = game.getThisGame(existingUser.id)

		discard = g["Discard Top"]

		players = g["Players"]

		hand = g["Player Hand"]
		turnForm.play.choices = [(c.id, c.Card.name, c.Card.img_front) for c in hand]

		deck_count = g["Deck Count"]
		discard_count = g["Discard Count"]

		logs = game.getLogs()

		if gameInfo.status == 'Ended':
			return redirect(url_for('statistics'))

	else:
		dump = "That is not a game we have right now."
		return redirect(url_for('login'))

	return render_template('playturn.html', existingUser=existingUser, turnForm=turnForm, players=players, usersPlaying=usersPlaying, dump=dump, logs=logs, discard=discard, deck=True, deck_count=deck_count, discard_count=discard_count, hand=hand, active=active_player, endgame=True)

@app.route("/error", methods = ['GET', 'POST'])
def error():
	if('username' in session):
		passedUserName = session['username']
	else:
		passedUserName = None
	return render_template('error.html', passedUserName=passedUserName)

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404

if __name__ == "__main__":
	#db.create_all()
	if 'liveconsole' not in gethostname():
		app.run(debug = True)
    #app.run()

