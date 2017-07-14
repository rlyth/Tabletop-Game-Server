from flask import Blueprint, request, render_template, url_for, redirect

import gameDB.models as models

gameDB = Blueprint('gameDB', __name__, url_prefix='/gameDB')

import gameDB.GameFunctions as GameFunctions
@gameDB.route("/")
def index():
    return render_template("gameDB/sandbox.html",
                                games=models.Game.query.all(),
                                ginstance=models.GameInstance.query.all(),
                                pgame=models.PlayersInGame.query.order_by(models.PlayersInGame.game_instance).all(),
                                cards=models.Card.query.all(),
                                icard=models.CardInstance.query.all(),
                                gcard=models.CardsInGame.query.all(),
                                piles=models.Pile.query.all())


@gameDB.route("/initGI/", methods=['post'])
def initGI():
        if(request.form["bg"]):
            gid = request.form["bg"]
        else:
            gid = 1
        GameFunctions.initGameInstance(gid, [1, 2, 3, 4])
        return redirect(url_for('gameDB.index'))


@gameDB.route("/deleteGI/", methods=['post'])
def deleteGI():
        if(request.form["delete"]):
            GameFunctions.deleteGameInstance(request.form["delete"])
        return redirect(url_for('gameDB.index'))
