from flask import Flask, render_template, session, request, flash, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect
#from sharedDB import db
from userForm import userForm
from socket import gethostname

app = Flask(__name__)

app.config.from_object('config')

CsrfProtect(app)

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

from userDB import userDB
app.register_blueprint(userDB)


from userDB import User

passedUserName = None

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/newgame")
def newGame():
    return render_template('newgame.html')

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
					passedUserName = logInForm.username.data
					return render_template('login.html')
	else:
		return render_template('newuser.html', form = logInForm)

@app.route("/profile")
def profile():
    return render_template('profile.html')

@app.route("/signedin", methods = ['GET', 'POST'])
def signIn():
	logInForm = userForm()
	if request.method == 'POST':
		if logInForm.validate() == False:
			flash('There was a problem with data that was entered.')
			return render_template('signedin.html', form = logInForm)
		else:
			#will want to replace with calls to user object
			existingUser = User.query.filter_by(username=logInForm.username.data).first()

			if(not existingUser.check_password(logInForm.password.data)):

				flash('There was a problem with the password you entered.')
				return render_template('signedin.html', form = logInForm)

			if(existingUser):
				session['username'] = existingUser.username
				return render_template('login.html')
			else:
				flash('Username does not exist.')

				return render_template('signedin.html', form = logInForm)
			print("Outside of the series of if statements")
	else:
		return render_template('signedin.html', form = logInForm)

@app.route("/statistics")
def statistics():
    return render_template('statistics.html')

@app.route("/login")
def login():

	if('username' in session):
		passedUserName = session['username']
		existingUser = User.query.filter_by(username=passedUserName).first()

		if(existingUser.role == 'Admin'):
			return render_template('adminLogin.html')
		else:
			return render_template('login.html', passedUserName)
	else:
		return render_template('index.html')

@app.route("/logout")
def logout():
	session['username'] = None
	return render_template('index.html')


if __name__ == "__main__":
	#db.create_all()
	if 'liveconsole' not in gethostname():
		app.run(debug = True)
    #app.run()
