import re

CHAPTER_PATTERNS = [
    r'^第\s*[0-9]+\s*章',
    r'^第[一二三四五六七八九十百千]+章',
    r'^[0-9]+\.',
    r'^Chapter\s+[0-9]+',
    r'^CHAPTER\s+[0-9]+',
    r'^第\s*[0-9]+\s*章.*$',
]

def parse_chapters(content):
    chapters = []
    lines = content.split('\n')
    
    chapter_patterns = [re.compile(pattern) for pattern in CHAPTER_PATTERNS]
    
    start_line = 0
    for i in range(min(20, len(lines))):
        if lines[i].strip() == '正文':
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    start_line = j
                    break
            break
    
    current_chapter = None
    current_content = []
    
    for i in range(start_line, len(lines)):
        line = lines[i]
        line_stripped = line.strip()
        
        is_chapter_title = False
        for pattern in chapter_patterns:
            if pattern.match(line_stripped):
                is_chapter_title = True
                break
        
        if is_chapter_title:
            is_new_chapter = False
            if i == start_line:
                is_new_chapter = True
            elif i > 0 and lines[i-1].strip() == '':
                is_new_chapter = True
            
            if not is_new_chapter:
                is_new_chapter = True
            
            if is_new_chapter:
                if current_chapter is not None:
                    chapters.append({
                        'name': current_chapter,
                        'content': '\n'.join(current_content).strip()
                    })
                
                current_chapter = line_stripped
                current_content = []
        else:
            if current_chapter is not None:
                current_content.append(line)
    
    if current_chapter is not None:
        chapters.append({
            'name': current_chapter,
            'content': '\n'.join(current_content).strip()
        })
    
    if not chapters and content.strip():
        chapters.append({
            'name': '正文',
            'content': content.strip()
        })
    
    return chapters
