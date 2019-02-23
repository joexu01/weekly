from flask import Blueprint

wk = Blueprint('wk', __name__)

from . import views
