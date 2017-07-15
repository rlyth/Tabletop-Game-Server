import gameDB.models as models
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
            newCard = models.CardInstance(in_pile=tempPile.id,base_card=card.card_id)

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
    # Get all Piles associated with this GameInstance
    piles = models.Pile.query.filter_by(game_instance=instanceID).all()
    db.session.commit()

    for pile in piles:
        # Delete all CardInstances in this pile
        models.CardInstance.query.filter_by(in_pile=pile.id).delete()
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