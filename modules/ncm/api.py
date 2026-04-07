from flask import jsonify, request, send_file
from . import ncm_bp
from utils.music_cache import get_cached_music, cache_music

NCM_API_BASE = 'http://wjysrv.moyuzj.cn:29996'

def ncm_api_request(endpoint, params=None):
    try:
        import requests
        url = f"{NCM_API_BASE}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"NCM API请求失败: {endpoint}, {e}")
        return {'code': 500, 'error': str(e)}

@ncm_bp.route('/api/ncm/search', methods=['GET'])
def api_search():
    keywords = request.args.get('keywords', '')
    limit = request.args.get('limit', 30, type=int)
    offset = request.args.get('offset', 0, type=int)
    search_type = request.args.get('type', 1, type=int)
    
    result = ncm_api_request('/search', {
        'keywords': keywords,
        'limit': limit,
        'offset': offset,
        'type': search_type
    })
    return jsonify(result)

@ncm_bp.route('/api/ncm/song/url', methods=['GET'])
def api_song_url():
    song_id = request.args.get('id', '')
    result = ncm_api_request('/song/url', {'id': song_id})
    return jsonify(result)

@ncm_bp.route('/api/ncm/song/detail', methods=['GET'])
def api_song_detail():
    ids = request.args.get('ids', '')
    result = ncm_api_request('/song/detail', {'ids': ids})
    return jsonify(result)

@ncm_bp.route('/api/ncm/personalized', methods=['GET'])
def api_personalized():
    limit = request.args.get('limit', 30, type=int)
    result = ncm_api_request('/personalized', {'limit': limit})
    return jsonify(result)

@ncm_bp.route('/api/ncm/lyric', methods=['GET'])
def api_lyric():
    song_id = request.args.get('id', '')
    result = ncm_api_request('/lyric', {'id': song_id})
    return jsonify(result)

@ncm_bp.route('/api/ncm/playlist/detail', methods=['GET'])
def api_playlist_detail():
    playlist_id = request.args.get('id', '')
    result = ncm_api_request('/playlist/detail', {'id': playlist_id})
    return jsonify(result)

@ncm_bp.route('/api/ncm/hot-search', methods=['GET'])
def api_hot_search():
    result = ncm_api_request('/search/hot/detail')
    return jsonify(result)

@ncm_bp.route('/api/ncm/cache-music', methods=['POST'])
def api_cache_music():
    data = request.get_json()
    song_id = data.get('id')
    song_url = data.get('url')
    song_name = data.get('name', 'unknown')
    
    if not song_id or not song_url:
        return jsonify({'success': False, 'error': '缺少参数'})
    
    cached_path = cache_music(song_id, song_url, song_name)
    if cached_path:
        return jsonify({'success': True, 'path': cached_path})
    else:
        return jsonify({'success': False, 'error': '缓存失败'})

@ncm_bp.route('/api/ncm/cached-music/<int:song_id>', methods=['GET'])
def api_get_cached_music(song_id):
    cached_path = get_cached_music(song_id)
    if cached_path:
        return jsonify({'success': True, 'path': cached_path})
    else:
        return jsonify({'success': False, 'error': '未缓存'})

@ncm_bp.route('/music/<filename>', methods=['GET'])
def serve_music(filename):
    music_dir = 'temp/music'
    return send_file(f'{music_dir}/{filename}')
