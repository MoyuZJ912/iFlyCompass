import os
import re
from datetime import datetime, timezone
from flask import jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models.novel import NovelReadingProgress
from config import Config
from utils import read_novel_content, detect_file_encoding
from .parser import parse_chapters
from . import novel_bp

def get_novel_author(filename):
    match = re.search(r'_作者：([^.]+)\.txt$', filename)
    if match:
        return match.group(1)
    
    file_path = os.path.join(Config.NOVELS_DIR, filename)
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
        print(f"读取文件失败: {e}")
    
    return "未知作者"

def get_novel_latest_chapter(filename):
    file_path = os.path.join(Config.NOVELS_DIR, filename)
    try:
        content = read_novel_content(file_path)
        if content is None:
            return "未知章节"
        chapters = parse_chapters(content)
        if chapters:
            return chapters[-1]['name']
    except Exception as e:
        print(f"获取最新章节失败: {e}")
    return "未知章节"

def extract_novel_name(filename):
    name = filename[:-4]
    author_match = re.search(r'^(.*?)_作者：', name)
    if author_match:
        return author_match.group(1)
    return name

def find_novel_file_by_name(novel_name):
    if not os.path.exists(Config.NOVELS_DIR):
        return None
    
    for filename in os.listdir(Config.NOVELS_DIR):
        if filename.endswith('.txt'):
            extracted_name = extract_novel_name(filename)
            if extracted_name == novel_name:
                return os.path.join(Config.NOVELS_DIR, filename)
    return None

@novel_bp.route('/api/novels', methods=['GET'])
@login_required
def get_novels():
    try:
        novels = []
        if os.path.exists(Config.NOVELS_DIR):
            for filename in os.listdir(Config.NOVELS_DIR):
                if filename.endswith('.txt'):
                    novel_name = extract_novel_name(filename)
                    author = get_novel_author(filename)
                    latest_chapter = get_novel_latest_chapter(filename)
                    
                    progress = NovelReadingProgress.query.filter_by(
                        user_id=current_user.id,
                        novel_filename=filename
                    ).first()
                    
                    last_read_chapter = None
                    if progress:
                        file_path = os.path.join(Config.NOVELS_DIR, filename)
                        content = read_novel_content(file_path)
                        if content:
                            chapters = parse_chapters(content)
                            if progress.last_chapter_index < len(chapters):
                                last_read_chapter = chapters[progress.last_chapter_index]['name']
                    
                    novels.append({
                        'name': novel_name,
                        'filename': filename,
                        'author': author,
                        'latest_chapter': latest_chapter,
                        'last_read_chapter': last_read_chapter
                    })
        return jsonify({
            'success': True,
            'novels': novels
        })
    except Exception as e:
        print(f"获取小说列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@novel_bp.route('/api/novels/<novel_name>/chapters', methods=['GET'])
@login_required
def get_novel_chapters(novel_name):
    try:
        file_path = find_novel_file_by_name(novel_name)
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': '小说不存在'
            }), 404
        
        content = read_novel_content(file_path)
        if content is None:
            return jsonify({
                'success': False,
                'error': '读取小说内容失败'
            }), 500
        
        chapters = parse_chapters(content)
        
        chapter_list = [{'index': i, 'name': ch['name']} for i, ch in enumerate(chapters)]
        
        return jsonify({
            'success': True,
            'chapters': chapter_list
        })
    except Exception as e:
        print(f"获取章节列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@novel_bp.route('/api/novels/<novel_name>/chapters/<int:chapter_index>', methods=['GET'])
@login_required
def get_chapter_content(novel_name, chapter_index):
    try:
        file_path = find_novel_file_by_name(novel_name)
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': '小说不存在'
            }), 404
        
        content = read_novel_content(file_path)
        if content is None:
            return jsonify({
                'success': False,
                'error': '读取小说内容失败'
            }), 500
        
        chapters = parse_chapters(content)
        
        if chapter_index < 0 or chapter_index >= len(chapters):
            return jsonify({
                'success': False,
                'error': '章节不存在'
            }), 404
        
        chapter = chapters[chapter_index]
        
        return jsonify({
            'success': True,
            'chapter_name': chapter['name'],
            'content': chapter['content'],
            'chapter_index': chapter_index,
            'total_chapters': len(chapters)
        })
    except Exception as e:
        print(f"获取章节内容失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@novel_bp.route('/api/novels/<novel_name>/progress', methods=['POST'])
@login_required
def save_reading_progress(novel_name):
    try:
        file_path = find_novel_file_by_name(novel_name)
        if not file_path:
            return jsonify({
                'success': False,
                'error': '小说不存在'
            }), 404
        
        chapter_index = request.json.get('chapter_index', 0)
        
        progress = NovelReadingProgress.query.filter_by(
            user_id=current_user.id,
            novel_filename=os.path.basename(file_path)
        ).first()
        
        if progress:
            progress.last_chapter_index = chapter_index
            progress.last_read_at = datetime.now(timezone.utc)
        else:
            progress = NovelReadingProgress(
                user_id=current_user.id,
                novel_filename=os.path.basename(file_path),
                last_chapter_index=chapter_index,
                last_read_at=datetime.now(timezone.utc)
            )
            db.session.add(progress)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '阅读进度保存成功'
        })
    except Exception as e:
        print(f"保存阅读进度失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@novel_bp.route('/api/novels/<novel_name>/progress', methods=['GET'])
@login_required
def get_reading_progress(novel_name):
    try:
        file_path = find_novel_file_by_name(novel_name)
        if not file_path:
            return jsonify({
                'success': False,
                'error': '小说不存在'
            }), 404
        
        progress = NovelReadingProgress.query.filter_by(
            user_id=current_user.id,
            novel_filename=os.path.basename(file_path)
        ).first()
        
        if progress:
            return jsonify({
                'success': True,
                'last_chapter_index': progress.last_chapter_index,
                'last_read_at': progress.last_read_at.isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'last_chapter_index': 0,
                'last_read_at': None
            })
    except Exception as e:
        print(f"获取阅读进度失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
