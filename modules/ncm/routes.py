from flask import render_template
from . import ncm_bp

@ncm_bp.route('/ncmplayer')
def ncm_player():
    return render_template('ncm_player.html')
