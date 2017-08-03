from app import db
from .models import Game, GameInstance, Card, CardInstance, PlayersInGame, Pile, CardsInGame
import random

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


# Creates a GameInstance based on a Game, and creates any CardInstance and Pile
#   required to play. Adds all players to PlayersInGame.
# Parameters:
#   baseGameID: ID of game to spawn an instance of
#   playerList: list of ID for players joining game
# Returns: The ID of the newly created GameInstance
def initGameInstance(baseGameID, playerList):
    # Confirm base game exists
    try:
        Game.query.filter_by(id=baseGameID).one()
    except MultipleResultsFound:
            return None
    except NoResultFound:
            return None

    # Create new GameInstance for this Game
    newGame = GameInstance(baseGameID, len(playerList))
    db.session.add(newGame)
    db.session.commit()

    # Add all players to PlayersInGame
    for p in playerList:
        newPlayer = PlayersInGame(game_instance=newGame.id)
        newPlayer.user_id = p
        db.session.add(newPlayer)
        db.session.commit()

    # Retrieve list of cards associated with baseGame
    gameCards = CardsInGame.query.filter_by(game_id=baseGameID).all()

    for card in gameCards:
        # Create (qty) instance(s) of all cards
        for x in range(0, card.quantity):
            newCard = CardInstance(newGame.id, card.card_id)

            db.session.add(newCard)
            db.session.commit()

    return newGame.id


# Retrieves information about a GameInstance and outputs it as a Python object
# Parameters:
#   instanceID: the ID of the GameInstance to retrieve
# Returns: a Python object containing information about a GameInstance
# {
#   ID: (GameInstance id)
#   Num Players:
#   Turns Played:
#   Turn Order:
#   Base Game: {
#       ID: (Game id)
#       Name:
#       Description:
#       Minimum Players:
#       Maximum Players:
#   }
#   Players: [
#       {
#           ID: (Player id)
#           Turn Order:
#       }
#       {
#           ...
#       }
#   ]
#   Piles: [
#       {
#           ID: (Pile id)
#           Type:
#           Owner:
#           Status:
#       }
#       {
#           ...
#       }
#   ]
#   Cards: [
#       {
#           ID: (CardInstance id)
#           Base Card ID: (Card id)
#           Name:
#           Description:
#           Type:
#           Front: (path to the card front image)
#           Back: (path to the card back image)
#           Value:
#           Status:
#           In Pile:
#           Pile Order:
#       }
#       {
#           ...
#       }
#   ]
# }
def fetchGameInstance(instanceID):
    gameInfo = {}

    try:
        gameInstance = GameInstance.query \
                            .filter_by(id=instanceID) \
                            .join(Game) \
                            .one()
    except MultipleResultsFound:
            # id is unique, this shouldnt happen
            return None
    except NoResultFound:
            return None


    # Add Game and GameInstance to gameInfo
    gameInfo["ID"] = gameInstance.id
    gameInfo["Num Players"] = gameInstance.num_players
    gameInfo["Turns Played"] = gameInstance.turns_played
    gameInfo["Turn Order"] = gameInstance.current_turn_order

    gameInfo["Base Game"] = {}
    gameInfo["Base Game"]["ID"] = gameInstance.Game.id
    gameInfo["Base Game"]["Name"] = gameInstance.Game.name
    gameInfo["Base Game"]["Description"] = gameInstance.Game.description
    gameInfo["Base Game"]["Minimum Players"] = gameInstance.Game.min_players
    gameInfo["Base Game"]["Maximum Players"] = gameInstance.Game.max_players

    # Add all PlayersInGame to gameInfo
    players = PlayersInGame.query \
                    .filter_by(game_instance=instanceID) \
                    .all()

    gameInfo["Players"] = []
    for p in players:
        newPlayer = {}

        newPlayer["ID"] = p.user_id
        newPlayer["Turn Order"] = p.turn_order

        gameInfo["Players"].append(newPlayer)

    # Add all Piles to gameInfo
    piles = Pile.query \
                .filter_by(game_instance=instanceID) \
                .all()

    gameInfo["Piles"] = []
    for p in piles:
        newPile = {}

        newPile["ID"] = p.id
        newPile["Type"] = p.pile_type
        newPile["Owner"] = p.pile_owner
        newPile["Status"] = p.pile_status

        gameInfo["Piles"].append(newPile)

    # Add all CardInstances to gameInfo
    cards = CardInstance.query \
                .filter_by(game_instance=instanceID) \
                .join(Card) \
                .all()

    gameInfo["Cards"] = []
    for c in cards:
        newCard = {}

        newCard["ID"] = c.id
        newCard["Base Card ID"] = c.base_card
        newCard["Name"] = c.Card.name
        newCard["Description"] = c.Card.description
        newCard["Type"] = c.Card.card_type
        newCard["Front"] = c.Card.img_front
        newCard["Back"] = c.Card.img_back
        newCard["Value"] = c.card_value
        newCard["Status"] = c.card_status
        newCard["In Pile"] = c.in_pile
        newCard["Pile Order"] = c.pile_order

        gameInfo["Cards"].append(newCard)

    return gameInfo


# Deletes a GameInstance and any CardInstance, Pile, and PlayersInGame entries
# associated with it
# Parameters:
#   instanceID: the ID of the GameInstance to delete
def deleteGameInstance(instanceID):
    # Delete all CardInstances associated with this GameInstance
    CardInstance.query.filter_by(game_instance=instanceID).delete()
    db.session.commit()

    # Delete Piles
    Pile.query.filter_by(game_instance=instanceID).delete()
    db.session.commit()

    # Remove all PlayersInGame
    PlayersInGame.query.filter_by(game_instance=instanceID).delete()
    db.session.commit()

    # Delete Game Instance
    GameInstance.query.filter_by(id=instanceID).delete()
    db.session.commit()


# Once instantiated with a valid instanceID, various functions can be called on
#   this object in order to progress the game state
class gamePlay:
    def __init__(self, instanceID):
        try:
            self.game = GameInstance.query \
                            .filter_by(id=instanceID) \
                            .one()
        except MultipleResultsFound:
                return None
        except NoResultFound:
                return None


    # Calls incrementTurnsPlayed() and getNextTurn()
    def endTurn(self):
        self.incrementTurnsPlayed()

        self.getNextTurn()


    # Randomly assigns a unique turn_order to all players in this GameInstance
    def randomizePlayers(self):
        # Make a list with all possible turn order values
        order = list(range(1, self.game.num_players + 1))

        random.shuffle(order)

        players = PlayersInGame.query \
                    .filter_by(game_instance = self.game.id) \
                    .all()

        for i, player in enumerate(players):
            player.turn_order = order[i]
            db.session.commit()

    # Randomizes the order of the CardInstances associated with a pile
    # Parameters:
    #   pileID: the ID of the pile to shuffle
    def shufflePile(self, pileID):
        cards = CardInstance.query \
                    .filter_by(in_pile=pileID) \
                    .all()

        order = list(range(1, len(cards) + 1))

        random.shuffle(order)

        for i, card in enumerate(cards):
            card.pile_order = order[i]
            db.session.commit()


    # Increases turns_played by 1
    def incrementTurnsPlayed(self):
        self.game.turns_played = self.game.turns_played + 1
        db.session.commit()


    # Sets current_turn_order to next player in line (loops back to start when
    #   end is reached)
    def getNextTurn(self):
        if (self.game.current_turn_order < self.game.num_players):
            self.game.current_turn_order = self.game.current_turn_order + 1
            db.session.commit()
        else:
            self.game.current_turn_order = 1
            db.session.commit()


    # Sets current_turn_order to new value if valid
    # Parameters:
    #   new_order: the value current_turn_order should be set to
    def setTurnOrder(self, newOrder):
        # New order must be in range 1 .. num_players
        if (newOrder > self.game.num_players) or (newOrder < 1):
            return False

        self.game.current_turn_order = newOrder
        db.session.commit()


    # Sets the turn_order for a PlayersInGame entry to the specified value
    # Parameters:
    #   playerID: the ID of the player whose turn_order will change
    #   newOrder: the new turn order for this player
    # This function is not responsible for ensuring that each player has a unique
    #   turn order
    def setPlayerTurn(self, playerID, newOrder):
        newOrder = int(newOrder)

        # New order must be in range 1 .. num_players
        if (newOrder > self.game.num_players) or (newOrder < 1):
            return False

        # Get the entry for this player in this game instance
        playerGame = PlayersInGame.query.filter_by(
            user_id = playerID,
            game_instance = self.game.id).one()

        playerGame.turn_order = newOrder
        db.session.commit()


    # Draws the top (highest pile_order) card from the specified pile and moves it
    #   to another pile
    # Parameters:
    #   pileFrom: the pile to take the top card from
    #   pileTo: the pile to move the top card to
    # The card will be placed on the top of its destination pile
    def drawTopCard(self, pileFrom, pileTo):
        # Check that the Pile is not empty
        if not CardInstance.query.filter_by(in_pile=pileFrom).first():
            return None

        # Retrieves card from pile with the highest pile_order
        card = CardInstance.query \
                .filter_by(in_pile=pileFrom) \
                .order_by(CardInstance.pile_order.desc()) \
                .first()

        # Card's new order at destination is one higher than current highest
        newOrder = self.getMaxOrder(pileTo) + 1

        card.pile_order = newOrder
        card.in_pile = pileTo
        db.session.commit()


    # Moves the specified CardInstance to a different Pile
    # Parameters:
    #   cardID: the ID of the CardInstance to move
    #   pileTo: the destination Pile
    # The card will be placed on the top of its destination pile
    def moveCard(self, cardID, pileTo):
        # Check that the CardInstance exists
        try:
            card = CardInstance.query \
                        .filter_by(id=cardID) \
                        .one()
        except NoResultFound:
            return None

        # Check that the destination Pile exists
        try:
            Pile.query.filter_by(id=pileTo).one()
        except NoResultFound:
            return None

        card.pile_order = self.getMaxOrder(pileTo) + 1
        card.in_pile = pileTo
        db.session.commit()


    # Moves every card in a Pile to a different Pile
    # Parameters:
    #   pileFrom: the source pile to move all cards from
    #   pileTo: the destination pile for the moved cards
    # The moved cards will be added to the top of the destination Pile, starting
    #   from the top of the source pile
    def moveAll(self, pileFrom, pileTo):
        try:
            Pile.query.filter_by(id=pileFrom).one()
            Pile.query.filter_by(id=pileTo).one()
        except NoResultFound:
            return None

        cardsFrom = CardInstance.query.filter_by(in_pile=pileFrom).all()
        for card in cardsFrom:
            self.moveCard(card.id, pileTo)


    # Allows changes to data fields of a CardInstance. To update in_pile, use the
    #   moveCard function instead.
    # Parameters:
    #   cardID: the ID of the CardInstance to update
    #   card_value: (optional) an integer value
    #   card_type: (optional) a string
    def updateCardInstance(self, cardID, card_value=None, card_type=None, card_status=None):
        try:
            card = CardInstance.query.filter_by(id = cardID).one()
        except NoResultFound:
            return None

        if card_value:
            card.card_value = card_value
        if card_type:
            card.card_type = card_type
        if card_status:
            card.card_status = card_status

        db.session.commit()


    # Returns the largest pile_order of every CardInstance in specified Pile
    # Parameters:
    #   pile: the ID of the pile to get the maximum pile_order of
    # Returns: the maximum pile_order in the Pile as an integer
    def getMaxOrder(self, pile):
        if not CardInstance.query \
                    .filter_by(in_pile=pile) \
                    .first():
            # Pile is empty
            return 0
        else:
            return CardInstance.query \
                    .filter_by(in_pile=pile) \
                    .order_by(CardInstance.pile_order.desc()) \
                    .first().pile_order