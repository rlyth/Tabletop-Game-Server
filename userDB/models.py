from app import db
from werkzeug.security import generate_password_hash, check_password_hash
#moved this here based on https://stackoverflow.com/questions/34281873/how-do-i-split-flask-models-out-of-app-py-without-passing-db-object-all-over
from flask_sqlalchemy import SQLAlchemy

#db = SQLAlchemy(app)

# Partly based on salt/hash examples from http://flask.pocoo.org/snippets/54/
class User(db.Model):
    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    display_name = db.Column(db.String(50))
    games_played = db.Column(db.Integer)
    wins = db.Column(db.Integer)
    losses = db.Column(db.Integer)
    draws = db.Column(db.Integer)

    _password = db.Column(db.String(100), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

        # Initialize player stats
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0

    def set_password(self, password):
        self._password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self._password, password)

    @classmethod
    def validate_user(cls, username, password):
        user = cls.query.filter_by(username=username).first()

        if user:
            return user, user.check_password(password)

        # user does not exist
        return user, False


# Draft
# Probably leave implementation for this as a stretch goal if there's time afterwards
"""
class FriendList(db.Model):
    __tablename__ = 'FriendList'

    user_id = db.Column(db.ForeignKey('User.id', ondelete='CASCADE', onupdate='CASCADE'))
    friend_id = db.Column(db.ForeignKey('User.id', ondelete='CASCADE', onupdate='CASCADE'))
    # For things such as 'Pending Confirmation'
    friend_status = db.Column(db.String(50))
"""