from flask import Flask, render_template, request, flash, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect
from userForm import userForm
from socket import gethostname

app = Flask(__name__)

app.secret_key = 'somerandomstring'
CsrfProtect(app)

#app.config.from_object('config')

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


# Adds the gameDB module
#from gameDB import gameDB
#app.register_blueprint(gameDB)

#from userDB import userDB
from userDB.models import User
#app.register_blueprint(userDB)

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
				#add new user to db
				if(logInForm.password.data != logInForm.password2.data):
					flash('The passwords do not match.')
					return render_template('newuser.html', form = logInForm)
				else:
					addUserToDB(logInForm.username.data, logInForm.password.data)
					return render_template('login.html', form = logInForm)
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
			return render_template('signedin.html', form = logInForm)
		else:
			#will want to replace with calls to user object
			existingUser = User.query.filter_by(username=logInForm.username.data).first()

			if(existingUser.password != logInForm.password.data):
				flash('There was a problem with the password you entered.')
				return render_template('signedin.html', form = logInForm)

			if(existingUser):
				return render_template('login.html')
			else:
				flash('Username does not exist.')
				return render_template('signedin.html', form = logInForm)
	else:
		return render_template('signedin.html', form = logInForm)

@app.route("/statistics")
def statistics():
    return render_template('statistics.html')

@app.route("/login",)
def login():
    return render_template('login.html')

@app.route("/logout")
def logout():
    return render_template('index.html')


if __name__ == "__main__":
	db.create_all()
	if 'liveconsole' not in gethostname():
		app.run(debug = True)
    #app.run()
