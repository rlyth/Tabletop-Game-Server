from flask import Blueprint, request, render_template
import json

uno = Blueprint('uno', __name__, url_prefix='/uno')

from gameDB.GameFunctions import fetchGameInstance
from .uno import Uno

@uno.route("/", methods=['GET', 'POST'])
def index():
    return render_template("uno/sandbox.html", dump="hihi")

@uno.route("/<int:instanceID>/", methods=['GET', 'POST'])
def instance(instanceID):
    if request.method == 'GET':
        dump = ''

        gameInfo = fetchGameInstance(instanceID)

        # Invalid instanceID error message
        if not gameInfo:
            dump = "Game Instance not found."
            return render_template("uno/sandbox.html", dump=dump)

        dump = json.dumps(gameInfo)

        newUno = Uno(instanceID)


        logs = gameInfo["Log"]
        players = gameInfo["Players"]

        if gameInfo:
            return render_template("uno/sandbox.html",
                                        dump=dump,
                                        logs=logs,
                                        players=players
                                    )
