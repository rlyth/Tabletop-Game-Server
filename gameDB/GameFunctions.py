import gameDB.models as models
import random
from app import db
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
        models.Game.query.filter_by(id=baseGameID).one()
    except MultipleResultsFound:
            # id is unique, this shouldnt happen
            return None
    except NoResultFound:
            return None

    # Create new GameInstance for this Game
    newGame = models.GameInstance(baseGameID, len(playerList))
    db.session.add(newGame)
    db.session.commit()

    # Add all players to PlayersInGame
    for p in playerList:
        newPlayer = models.PlayersInGame(game_instance=newGame.id)
        newPlayer.user_id = p
        db.session.add(newPlayer)
        db.session.commit()

    # Initialize pile(s)
    tempPile = models.Pile(game_instance=newGame.id, pile_type="Init_Temp_Pile")
    db.session.add(tempPile)
    db.session.commit()

    # Retrieve list of cards associated with baseGame
    gameCards = models.CardsInGame.query.filter_by(game_id=baseGameID).all()

    for card in gameCards:
        # Create (qty) instance(s) of all cards
        for x in range(0, card.quantity):
            #newCard = models.CardInstance(in_pile=tempPile.id,base_card=card.card_id)
            newCard = models.CardInstance(newGame.id, card.card_id, tempPile.id)

            db.session.add(newCard)
            db.session.commit()

    return newGame.id


# Retrieves information about a GameInstance and outputs it as a Python object
# Parameters:
#   instanceID: the ID of the GameInstance to retrieve
# Returns: a Python object containing information about a GameInstance
def fetchGameInstance(instanceID):
    gameInfo = {}

    try:
        gameInstance = models.GameInstance.query.filter_by(id=instanceID).one()
    except MultipleResultsFound:
            # id is unique, this shouldnt happen
            return None
    except NoResultFound:
            return None

    gameInfo["ID"] = gameInstance.id
    gameInfo["Num Players"] = gameInstance.num_players
    gameInfo["Turns Played"] = gameInstance.turns_played
    gameInfo["Turn Order"] = gameInstance.current_turn_order

    baseGame = models.Game.query.filter_by(id=gameInstance.base_game).one()
    gameInfo["Base Game"] = {}
    gameInfo["Base Game"]["ID"] = baseGame.id
    gameInfo["Base Game"]["Name"] = baseGame.name
    gameInfo["Base Game"]["Description"] = baseGame.description
    gameInfo["Base Game"]["Minimum Players"] = baseGame.min_players
    gameInfo["Base Game"]["Maximum Players"] = baseGame.max_players

    players = models.PlayersInGame.query.filter_by(game_instance=instanceID).all()
    gameInfo["Players"] = []
    for p in players:
        newPlayer = {}
        newPlayer["ID"] = p.user_id
        newPlayer["Turn Order"] = p.turn_order
        gameInfo["Players"].append(newPlayer)

    piles = models.Pile.query.filter_by(game_instance=instanceID).all()
    gameInfo["Piles"] = []
    for p in piles:
        newPile = {}
        newPile["ID"] = p.id
        newPile["Type"] = p.pile_type
        newPile["Owner"] = p.pile_owner

        cards = models.CardInstance.query.filter_by(in_pile=p.id).all()
        newPile["Cards"] = []
        # Note: consider refactoring CardInstance to copy over name/desc info
        #   from Card to reduce extraneous queries
        for c in cards:
            newCard = {}

            newCard["ID"] = c.id
            newCard["Base Card"] = c.base_card
            newCard["In Pile"] = c.in_pile
            newCard["Card Value"] = c.card_value

            newPile["Cards"].append(newCard)

        gameInfo["Piles"].append(newPile)

    return gameInfo


# Deletes a GameInstance and any CardInstance, Pile, and PlayersInGame entries
# associated with it
# Parameters:
#   instanceID: the ID of the GameInstance to delete
def deleteGameInstance(instanceID):
    # Delete all CardInstances associated with this GameInstance
    models.CardInstance.query.filter_by(game_instance=instanceID).delete()
    db.session.commit()

    # Delete Piles
    models.Pile.query.filter_by(game_instance=instanceID).delete()
    db.session.commit()

    # Remove all PlayersInGame
    models.PlayersInGame.query.filter_by(game_instance=instanceID).delete()
    db.session.commit()

    # Delete Game Instance
    models.GameInstance.query.filter_by(id=instanceID).delete()
    db.session.commit()

    return


# Once instantiated with a valid instanceID, various functions can be called on
#   this object in order to progress the game state
class thisGame:
    def __init__(self, instanceID):
        #self.id = instanceID

        try:
            self.game = models.GameInstance.query.filter_by(id=instanceID).one()
        except MultipleResultsFound:
                return None
        except NoResultFound:
                return None

    ## Higher level functions
    # Functions that call other functions, or perform multiple actions at once

    # Calls incrementTurnsPlayed() and getNextTurn()
    def endTurn(self):
        self.incrementTurnsPlayed()

        self.getNextTurn()

    # Randomly assigns a turn_order to all players in this GameInstance
    def randomizePlayers(self):
        order = []

        # Make a list with all possible turn order values
        for i in range(1, self.game.num_players + 1):
            order.append(i)

        random.shuffle(order)

        players = models.PlayersInGame.query.filter_by(
            game_instance = self.game.id).all()

        for i, player in enumerate(players):
            player.turn_order = order[i]
            db.session.commit()


    ## Lower level functions
    # More elemental functions, meant to perform smaller/single tasks

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
        playerGame = models.PlayersInGame.query.filter_by(
            user_id = playerID,
            game_instance = self.game.id).one()

        playerGame.turn_order = newOrder
        db.session.commit()