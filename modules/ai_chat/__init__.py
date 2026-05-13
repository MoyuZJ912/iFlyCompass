from flask import Blueprint

ai_chat_bp = Blueprint('ai_chat', __name__)

from . import routes, api
