from gameDB.GameFunctions import gamePlay

# Uno extends gamePlay
class Uno(gamePlay):

    # This will only be called once, and enacts Uno-specific set-up
    def initialSetup(self):
        # Starting turn order is random
        self.randomizePlayers()

        # Create piles
        deck = self.addPile("Deck")
        discard = self.addPile("Discard")

        # Create Hand for every player
        players = self.getPlayers()
        hands = []
        for p in players:
            newHand = self.addPile("Hand", pile_owner=p.user_id)
            hands.append(newHand)

        # Move all cards to main deck
        self.moveAll(deck)

        # Shuffle deck
        self.shufflePile(deck)

        # Deal 7 cards to each player hand
        self.dealCards(deck, hands, 7)

        # Draw first card and place on discard
        self.drawTopCard(deck, discard)

        # Check if top card is Wild
        top = self.getTopCard(discard)
        if top.Card.card_type == 'Wild':
            self.updateCardInstance(top.id, card_status='Any')

        return True


    # This is called any time a new Uno object is created
    def setVariables(self):
        self.deck = self.getPile(pile_type="Deck")
        self.discard = self.getPile(pile_type="Discard")


    # For testing
    def resetGame(self):
        self.randomizePlayers()
        self.setTurnsPlayed(0)

        # Move all cards to main deck
        self.moveAll(self.deck.id)

        self.shufflePile(self.deck.id)

        hands = self.getPiles(pile_type="Hand")
        handid = []
        for hand in hands:
            handid.append(hand.id)

        # Deal 7 cards to each player hand
        self.dealCards(self.deck.id, handid, 7)

        # Draw first card and place on discard
        self.drawTopCard(self.deck.id, self.discard.id)


        # Check if top card is Wild
        top = self.getTopCard(self.discard.id)
        if top.Card.card_type == 'Wild':
            self.updateCardInstance(top.id, card_status='Any')


        self.setStatus('Active')

        self.addLog('Game reset.')


    # This draws a card and (for now) ends the player's turn
    #   Should only be used by the current player, not when another player
    #   is forced to draw
    # Parameters:
    #   playerID: the ID of the player drawing the card
    def draw(self, playerID):
        self.drawFromDeck(playerID)


        player = self.getPlayer(user_id=playerID)
        self.addLog(player.User.username + " drew from the deck.")

        # The turn ends after the player draws a card
        # this might not exactly match Uno rules, but it'll do for now
        self.endTurn()


    # Attempts to draw from the deck, if the deck is empty, shuffles discard
    #   into deck and attempts to draw again
    # Parameters:
    #   playerID: the id of the player whose hand the card should be drawn to
    def drawFromDeck(self, playerID):
        hand = self.getPile(pile_type="Hand", pile_owner=playerID)

        # Deck is empty
        if not self.drawTopCard(self.deck.id, hand.id):
            # Temporarily store top discard card
            top = self.getTopCard(self.discard.id)

            # Move all cards from discard to deck
            self.moveAll(self.deck.id, pileFrom=self.discard.id)

            # Move top discard card back to discard
            self.moveCard(top.id, self.discard.id)

            self.shufflePile(self.deck.id)

            # Draw again; if pile is still empty, continue anyway
            self.drawTopCard(self.deck.id, hand.id)



    # Determines whether a play is legal, then performs the appropriate actions
    # Parameters:
    #   playerID: the ID of the player making the move
    #   cardID: the ID of the card to play
    #   wildColor: (optional) the color a wild card should be set to (Red, Green, Blue, Yellow)
    # Returns: True if the action was legal and completed, False if illegal
    def playCard(self, playerID, cardID, wildColor=None):
        # Retrieve played card and top card of discard
        top = self.getTopCard(self.discard.id)
        played = self.getCard(id=cardID)

        if top.Card.card_type == 'Wild':
            # Assigned color for Wild card
            top_type = top.card_status
        else:
            top_type = top.Card.card_type

        # Moves are valid if they match value, type, or are wild
        if played.Card.card_type == 'Wild' \
                or top_type == played.Card.card_type \
                or top.card_value == played.card_value \
                or top_type == 'Any':

            player = self.getPlayer(user_id=playerID)

            self.addLog(player.User.username + " played " \
                    + played.Card.name + ".")

            # Move the card to the discard
            self.moveCard(played.id, self.discard.id)

            # Wild and Wild Draw 4
            if played.Card.card_type == 'Wild':
                self.wild(played, wildColor)

            # Skip
            elif played.card_value == 10:
                self.skip()

            # Draw Two
            elif played.card_value == 11:
                self.drawTwo()

            # Reverse
            elif played.card_value == 12:
                self.reverse(playerID)

            else:
                # Normal card
                self.endTurn()


            # If the player is out of cards in hand, the game is over
            playerHand = self.getPile(pile_type="Hand", pile_owner=playerID)
            if self.getPileCount(playerHand.id) == 0:
                winners = []
                losers = []

                for player in self.getPlayers():
                    if player.user_id == playerID:
                        winners.append(player.user_id)
                    else:
                        losers.append(player.user_id)

                self.gameOver(win=winners, loss=losers)


            return True

        return False


    # Skip card effect
    def skip(self):
        nextPlayer = self.getNextPlayer()
        self.addLog(nextPlayer.User.username + " turn was skipped.")

        self.endTurnMsg()
        self.incrementTurnsPlayed()

        self.setNextTurn()
        self.setNextTurn()


    # Draw Two card effect
    def drawTwo(self):
        nextPlayer = self.getNextPlayer()

        for i in range(0, 2):
            self.drawFromDeck(nextPlayer.user_id)

        self.addLog(nextPlayer.User.username + " drew two cards.")

        self.endTurn()


    # Reverse card effect
    def reverse(self, playerID):
        # reverse the turn orders
        playerList = []

        # Add every player other than the current player to a list, in turn order
        for i in range(0, self.game.num_players - 1):
            self.setNextTurn()

            playerList.append(self.getCurrentPlayerID())

        # Turns are reassigned, with current player assigned turn_order 1
        self.setTurnOrder(1)
        self.setPlayerTurn(playerID, 1)

        i = 2
        for id in reversed(playerList):
            self.setPlayerTurn(id, i)
            i += 1

        self.endTurn()


    # Wild card effect
    def wild(self, played, wildColor):
        # card_status contains the color the Wild card is currently set to
        self.updateCardInstance(played.id, card_status=wildColor)

        self.addLog("The " + played.Card.name + " was set to " + wildColor + ".")

        # If Draw 4
        if played.card_value == -2:
            nextPlayer = self.getNextPlayer()

            for i in range(0, 4):
                self.drawFromDeck(nextPlayer.user_id)

            self.addLog(nextPlayer.User.username + " drew four cards.")

        self.endTurn()


    # Retrieves any information needed to display this game
    # If a player ID is provided it will include the player's hand, otherwise
    #   the output will be suitable for a spectator (no hands shown)
    # Parameters:
    #   forPlayer: (optional)
    # Returns: the following object
    """
        {
            Deck ID: (int)
            Deck Count: (int)
            Discard ID: (int)
            Discard Count: (int)
            Discard Top: (CardInstance/Card object)
            Players: ([0]: Player (PlayersInGame/User object), [1]: Player Hand Count (int))
            Player Hand: [if forPlayer provided] (CardInstance/Card object)
        }
    """
    def getThisGame(self, forPlayer=None):
        game = {}

        game["Deck ID"] = self.deck.id
        game["Deck Count"] = self.getPileCount(self.deck.id)
        game["Discard ID"] = self.discard.id
        game["Discard Count"]= self.getPileCount(self.discard.id)
        game["Discard Top"] = self.getTopCard(self.discard.id)

        # NB: Could make this a single query using a join
        players = self.getPlayers()

        game["Players"] = []
        for player in players:
            hand = self.getPile(pile_type="Hand", pile_owner=player.user_id)

            newPlayer = (player, self.getPileCount(hand.id))
            game["Players"].append(newPlayer)

            if forPlayer and hand.pile_owner == forPlayer:
                game["Player Hand"] = self.getCards(pile=hand.id)

        return game
