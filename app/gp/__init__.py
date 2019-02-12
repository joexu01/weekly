from flask import Blueprint

gp = Blueprint('gp', __name__)

from . import views
