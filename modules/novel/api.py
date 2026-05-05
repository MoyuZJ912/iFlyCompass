import os
from flask import jsonify, send_file
from flask_login import login_required
from config import Config
from utils import get_all_novels, get_novel_info, refresh_novel_cache
from utils.novel_cache import init_novel_cache
from utils.file import detect_file_encoding
from . import novel_bp


def _find_novel(novel_name):
    """Find novel by name, returning cache info dict or None."""
    novels = get_all_novels()
    for novel in novels:
        if novel['name'] == novel_name:
            return novel
    # Try URL-decoded name as fallback
    import urllib.parse
    decoded = urllib.parse.unquote(novel_name)
    if decoded != novel_name:
        for novel in novels:
            if novel['name'] == decoded:
                return novel
    return None


def _get_file_path(novel_info):
    """Resolve file path from novel info dict."""
    if not novel_info:
        return None
    path = novel_info.get('file_path')
    if path and os.path.exists(path):
        return path
    path = os.path.join(Config.NOVELS_DIR, novel_info['filename'])
    return path if os.path.exists(path) else None


@novel_bp.route('/api/novels', methods=['GET'])
@login_required
def get_novels():
    try:
        init_novel_cache()
        novels = get_all_novels()
        result = [{
            'name': n['name'],
            'filename': n['filename'],
            'author': n['author'],
            'latest_chapter': n['latest_chapter']
        } for n in novels]

        return jsonify({'success': True, 'novels': result})
    except Exception as e:
        print(f"获取小说列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@novel_bp.route('/api/novels/refresh-cache', methods=['POST'])
@login_required
def refresh_cache():
    try:
        count = refresh_novel_cache()
        return jsonify({'success': True, 'message': f'缓存刷新成功，共扫描 {count} 本小说'})
    except Exception as e:
        print(f"刷新缓存失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@novel_bp.route('/api/novels/<path:novel_name>/info', methods=['GET'])
@login_required
def get_novel_info_api(novel_name):
    try:
        info = _find_novel(novel_name)
        file_path = _get_file_path(info)
        if not file_path:
            return jsonify({'success': False, 'error': '小说不存在'}), 404

        stat = os.stat(file_path)
        encoding = detect_file_encoding(file_path)

        return jsonify({
            'success': True,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'filename': info['filename'],
            'encoding': encoding or 'utf-8'
        })
    except Exception as e:
        print(f"获取小说信息失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@novel_bp.route('/api/novels/<path:novel_name>/file', methods=['GET'])
@login_required
def download_novel_file(novel_name):
    try:
        info = _find_novel(novel_name)
        file_path = _get_file_path(info)
        if not file_path:
            return jsonify({'success': False, 'error': '小说不存在'}), 404

        return send_file(
            file_path,
            mimetype='application/octet-stream',
            as_attachment=False,
            conditional=True
        )
    except Exception as e:
        print(f"下载小说文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
