from flask import Blueprint, request, render_template

import gameDB.models as models
import json

gameDB = Blueprint('gameDB', __name__, url_prefix='/gameDB')

import gameDB.GameFunctions as GF
@gameDB.route("/", methods=['GET', 'POST'])
def index():
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

    return render_template("gameDB/sandbox.html",
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