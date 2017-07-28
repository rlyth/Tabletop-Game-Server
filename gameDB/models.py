from __main__ import app
#moved this here based on https://stackoverflow.com/questions/34281873/how-do-i-split-flask-models-out-of-app-py-without-passing-db-object-all-over
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)


# "Base Game"
# Stores unchanging information about a game, which is used to spawn a GameInstance
class Game(db.Model):
    __tablename__ = 'Game'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    min_players = db.Column(db.Integer)
    max_players = db.Column(db.Integer)


# "Base Card"
# Describes a card, may be used in multiple games
# Used to spawn a CardInstance
class Card(db.Model):
    __tablename__ = 'Card'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    card_type = db.Column(db.String(50))


# A specific instance of a game in progress
# Stores info on the current game state
class GameInstance(db.Model):
    __tablename__ = 'GameInstance'

    id = db.Column(db.Integer, primary_key=True)
    base_game = db.Column(db.ForeignKey('Game.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    num_players = db.Column(db.Integer)
    turns_played = db.Column(db.Integer, default=0)
    current_turn_order = db.Column(db.Integer, default=1)

    Game = db.relationship('Game', primaryjoin='GameInstance.base_game == Game.id', backref='game_instances')

    def __init__(self, base_game, num_players):
        self.base_game = base_game
        self.num_players = num_players
        self.turns_played = 0
        self.current_turn_order = 1


# Might be separated out into Pile/PileInstance -- tbd
# Describes any collection of cards (deck, discard, hand, bank, etc)
class Pile(db.Model):
    __tablename__ = 'Pile'

    id = db.Column(db.Integer, primary_key=True)
    game_instance = db.Column(db.Integer, nullable=False)
    pile_type = db.Column(db.String(50))
    pile_status = db.Column(db.String(50))
    pile_owner = db.Column(db.Integer)



# A specific instance of a Card for a currently running GameInstance
# Stores info on the current card state (location etc)
class CardInstance(db.Model):
    __tablename__ = 'CardInstance'

    id = db.Column(db.Integer, primary_key=True)
    game_instance = db.Column(db.ForeignKey('GameInstance.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    base_card = db.Column(db.ForeignKey('Card.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    in_pile = db.Column(db.ForeignKey('Pile.id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    pile_order = db.Column(db.Integer)
    card_value = db.Column(db.Integer)
    card_status = db.Column(db.String(50))

    Card = db.relationship('Card', primaryjoin='CardInstance.base_card == Card.id', backref='card_instances')
    Pile = db.relationship('Pile', primaryjoin='CardInstance.in_pile == Pile.id', backref='card_instances')
    GameInstance = db.relationship('GameInstance', primaryjoin='CardInstance.game_instance == GameInstance.id', backref='card_instances')

    def __init__(self, game_instance, base_card, in_pile=None):
        self.game_instance = game_instance
        self.base_card = base_card

        if in_pile:
            self.in_pile = in_pile


# A list of all the Cards needed to play a Game
# Since the same cards can be used for multiple games (e.g. a standard deck of cards)
# this is a many-to-many relationship
class CardsInGame(db.Model):
    __tablename__ = 'CardsInGame'

    card_id = db.Column(db.ForeignKey('Card.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    game_id = db.Column(db.ForeignKey('Game.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    card = db.relationship('Card', primaryjoin='CardsInGame.card_id == Card.id', backref='cards_in_games')
    game = db.relationship('Game', primaryjoin='CardsInGame.game_id == Game.id', backref='cards_in_games')


# Players associated with a currently GameInstance and information about the
# player in relation to the GameInstance (e.g. turn order)
class PlayersInGame(db.Model):
    __tablename__ = 'PlayersInGame'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False, server_default=db.FetchedValue())
    game_instance = db.Column(db.ForeignKey('GameInstance.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False, index=True, server_default=db.FetchedValue())
    turn_order = db.Column(db.Integer)
    player_status = db.Column(db.String(50))

    GameInstance = db.relationship('GameInstance', primaryjoin='PlayersInGame.game_instance == GameInstance.id', backref='players_in_games')