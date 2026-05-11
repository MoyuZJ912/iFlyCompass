from flask import render_template
from flask_login import login_required, current_user
from utils import get_settings
from . import ai_chat_bp

@ai_chat_bp.route('/board/ai-chat')
@login_required
def ai_chat():
    settings = get_settings()
    return render_template('ai_chat.html',
                         current_user=current_user,
                         sidebar_expanded=settings.get('sidebar_default_expanded', False))
