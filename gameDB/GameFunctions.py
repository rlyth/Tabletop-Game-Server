from app import db
from .models import Game, GameInstance, Card, CardInstance, PlayersInGame, Pile, CardsInGame, GameLog
import random
from userDB.models import User

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


# Creates a GameInstance based on a Game, and creates any CardInstance and Pile
#   required to play. Adds all players to PlayersInGame and sets invites.
# Parameters:
#   baseGameID: ID of game to spawn an instance of
#   creatorID: the User id of the player who initiated the game
#   inviteList: list of User ids for the players invited to the game
# Returns: The ID of the newly created GameInstance
def initGameInstance(baseGameID, creatorID, inviteList):
    # Confirm base game exists
    try:
        Game.query.filter_by(id=baseGameID).one()
    except (MultipleResultsFound, NoResultFound):
            return None

    # Create new GameInstance for this Game
    # num_players is set to 1, and increments as players accept invites
    newGame = GameInstance(baseGameID, 1)
    db.session.add(newGame)
    db.session.commit()

    creator = PlayersInGame(newGame.id, creatorID, invite_status='Creator')
    db.session.add(creator)
    db.session.commit()

    # Add all players to PlayersInGame with invite status
    players = []
    for p in inviteList:
        newPlayer = PlayersInGame(newGame.id, p, invite_status='Invited')
        players.append(newPlayer)

    db.session.bulk_save_objects(players)
    db.session.commit()

    # Retrieve list of cards associated with baseGame
    gameCards = CardsInGame.query.filter_by(game_id=baseGameID).all()

    for card in gameCards:
        # Create (qty) instance(s) of all cards
        for x in range(0, card.quantity):
            newCard = CardInstance(newGame.id, card.card_id, card_value=card.card_value)

            db.session.add(newCard)
            db.session.commit()

    initMessage = GameLog(newGame.id, "Game created.")
    db.session.add(initMessage)
    db.session.commit()

    return newGame.id


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

    # Remove all GameLog entries
    GameLog.query.filter_by(game_instance=instanceID).delete()
    db.session.commit()

    # Delete Game Instance
    GameInstance.query.filter_by(id=instanceID).delete()
    db.session.commit()


# Retrieve a GameInstance and its base Game
# Parameters:
#   instanceID: the ID of the GameInstance to retrieve
# Returns: a GameInstance/Game object for the provided instanceID OR None
def getGameInstance(instanceID):
    try:
        return GameInstance.query \
                    .filter_by(id=instanceID) \
                    .join(Game) \
                    .one()
    except (MultipleResultsFound,NoResultFound):
        return None


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

        # Game has not yet been setup
        # Will only run once all the invites have been accepted or declined
        if (not self.isPendingInvites()) and self.game.status == 'Created':
            self.initialSetup()
            self.setStatus('Active')

        self.setVariables()


    ## NB: in the future, it might make sense to not run this automatically,
    ##      and instead make the players start the game via a function call
    def initialSetup(self):
        # Each game should implement this based on the game's rules
        return

    def setVariables(self):
        # Each game should implement this to store game-relevant variables
        return


    # NB: this could be written better
    # +1 to the win/loss/draw statistics of users
    # Parameters:
    #   win: (optional) a list containing the user ids of any player who won
    #   loss: (optional) a list containing the user ids of any player who lost
    #   draw: (optional) a list containing the user ids of any player who drew
    def gameOver(self, win=None, loss=None, draw=None):
        self.setStatus('Ended')
        self.addLog("The game has ended.")

        if win:
            winMsg = "Win: "
            for winner in win:
                w = User.query.filter_by(id=winner).first()
                w.wins += 1
                w.games_played += 1
                db.session.commit()

                winMsg += w.username + " "

            self.addLog(winMsg)

        if loss:
            loseMsg = "Lose: "
            for loser in loss:
                l = User.query.filter_by(id=loser).first()
                l.losses += 1
                l.games_played += 1
                db.session.commit()

                loseMsg += l.username + " "

            self.addLog(loseMsg)

        if draw:
            drawMsg = "Draw: "
            for drawer in draw:
                d = User.query.filter_by(id=drawer).first()
                d.draws += 1
                d.games_played += 1
                db.session.commit()

                drawMsg += d.username + " "

            self.addLog(drawMsg)


    # Calls incrementTurnsPlayed() and getNextTurn()
    def endTurn(self):
        self.endTurnMsg()

        self.incrementTurnsPlayed()

        self.setNextTurn()


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


    # NB: this could also become a bulk update
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


    # Deals (qty) cards to every pile in pilesTo, one at a time, in order
    # Parameters:
    #   pileFrom: the ID of the pile to deal from
    #   pilesTo: a list of pile IDs to deal cards to
    #   qty: the number of cards to be dealt to each pile
    # If the number of cards dealt exceeds the number of cards in pileFrom,
    #   the function will deal as many cards as exist in the pile then return
    #   None
    def dealCards(self, pileFrom, pilesTo, qty):
        for i in range(0, qty):
            for p in range(0, len(pilesTo)):
                drawn = self.drawTopCard(pileFrom, pilesTo[p])

                # pileFrom is empty
                if not drawn:
                    return None


    # Draws the top (highest pile_order) card from the specified pile and moves it
    #   to another pile
    # Parameters:
    #   pileFrom: the pile to take the top card from
    #   pileTo: the pile to move the top card to
    # The card will be placed on the top of its destination pile
    def drawTopCard(self, pileFrom, pileTo, discard=None):
        # Check that the Pile is not empty
        if not CardInstance.query.filter_by(in_pile=pileFrom).first():
            return None

        # Retrieves card from pile with the highest pile_order
        card = CardInstance.query \
                .filter_by(in_pile=pileFrom) \
                .order_by(CardInstance.pile_order.desc()) \
                .first()

        # Card's new order at destination is one higher than current highest
        # NB: replace this with moveCard call
        newOrder = self.getMaxOrder(pileTo) + 1

        card.pile_order = newOrder
        card.in_pile = pileTo
        db.session.commit()

        return True


    # Increases turns_played by 1
    def incrementTurnsPlayed(self):
        self.game.turns_played = self.game.turns_played + 1
        db.session.commit()


    # Adds a GameLog message indicating the current player's turn has ended
    def endTurnMsg(self):
        currentPlayer = PlayersInGame.query \
                            .filter_by(
                                game_instance=self.game.id,
                                turn_order=self.game.current_turn_order
                                ) \
                            .first().user_id

        self.addLog("Player " + str(currentPlayer) + " ended their turn.")


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


    # NB: find a way to do this with a bulk update to reduce queries
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



    ########################################
    ########################################
    # Invites/Joining/Leaving game
    ########################################
    ########################################

    def acceptInvite(self, userID):
        player = PlayersInGame.query \
                        .filter_by(
                            game_instance=self.game.id,
                            user_id=userID
                        ) \
                        .join(User) \
                        .first()

        # Player is game creator or already accepted
        if player.invite_status != 'Invited':
            return False

        player.invite_status = 'Accepted'
        self.game.num_players += 1
        db.session.commit()

        self.addLog(player.User.username + " has joined the game.")

        return True


    def declineInvite(self, userID):
        player = PlayersInGame.query \
                        .filter_by(
                            game_instance=self.game.id,
                            user_id=userID
                        ) \
                        .first()

        if player.invite_status != 'Invited':
            return False

        db.session.delete(player)
        db.session.commit()

        return True


    def invitePlayer(self, userID):
        newPlayer = PlayersInGame(self.game.id, userID, invite_status="Invited")

        db.session.add(newPlayer)
        db.session.commit()


    # Returns: True if not all players have accepted the game invite, False otherwise
    def isPendingInvites(self):
        pending = PlayersInGame.query \
                        .filter_by(
                            game_instance=self.game.id,
                            invite_status='Invited'
                        ) \
                        .all()

        if pending:
            return True

        return False


    ########################################
    ########################################
    # Adders
    ########################################
    ########################################


    # Creates a new Pile associated with this GameInstance
    # Parameters:
    #   pile_type: the label for the pile
    #   pile_owner: (optional) the id of the pile_owner
    #   pile_status: (optional) the pile_status value
    # Returns: the ID of the newly created pile
    def addPile(self, pile_type, pile_owner=None, pile_status=None):
        newPile = Pile(self.game.id, pile_type, pile_owner, pile_status)
        db.session.add(newPile)
        db.session.commit()

        return newPile.id


    # Creates a new GameLog associated with this GameInstance
    # Parameters:
    #   message: The text to add to the log
    # Returns: the ID of the newly created GameLog
    def addLog(self, message):
        newMsg = GameLog(self.game.id, message)
        db.session.add(newMsg)
        db.session.commit()

        return newMsg.id


    ########################################
    ########################################
    # Setters/Update
    ########################################
    ########################################


    # Sets current_turn_order to next player in line (loops back to start when
    #   end is reached)
    def setNextTurn(self):
        self.game.current_turn_order = self.getNextTurn()
        db.session.commit()


    # Sets the player's player_status to the specified value
    def setPlayerStatus(self, playerID, newStatus):
        player = PlayersInGame.query \
                        .filter_by(
                            game_instance=self.game.id,
                            user_id=playerID
                        ) \
                        .first()

        player.player_status = newStatus
        db.session.commit()


    # Sets the turn_order for a PlayersInGame entry to the specified value
    # Parameters:
    #   playerID: the ID of the player whose turn_order will change
    #   newOrder: the new turn order for this player
    # Returns: False if newOrder is invalid, True otherwise
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

        return True


    # Sets the status for a GameInstance to the specified value
    # Parameters:
    #   status: the new value for status
    def setStatus(self, status):
        self.game.status = status
        db.session.commit()


    # Sets current_turn_order to new value if valid
    # Parameters:
    #   newOrder: the value current_turn_order should be set to
    def setTurnOrder(self, newOrder):
        # New order must be in range 1 .. num_players
        if (newOrder > self.game.num_players) or (newOrder < 1):
            return False

        self.game.current_turn_order = newOrder
        db.session.commit()


    # Sets turns_played  to new value if valid
    # Parameters:
    #   newTurns: the value turns_played should be set to
    def setTurnsPlayed(self, newTurns):
        if (newTurns < 0):
            return False

        self.game.turns_played = newTurns
        db.session.commit()


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


    ########################################
    ########################################
    # Getters
    ########################################
    ########################################


    # Returns: a CardInstance/Card object with all cards in this GameInstance OR Pile
    # Will filter by the most specific property (card_id > pile > no parameters)
    #   Parameters:
    #       pile: (optional) the ID of the pile to get the cards from
    #       card_id: (optional) the ID of a specific card to retrieve
    def getCards(self, pile=None, card_id=None):
        filters = {}

        if card_id:
            filters["id"] = card_id
        elif pile:
            filters["in_pile"] = pile
        else:
            filters["game_instance"] = self.game.id

        try:
            return CardInstance.query \
                        .filter_by(**filters) \
                        .join(Card) \
                        .order_by(CardInstance.pile_order.desc()) \
                        .all()
        except NoResultFound:
            return None

    # Same as above, except returns a single Card
    def getCard(self, id=None, card_status=None, card_value=None):
        filters = {}

        if id:
            filters["id"] = id
        if card_status:
            filters["card_status"] = card_status
        if card_value:
            filters["card_value"] = card_value

        return CardInstance.query \
                    .filter_by(**filters) \
                    .join(Card) \
                    .first()


    # Returns: The user_id of the Player whose turn order matches the current turn order
    def getCurrentPlayerID(self):
        player = PlayersInGame.query \
                    .filter_by(
                        game_instance = self.game.id,
                        turn_order = self.game.current_turn_order
                    ) \
                    .first()

        if player:
            return player.user_id

        # Unlikely
        return None


    # Returns: All GameLog entries associated with this game
    def getLogs(self):
        return GameLog.query \
                    .filter_by(game_instance=self.game.id) \
                    .order_by(
                        GameLog.timestamp.desc(),
                        GameLog.id.desc()
                        ) \
                    .all()


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


    # Returns: a Player object for the player whose turn is next
    def getNextPlayer(self):
        nextTurn = self.getNextTurn()

        return PlayersInGame.query \
                    .filter_by(
                        game_instance=self.game.id,
                        turn_order=nextTurn
                        ) \
                    .first()


    # Returns: the turn_order that comes after this one (loops back to 1
    #   when end is reached)
    def getNextTurn(self):
        if (self.game.current_turn_order < self.game.num_players):
            return self.game.current_turn_order + 1
        else:
            return 1


    # Parameters:
    #   pile_type: (optional) a string with the desired pile_type
    #   pile_owner: (optional) the user ID of the desired pile_owner
    # Returns: a Pile object with every pile in this GameInstance or the Pile that
    #   matches the specifications
    def getPiles(self, pile_type=None, pile_owner = None):
        filters = {}
        filters["game_instance"] = self.game.id

        # Optional filters
        if pile_type:
            filters["pile_type"] = pile_type
        if pile_owner:
            filters["pile_owner"] = pile_owner

        try:
            return Pile.query \
                    .filter_by(**filters) \
                    .all()
        except NoResultFound:
            return None


    # The same as above, except a single result is returned
    # Parameters:
    #   pile_type: (optional) a string with the desired pile_type
    #   pile_owner: (optional) the user ID of the desired pile_owner
    # Returns: a Pile matching the input or None
    def getPile(self, pile_type=None, pile_owner = None):
        filters = {}
        filters["game_instance"] = self.game.id

        # Optional filters
        if pile_type:
            filters["pile_type"] = pile_type
        if pile_owner:
            filters["pile_owner"] = pile_owner

        return Pile.query \
                    .filter_by(**filters) \
                    .first()


    # Parameters:
    #   pile: the pile to get the card count for
    # Returns: An integer indicating the number of cards in the Pile
    def getPileCount(self, pile):
        return CardInstance.query \
                    .filter_by(in_pile=pile) \
                    .count()


    # Returns: a list of PlayersInGame/User objects with all players in this GameInstance
    def getPlayers(self):
        return PlayersInGame.query \
                    .filter_by(game_instance = self.game.id) \
                    .join(User) \
                    .order_by(PlayersInGame.turn_order) \
                    .all()


    # Returns: a CardInstance/Card object with the card in the Pile with the
    #   highest pile_order
    def getTopCard(self, pileFrom):
        # Check that the Pile exists
        if not Pile.query.filter_by(id=pileFrom).first():
            return None

        # Check that the Pile is not empty
        if not CardInstance.query.filter_by(in_pile=pileFrom).first():
            return None

        # Retrieves card from pile with the highest pile_order
        return CardInstance.query \
                .filter_by(in_pile=pileFrom) \
                .join(Card) \
                .order_by(CardInstance.pile_order.desc()) \
                .first()


# NB: if this never gets json-ified, it might be easier to just pass database objects instead
# Retrieves information about a GameInstance and outputs it as a Python object
# Parameters:
#   instanceID: the ID of the GameInstance to retrieve
# Returns: a Python object containing information about a GameInstance
# {
#   ID: (GameInstance id)
#   Num Players:
#   Turns Played:
#   Turn Order:
#   Status:
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
#   Log: [
#       {
#           Message:
#           Timestamp:
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
    gameInfo["Status"] = gameInstance.status

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

    # Add all GameLog entries to gameInfo
    # Newest messages are at the front of the list
    logs = GameLog.query \
                .filter_by(game_instance=instanceID) \
                .order_by(GameLog.timestamp.desc()) \
                .all()

    gameInfo["Log"] = []
    for log in logs:
        newLog = {}

        newLog["Message"] = log.message
        newLog["Timestamp"] = log.timestamp.strftime('%x %X')

        gameInfo["Log"].append(newLog)

    return gameInfo