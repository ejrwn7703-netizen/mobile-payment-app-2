from flask import Blueprint

bp = Blueprint('api', __name__)

from .api import *
from .payments import *