from flask import Blueprint, request, render_template, flash

uno = Blueprint('uno', __name__, url_prefix='/uno')

from gameDB.GameFunctions import instanceInfo
from .uno import Uno

@uno.route("/", methods=['GET', 'POST'])
def index():
    #
    return render_template("uno/sandbox.html", dump="this page doesn't do anything")

@uno.route("/<int:instanceID>/", methods=['GET', 'POST'])
def instance(instanceID):
    # the actual user-facing page should go here
    return

# for testing only
@uno.route("/<int:instanceID>/sandbox/", methods=['GET', 'POST'])
def sandbox(instanceID):
    dump = ''

    # I'll write a query that only retrieves the GameInstance/Game soon
    gameInfo = instanceInfo(instanceID)

    # Invalid instanceID
    if not gameInfo:
        dump = "Game Instance not found."
        return render_template("uno/sandbox.html", dump=dump)

    # GameInstance is not Uno
    if gameInfo.Game.name != 'Uno':
        dump = "Incorrect game type."
        return render_template("uno/sandbox.html", dump=dump)

    game = Uno(instanceID)

    # temporary hack, replace with current logged in user id
    active_player = game.getCurrentPlayerID()

    # Check whether user id of user viewing page matches current turn order,
    #   also maybe check whether they are in the game to handle spectators

    if request.method == 'POST':
        if 'drawCard' in request.form:
            game.draw(active_player)

        elif 'playCard' in request.form:
            wc = None

            # Wild card was played, get color
            if 'wildColor' in request.form:
                wc = request.form["wildColor"]

            # playCard returned false; move is illegal
            if not game.playCard(active_player, request.form["cid"], wildColor=wc):
                flash('Can\'t play that card')

        # for testing
        elif 'endTurn' in request.form:
            game.endTurn()

        # for testing
        elif 'endGame' in request.form:
            game.gameOver(win=[1], loss=[2,3], draw=[4])

        # for testing
        elif 'resetGame' in request.form:
            game.resetGame()

    # temporary hack, remove it later
    active_player = game.getCurrentPlayerID()

    # instead of separating everything out into different variables,
    #   probably can just pass the template this variable and extract everything
    #   from there
    g = game.getThisGame(active_player)

    discard = g["Discard Top"]

    players = g["Players"]

    hand = g["Player Hand"]

    deck_count = g["Deck Count"]
    discard_count = g["Discard Count"]

    logs = game.getLogs()

    return render_template("uno/sandbox.html",
                                dump=dump,
                                logs=logs,
                                players=players,
                                discard=discard,
                                deck=True,
                                deck_count=deck_count,
                                discard_count=discard_count,
                                hand=hand,
                                gid=instanceID,
                                active=active_player,
                                endgame=True
                            )
