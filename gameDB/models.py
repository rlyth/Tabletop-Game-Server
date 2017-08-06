from app import db


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
    img_front = db.Column(db.String(100))
    img_back = db.Column(db.String(100))


# A specific instance of a game in progress
# Stores info on the current game state
class GameInstance(db.Model):
    __tablename__ = 'GameInstance'

    id = db.Column(db.Integer, primary_key=True)
    base_game = db.Column(db.ForeignKey('Game.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    num_players = db.Column(db.Integer)
    turns_played = db.Column(db.Integer, default=0)
    current_turn_order = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50))

    Game = db.relationship('Game', primaryjoin='GameInstance.base_game == Game.id', backref='game_instances')

    def __init__(self, base_game, num_players):
        self.base_game = base_game
        self.num_players = num_players
        self.current_turn_order = 1
        self.turns_played = 0
        self.status = 'Created'


# Might be separated out into Pile/PileInstance -- tbd
# Describes any collection of cards (deck, discard, hand, bank, etc)
class Pile(db.Model):
    __tablename__ = 'Pile'

    id = db.Column(db.Integer, primary_key=True)
    game_instance = db.Column(db.Integer, nullable=False)
    pile_type = db.Column(db.String(50), nullable=False)
    pile_status = db.Column(db.String(50))
    pile_owner = db.Column(db.Integer)

    def __init__(self, game_instance, pile_type, pile_owner=None, pile_status=None):
        self.game_instance = game_instance
        self.pile_type = pile_type

        if pile_status:
            self.pile_status = pile_status
        if pile_owner:
            self.pile_owner = pile_owner


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

    def __init__(self, game_instance, base_card, in_pile=None, card_value=None):
        self.game_instance = game_instance
        self.base_card = base_card

        if in_pile:
            self.in_pile = in_pile

        if card_value:
            self.card_value = card_value


# A list of all the Cards needed to play a Game
# Since the same cards can be used for multiple games (e.g. a standard deck of cards)
# this is a many-to-many relationship
class CardsInGame(db.Model):
    __tablename__ = 'CardsInGame'

    card_id = db.Column(db.ForeignKey('Card.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    game_id = db.Column(db.ForeignKey('Game.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    # The initial card_value CardInstance starts with
    card_value = db.Column(db.Integer)

    card = db.relationship('Card', primaryjoin='CardsInGame.card_id == Card.id', backref='cards_in_games')
    game = db.relationship('Game', primaryjoin='CardsInGame.game_id == Game.id', backref='cards_in_games')


# Players associated with a currently GameInstance and information about the
# player in relation to the GameInstance (e.g. turn order)
class PlayersInGame(db.Model):
    __tablename__ = 'PlayersInGame'

    user_id = db.Column(db.ForeignKey('User.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False, index=True)
    game_instance = db.Column(db.ForeignKey('GameInstance.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False, index=True, server_default=db.FetchedValue())
    turn_order = db.Column(db.Integer)
    player_status = db.Column(db.String(50))

    GameInstance = db.relationship('GameInstance', primaryjoin='PlayersInGame.game_instance == GameInstance.id', backref='players_in_games')
    User = db.relationship('User', primaryjoin='PlayersInGame.user_id == User.id', backref='players_in_games')


# Messages associated with a current GameInstance (actions taken, etc)
class GameLog(db.Model):
    __tablename__= 'GameLog'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime)
    game_instance = db.Column(db.ForeignKey('GameInstance.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    GameInstance = db.relationship('GameInstance', primaryjoin='GameLog.game_instance == GameInstance.id', backref='log_instances')

    def __init__(self, game_instance, message):
        self.message = message
        self.game_instance = game_instance
        self.timestamp = db.func.now()
