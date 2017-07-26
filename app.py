from flask import Flask, render_template
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


if __name__ == "__main__":
    app.run()
