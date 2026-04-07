import requests

NCM_API_BASE = 'http://wjysrv.moyuzj.cn:29996'

def ncm_api_request(endpoint, params=None):
    try:
        url = f"{NCM_API_BASE}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"NCM API请求失败: {endpoint}, {e}")
        return {'code': 500, 'error': str(e)}

def ncm_search(keywords, limit=30, offset=0, search_type=1):
    try:
        url = f"{NCM_API_BASE}/search"
        params = {
            'keywords': keywords,
            'limit': limit,
            'offset': offset,
            'type': search_type
        }
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"搜索失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_song_url(song_id):
    try:
        url = f"{NCM_API_BASE}/song/url"
        params = {'id': song_id}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取歌曲URL失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_song_detail(song_ids):
    try:
        url = f"{NCM_API_BASE}/song/detail"
        params = {'ids': song_ids}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取歌曲详情失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_lyric(song_id):
    try:
        url = f"{NCM_API_BASE}/lyric"
        params = {'id': song_id}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取歌词失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_personalized(limit=30):
    try:
        url = f"{NCM_API_BASE}/personalized"
        params = {'limit': limit}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取推荐歌单失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_playlist_detail(playlist_id):
    try:
        url = f"{NCM_API_BASE}/playlist/detail"
        params = {'id': playlist_id}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取歌单详情失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_hot_search():
    try:
        url = f"{NCM_API_BASE}/search/hot/detail"
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取热搜失败: {e}")
        return {'code': 500, 'error': str(e)}
