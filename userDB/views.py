from flask import Blueprint, request, render_template, flash, session, redirect, url_for
from sqlalchemy.orm.exc import NoResultFound

from .forms import createUser, updatePassword
from .models import User
from app import db

from gameDB import GameFunctions
from gameDB.models import PlayersInGame

userDB = Blueprint('userDB', __name__, url_prefix='/user')


@userDB.route("/home", methods= ['GET'])
def home():
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

        # find some other way to deal with admin users
        if(existingUser.role == 'Admin'):
        	return render_template('adminLogin.html', passedUserName=passedUserName, gname=gname, gameids=gameids, playableGame=playableGame, users=users, players=players)
        else:
        	return render_template('user/home.html', current_user=passedUserName, gname=gname, gameids=gameids, playableGame=playableGame, users=users, players=players)

	# send user to login page instead?
    else:
    	return render_template('index.html')

@userDB.route("/new", methods = ['GET', 'POST'])
def newUser():
    form = createUser()
    if request.method == 'POST':
        # Validate input data, then create new user
        if form.validate() == True:
            existingUser = User.query.filter_by(username=form.username.data).first()

            if existingUser:
                flash('Sorry, username already exists.')

            elif form.password.data != form.password2.data:
                flash('The passwords do not match.')

            else:
                newUser = User(form.username.data, form.password.data)
                db.session.add(newUser)
                db.session.commit()

                # redirect user
                session['username'] = form.username.data
                return redirect(url_for('login'))

    return render_template('user/create.html', form=form)


@userDB.route("/profile/<int:userID>/", methods=['GET'])
def profile(userID):
    user = User.query.filter_by(id=userID).first()

    # NB: not correctly checking logged-in status
    if 'username' in session:
        passedUserName = session['username']
    else:
        passedUserName = None

    if user:
        if user.games_played > 0:
            win_rate = round(100 * (user.wins/user.games_played), 2)
        else:
            win_rate = 0.00

        return render_template('user/profile.html', user=user, win_rate=win_rate, username=user.username)

    # Invalid user id
    else:
        return render_template('error.html', passedUserName=passedUserName, errormsg='That user does not exist.')


# NB: move password update functionality elsewhere
@userDB.route("/profile", methods = ['GET', 'POST'])
def myProfile():
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