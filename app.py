from flask import Flask, render_template, Blueprint
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config.from_object('config')

db = SQLAlchemy(app)

# Adds the gameDB module
from gameDB import gameDB
app.register_blueprint(gameDB)

from userDB import userDB
app.register_blueprint(userDB)

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/newgame")
def newGame():
    return render_template('newgame.html')

@app.route("/newuser")
def newUser():
    return render_template('newuser.html')

@app.route("/profile")
def profile():
    return render_template('profile.html')

@app.route("/signedin")
def signIn():
    return render_template('signedin.html')

@app.route("/statistics")
def statistics():
    return render_template('statistics.html')

@app.route("/login")
def login():
    return render_template('login.html')


if __name__ == "__main__":
    app.run()
