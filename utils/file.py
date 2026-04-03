import os
import chardet
import requests
from config import Config

def detect_file_encoding(file_path):
    try:
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'rb') as f:
            raw_data = f.read(min(100 * 1024, file_size))
        
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'
        return encoding
    except Exception as e:
        print(f"检测编码失败: {e}")
        return 'utf-8'

def read_novel_content(file_path):
    encoding = detect_file_encoding(file_path)
    
    try:
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        return content
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None

def download_sticker_image(url, code, sticker_type):
    try:
        if url.startswith('/'):
            url = f'http://45.207.204.145:5003{url}'
        
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"下载图片失败: {url}, 状态码: {response.status_code}")
            return None
        
        content_type = response.headers.get('content-type', '')
        if 'png' in content_type:
            ext = 'png'
        elif 'jpg' in content_type or 'jpeg' in content_type:
            ext = 'jpg'
        elif 'gif' in content_type:
            ext = 'gif'
        else:
            ext = 'png'
        
        filename = f"{sticker_type}_{code}.{ext}"
        filepath = os.path.join(Config.STICKERS_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return f'/stickers/{filename}'
    except Exception as e:
        print(f"下载表情图片失败: {e}")
        return None
