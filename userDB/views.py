from flask import Blueprint, request, render_template, flash, session, redirect, url_for, g
#from sqlalchemy.orm.exc import NoResultFound

from .forms import createUser, updatePassword
from .models import User
from app import db

from gameDB import GameFunctions

userDB = Blueprint('userDB', __name__, url_prefix='/user')


# Sets the value of g.user to current user if logged in, and None otherwise
@userDB.before_request
def before_request():
    try:
        g.username = session['username']
        g.userid = session['userid']
    except:
        g.username = None
        g.userid = None


@userDB.route("/home", methods= ['GET'])
def home():
    if g.username is not None and g.userid is not None:
        player_games = GameFunctions.getPlayerGames(g.userid)

        # Various game categories
        player_move = []
        other_move = []
        waiting_join = []
        invited = []
        completed = []
        # NB: move invites to notification tray?

        for game in player_games:
            if game.invite_status == 'Invited':
                # Catches all games where player needs to accept invite
                invited.append(game)
            elif game.GameInstance.status == 'Ended':
                # Catches all completed games
                completed.append(game)
            else:
                # create gamePlay object to trigger setup, if needed
                this_game = GameFunctions.gamePlay(game.GameInstance.id)

                # game has not started
                if this_game.getStatus == 'Created':
                    waiting_join.append(game)

                # this player's move
                elif this_game.getCurrentPlayerID() == g.userid:
                    player_move.append(game)

                # other player's move
                else:
                    other_move.append(game)

        return render_template('user/home.html',
                                    current_user=g.username,
                                    player_move=player_move,
                                    other_move=other_move,
                                    waiting_join=waiting_join,
                                    completed=completed,
                                    invited=invited)

	# NB: send user to login page instead?
    else:
    	return redirect(url_for('main'))

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
                session['username'] = newUser.username
                session['userid'] = newUser.id
                return redirect(url_for('userDB.home'))

    return render_template('user/create.html', form=form)


@userDB.route("/profile/<int:userID>/", methods=['GET'])
def profile(userID):
    user = User.query.filter_by(id=userID).first()

    if user:
        if user.games_played > 0:
            win_rate = round(100 * (user.wins/user.games_played), 2)
        else:
            win_rate = 0.00

        return render_template('user/profile.html', user=user, win_rate=win_rate, username=user.username)

    # Invalid user id
    else:
        return render_template('error.html', current_user=g.username, error_msg='That user does not exist.')


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