from flask import Blueprint, request, render_template, g, session

import gameDB.models as models
import json

gameDB = Blueprint('gameDB', __name__, url_prefix='/game')

import gameDB.GameFunctions as GF
from .models import Game, GameInstance
from .GameFunctions import getGameInstance, gamePlay
from .forms import createGame

from userDB import User

# games
from uno.uno import Uno

@gameDB.before_request
def before_request():
    try:
        g.username = session['username']
        g.userid = session['userid']
    except:
        g.username = None
        g.userid = None

@gameDB.route("/<int:gameID>/", methods=['GET'])
def gameHome():
    # page showing game info, rules, and statistics
    return

@gameDB.route("/new", methods=['GET', 'POST'])
def newGame():
    form = createGame()

    games = Game.query.all()

    form.game.choices = [(game.id, game.name) for game in games]

    players = [(user.id, user.username) for user in User.query.filter(User.id != g.userid).all()]


    return render_template('game/create.html', form=form, games=games, players=players)

    """
    users = User.query.filter(User.username != passedUserName).all()
    existingUser = User.query.filter_by(username=passedUserName).first()
    newGameForm = gameForm()

    newGameForm.player2.choices = [(u.id, u.username) for u in User.query.filter(User.username != passedUserName)]
    newGameForm.player3.choices = [(u.id, u.username) for u in User.query.filter(User.username != passedUserName)]
    newGameForm.player4.choices = [(u.id, u.username) for u in User.query.filter(User.username != passedUserName)]

    newGameForm.player2.choices.insert(0, ('0', 'Select'))
    newGameForm.player3.choices.insert(0, ('0', 'Select'))
    newGameForm.player4.choices.insert(0, ('0', 'Select'))

    if request.method == 'POST':
        gameName = newGameForm.game.data
        #THIS IS WHERE WE KEEP TRACK OF WHICH GAME IS STARTING MODIFY FOR FUTURE GAMES
        baseGameID = 2
        if gameName == 'uno':
            baseGameID = 2
        gamePlayers = newGameForm.numberOfPlayers.data
        playerNum2 = newGameForm.player2.data
        playerNum3 = newGameForm.player3.data
        playerNum4 = newGameForm.player4.data
        if gamePlayers == '03':
            if playerNum2 == 0 or playerNum3 == 0 or playerNum2 == playerNum3:
                return render_template('error.html')
            else:
                inviteList = [playerNum2, playerNum3]
                GameFunctions.initGameInstance(baseGameID, existingUser.id, inviteList)
                return redirect(url_for('login'))

        if gamePlayers == '04':
            if playerNum2 == 0 or playerNum3 == 0 or playerNum4 == 0 or playerNum2 == playerNum3 or playerNum2 == playerNum4 or playerNum4 == playerNum3:
                return render_template('error.html')
            else:
                inviteList = [playerNum2, playerNum3, playerNum4]
                GameFunctions.initGameInstance(baseGameID, existingUser.id, inviteList)
                return redirect(url_for('login'))
        else:
            if playerNum2 == 0:
                return render_template('error.html')
            else:
                inviteList = [playerNum2]
                GameFunctions.initGameInstance(baseGameID, existingUser.id, inviteList)
                return redirect(url_for('login'))

    return render_template('newgame.html', passedUserName=passedUserName, users=users, newGameForm=newGameForm)
    """



@gameDB.route("/play/<int:instanceID>/", methods=['GET', 'POST'])
def play(instanceID):

    thisGame = getGameInstance(instanceID)

    if not thisGame:
        return render_template('error.html', error_msg="That game does not exist.")



    # Create game-specific object and use it to retrieve game information
    if thisGame.Game.name == 'Uno':
        game = Uno(instanceID)

        game_template = 'uno/play_uno.html'

    logs = None
    active = False

    if game:
        logs = game.getLogs()

        if g.userid == game.getCurrentPlayerID():
                active = True

    return render_template(game_template,
                                game=game.getThisGame(g.userid),
                                logs=logs,
                                active=active,
                                current_user=g.username,
                                game_type=thisGame.Game.name,
                                game_instance=thisGame.id)



    # determine what game it is

    # separate game logic for each game out into its own module.. somehow






@gameDB.route("/sandbox", methods=['GET', 'POST'])
def sandbox():
    # Admins only
    try:
        current_user = User.query.filter_by(id=g.userid).first()
        # NB: not working as intended
        if current_user.role != 'Admin':
            render_template('error.html', error_msg="You do not have permission to view this page.")
    except:
        render_template('error.html', error_msg="You must be logged in to view this page.")

    dumps = ''

    if request.method == 'POST':
        if 'initGI' in request.form:
            if(request.form["bg"]):
                gid = request.form["bg"]
            else:
                gid = 1
            GF.initGameInstance(gid, 1, [2, 3, 4])
            # auto-accept all invites for testing purposes

        if 'gid' in request.form:
            gid = request.form['gid']

            game = GF.gamePlay(gid)

            if 'randomizePlayers' in request.form:
                game.randomizePlayers()

            elif 'endTurn' in request.form:
                game.endTurn()

            elif 'deleteGI' in request.form:
                if gid == '1':
                    dumps = 'Not deleting that GameInstance. Please try another.'
                else:
                    GF.deleteGameInstance(gid)

            elif 'setPlayerTurn' in request.form:
                if request.form['turn'] != '':
                    game.setPlayerTurn(request.form["uid"], request.form["turn"])

            elif 'acceptInvite' in request.form:
                game.acceptInvite(request.form["uid"])

            elif 'declineInvite' in request.form:
                game.declineInvite(request.form["uid"])

            elif 'acceptAll' in request.form:
                players = game.getPlayers()

                for p in players:
                    game.acceptInvite(p.user_id)

            elif 'fetchGI' in request.form:
                dumps = json.dumps(GF.fetchGameInstance(gid))

            elif 'currentPlayerID' in request.form:
                dumps = game.getCurrentPlayerID()

        if 'pid' in request.form:
            pid = request.form['pid']

            game = GF.gamePlay(models.Pile.query.filter_by(
                    id=pid
                    ).one().game_instance)

            if 'shufflePile' in request.form:
                game.shufflePile(pid)

            elif 'drawTopCard' in request.form:
                if pid == '1':
                    toPile = 2
                else:
                    toPile = 1

                if not game.drawTopCard(pid, toPile):
                    dumps = 'Empty Pile'

        if 'cid' in request.form:
            cid = request.form['cid']

            game = GF.gamePlay(models.CardInstance.query.filter_by(
                    id=cid
                    ).one().game_instance)


            if 'moveCard' in request.form:
                card = models.CardInstance.query.filter_by(
                        id=cid
                        ).one()
                if card.in_pile == 1:
                    game.moveCard(cid, 2)
                elif card.in_pile == 2:
                    game.moveCard(cid, 1)
                else:
                    game.moveCard(cid, 1)

            if 'updateCard' in request.form:
                val = None
                stat = None

                if request.form['value'] is not '':
                    val = request.form['value']
                if request.form['status'] is not '':
                    stat = request.form['status']

                game.updateCardInstance(cid, card_value=val, card_status=stat)

        if 'uid' in request.form:
            uid = request.form['uid']

            if 'getPlayerGames' in request.form:
                dumps = GF.getPlayerGames(uid)

    return render_template("game/sandbox.html",
                                    games=models.Game.query.all(),

                                    ginstance=models.GameInstance.query.all(),

                                    pgame=models.PlayersInGame.query.order_by(
                                        models.PlayersInGame.game_instance,
                                        models.PlayersInGame.turn_order
                                        ).all(),

                                    cards=models.Card.query.all(),

                                    icard=models.CardInstance.query.order_by(
                                            models.CardInstance.in_pile,
                                            models.CardInstance.pile_order
                                        ).all(),

                                    gcard=models.CardsInGame.query.all(),

                                    piles=models.Pile.query.all(),

                                    log=models.GameLog.query \
                                                .order_by(
                                                    models.GameLog.game_instance,
                                                    models.GameLog.timestamp.desc()
                                                    ) \
                                                .all(),
                                    dump=dumps)