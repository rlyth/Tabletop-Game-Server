import models
from app import db
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound


# Parameters: id of game to spawn an instance of, id list of players joining game
# Returns: The id of the newly created GameInstance
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


def fetchGameInstance(instanceID):
    # Query everything and build a huge JSON object, probably
    return

def deleteGameInstance(instanceID):
    # Delete all CardInstances
    # Delete all Piles
    # Remove all PlayersInGame
    # Delete Game Instance
    return