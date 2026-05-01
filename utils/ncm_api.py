import requests

NCM_API_BASE = 'http://wjysrv.moyuzj.cn:29996'


class NCMAPIClient:
    def __init__(self, base_url=NCM_API_BASE, timeout=10):
        self.base_url = base_url
        self.timeout = timeout

    def request(self, endpoint, params=None):
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"[NCM API] 请求: {url}, 参数: {params}")
            response = requests.get(url, params=params, timeout=self.timeout)
            print(f"[NCM API] 响应状态码: {response.status_code}")
            return response.json()
        except requests.exceptions.Timeout:
            print(f"[NCM API] 请求超时: {endpoint}")
            return {'code': 408, 'error': '请求超时'}
        except requests.exceptions.RequestException as e:
            print(f"[NCM API] 请求失败: {endpoint}, 错误: {e}")
            return {'code': 500, 'error': str(e)}
        except Exception as e:
            print(f"[NCM API] 未知错误: {endpoint}, 错误: {e}")
            return {'code': 500, 'error': str(e)}

    def search(self, keywords, limit=30, offset=0, search_type=1):
        return self.request('/search', {
            'keywords': keywords,
            'limit': limit,
            'offset': offset,
            'type': search_type
        })

    def get_song_url(self, song_id):
        return self.request('/song/url', {'id': song_id})

    def get_song_detail(self, song_ids):
        if isinstance(song_ids, list):
            song_ids = ','.join(map(str, song_ids))
        return self.request('/song/detail', {'ids': song_ids})

    def get_lyric(self, song_id):
        return self.request('/lyric', {'id': song_id})

    def get_personalized(self, limit=30):
        return self.request('/personalized', {'limit': limit})

    def get_personalized_newsong(self, limit=10):
        return self.request('/personalized/newsong', {'limit': limit})

    def get_playlist_detail(self, playlist_id):
        return self.request('/playlist/detail', {'id': playlist_id})

    def get_hot_search(self):
        return self.request('/search/hot/detail')


ncm_client = NCMAPIClient()
