from flask import render_template, send_from_directory
from flask_login import login_required, current_user
from utils import get_bing_wallpaper, get_poetry
from config import Config
from . import main_bp

@main_bp.route('/')
def index():
    wallpaper_url = get_bing_wallpaper()
    poetry = get_poetry()
    return render_template('index.html', wallpaper_url=wallpaper_url, poetry=poetry)

@main_bp.route('/board')
@login_required
def board():
    return render_template('board.html', 
                         username=current_user.username, 
                         passkey_used=current_user.passkey_used,
                         is_admin=current_user.is_admin, 
                         is_super_admin=current_user.is_super_admin)

@main_bp.route('/board/tools')
@login_required
def tools():
    return render_template('tools.html', 
                         username=current_user.username, 
                         passkey_used=current_user.passkey_used,
                         is_admin=current_user.is_admin, 
                         is_super_admin=current_user.is_super_admin)

@main_bp.route('/temp/<path:filename>')
def serve_temp(filename):
    return send_from_directory(Config.TEMP_DIR, filename)

@main_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(Config.ASSETS_DIR, filename)
