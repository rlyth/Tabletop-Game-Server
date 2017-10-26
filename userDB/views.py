from flask import Blueprint, request, render_template, flash, session, redirect, url_for
from sqlalchemy.orm.exc import NoResultFound

from .forms import createUser, updatePassword
from .models import User
from app import db

userDB = Blueprint('userDB', __name__, url_prefix='/user')

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

    return render_template('user/create.html', form=form, htitle="Create New Account")


# NB: roll statistics into a "true" profile page with user info
@userDB.route("/statistics")
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


# NB: move password update functionality elsewhere
@userDB.route("/profile", methods = ['GET', 'POST'])
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