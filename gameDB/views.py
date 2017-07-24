from flask import Blueprint, request, render_template, url_for, redirect

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
            GF.initGameInstance(gid, [1, 2, 3, 4])

        if 'gid' in request.form:
            gid = request.form['gid']

            game = GF.gamePlay(gid)

            if 'randomizePlayers' in request.form:
                game.randomizePlayers()

            elif 'endTurn' in request.form:
                game.endTurn()

            elif 'deleteGI' in request.form:
                GF.deleteGameInstance(gid)

            elif 'setPlayerTurn' in request.form:
                if request.form['turn'] != '':
                    game.setPlayerTurn(request.form["setPlayerTurn"], request.form["turn"])

            elif 'fetchGI' in request.form:
                dumps = json.dumps(GF.fetchGameInstance(gid))

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
                                    dump=dumps)