import os
import re
from datetime import datetime, timezone
from flask import jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models.novel import NovelReadingProgress
from config import Config
from utils import read_novel_content, get_all_novels, get_novel_info, refresh_novel_cache
from utils.novel_cache import is_cache_initialized, init_novel_cache
from .parser import parse_chapters
from . import novel_bp

def find_novel_file_by_name(novel_name):
    novels = get_all_novels()
    for novel in novels:
        if novel['name'] == novel_name:
            return novel.get('file_path') or os.path.join(Config.NOVELS_DIR, novel['filename'])
    return None

@novel_bp.route('/api/novels', methods=['GET'])
@login_required
def get_novels():
    try:
        if not is_cache_initialized():
            init_novel_cache()
        novels = get_all_novels()
        
        result = []
        for novel in novels:
            progress = NovelReadingProgress.query.filter_by(
                user_id=current_user.id,
                novel_filename=novel['filename']
            ).first()
            
            last_read_chapter = None
            if progress:
                file_path = os.path.join(Config.NOVELS_DIR, novel['filename'])
                content = read_novel_content(file_path)
                if content:
                    chapters = parse_chapters(content)
                    if progress.last_chapter_index < len(chapters):
                        last_read_chapter = chapters[progress.last_chapter_index]['name']
            
            result.append({
                'name': novel['name'],
                'filename': novel['filename'],
                'author': novel['author'],
                'latest_chapter': novel['latest_chapter'],
                'last_read_chapter': last_read_chapter
            })
        
        return jsonify({
            'success': True,
            'novels': result
        })
    except Exception as e:
        print(f"获取小说列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@novel_bp.route('/api/novels/refresh-cache', methods=['POST'])
@login_required
def refresh_cache():
    try:
        count = refresh_novel_cache()
        return jsonify({
            'success': True,
            'message': f'缓存刷新成功，共扫描 {count} 本小说'
        })
    except Exception as e:
        print(f"刷新缓存失败: {e}")
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

@novel_bp.route('/api/novels/<novel_name>/download-all')
@login_required
def download_all_chapters(novel_name):
    """一次性返回所有章节内容，供客户端整本书缓存"""
    try:
        file_path = find_novel_file_by_name(novel_name)
        if not file_path:
            return jsonify({'success': False, 'error': '小说不存在'}), 404

        content = read_novel_content(file_path)
        if content is None:
            return jsonify({'success': False, 'error': '读取小说内容失败'}), 500

        chapters = parse_chapters(content)
        all_chapters = [
            {'index': i, 'name': ch['name'], 'content': ch['content']}
            for i, ch in enumerate(chapters)
        ]

        return jsonify({
            'success': True,
            'novel_name': novel_name,
            'total_chapters': len(all_chapters),
            'chapters': all_chapters
        })
    except Exception as e:
        print(f"下载全部章节失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
