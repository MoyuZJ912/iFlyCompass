import os
import re
import threading
from config import Config
from utils.file import detect_file_encoding
from utils.chapter_parser import detect_chapters_from_lines

_novel_cache = {}
_cache_lock = threading.Lock()
_cache_initialized = False

def extract_novel_name(filename):
    name = filename[:-4]
    author_match = re.search(r'^(.*?)_作者：', name)
    if author_match:
        return author_match.group(1)
    return name

def get_novel_author_from_file(file_path, filename):
    match = re.search(r'_作者：([^.]+)\.txt$', filename)
    if match:
        return match.group(1)
    
    try:
        encoding = detect_file_encoding(file_path)
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            for i in range(10):
                line = f.readline()
                if not line:
                    break
                author_match = re.search(r'作者：(.+)', line)
                if author_match:
                    return author_match.group(1).strip()
    except Exception as e:
        print(f"读取作者失败 {filename}: {e}")
    
    return "未知作者"

def get_novel_latest_chapter_from_file(file_path):
    try:
        encoding = detect_file_encoding(file_path)
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        chapters = detect_chapters_from_lines(lines)
        
        if chapters:
            return chapters[-1]['title']
    except Exception as e:
        print(f"获取最新章节失败 {file_path}: {e}")
    return "未知章节"

def scan_novel(filename):
    file_path = os.path.join(Config.NOVELS_DIR, filename)
    
    if not os.path.exists(file_path):
        return None
    
    try:
        novel_name = extract_novel_name(filename)
        author = get_novel_author_from_file(file_path, filename)
        latest_chapter = get_novel_latest_chapter_from_file(file_path)
        
        return {
            'name': novel_name,
            'filename': filename,
            'author': author,
            'latest_chapter': latest_chapter,
            'file_path': file_path
        }
    except Exception as e:
        print(f"扫描小说失败 {filename}: {e}")
        return None

def init_novel_cache():
    global _novel_cache, _cache_initialized
    
    print("开始扫描小说目录...")
    
    new_cache = {}
    scanned_count = 0
    
    if os.path.exists(Config.NOVELS_DIR):
        for filename in os.listdir(Config.NOVELS_DIR):
            if filename.endswith('.txt'):
                novel_info = scan_novel(filename)
                if novel_info:
                    new_cache[filename] = novel_info
                    scanned_count += 1
                    print(f"  已扫描: {novel_info['name']} - {novel_info['author']} (最新: {novel_info['latest_chapter'][:20]}...)")
    
    with _cache_lock:
        _novel_cache = new_cache
        _cache_initialized = True
    
    print(f"小说缓存初始化完成，共扫描 {scanned_count} 本小说")
    return scanned_count

def get_novel_cache():
    with _cache_lock:
        return _novel_cache.copy()

def get_novel_info(filename):
    with _cache_lock:
        return _novel_cache.get(filename)

def get_all_novels():
    with _cache_lock:
        return list(_novel_cache.values())

def refresh_novel_cache():
    return init_novel_cache()

def is_cache_initialized():
    return _cache_initialized
