from flask import Blueprint, request, render_template
from sqlalchemy.orm.exc import NoResultFound

userDB = Blueprint('userDB', __name__, url_prefix='/user')