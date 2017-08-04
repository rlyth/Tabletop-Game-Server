from gameDB.GameFunctions import gamePlay

# Uno extends gamePlay
class Uno(gamePlay):
    # This will only be called once, and enacts Uno-specific set-up
    def initialSetup(self):
        # Assign values to all cards
        # this really should be delegated to initGameInstance()

        # Randomize turn order
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
        cards = self.getCards()
        for c in cards:
            self.moveCard(c.id, deck)

        # Shuffle deck
        self.shufflePile(deck)

        # NB: dealCards might be behaving improperly, investigate further
        # Deal 7 cards to each player hand
        self.dealCards(deck, hands, 7)

        # Draw first card and place on discard
        self.drawTopCard(deck, discard)

        return