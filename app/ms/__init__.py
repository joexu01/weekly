from flask import Blueprint

ms = Blueprint('ms', __name__)

from . import views
