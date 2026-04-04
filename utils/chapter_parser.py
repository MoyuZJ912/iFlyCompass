# -*- coding: utf-8 -*-
"""
章节检测 V3.1 — 锚点学习 + 统计验证

V3.1 修复（相对于 V3）：
1. find_content_start 完全重写：emoji/URL检测 + 首个章节标题定位
2. looks_like_prose 移除 len<8 短路，大幅增强散文检测信号
3. Phase3 无前缀模式时强制要求前空行
4. Phase4 置信度底线提高

用法:
    from utils.chapter_parser import parse_chapters_advanced, detect_chapters
    
    # 方式1: 直接解析章节内容
    chapters = parse_chapters_advanced(content)
    
    # 方式2: 从文件检测章节位置
    chapters = detect_chapters(filepath)
"""
import re
from statistics import median

ANCHOR_RULES = [
    (re.compile(r'^第\s*[\d一二三四五六七八九十百千万零]+\s*[卷部篇章回节条编集]'), 'cn'),
    (re.compile(r'^(?:Chapter|Part|Section)\s+\d+', re.I), 'en'),
    (re.compile(r'^\d+[\.\u3001]\s*\S'), 'num'),
    (re.compile(r'^(?:前言|序[言章幕]?|楔子|引子|后记|尾声|跋)\s*$'), 'sp'),
    (re.compile(r'^\S{2,25}[（\(][\d一二三四五六七八九十百零]+[）\)]\s*$'), 'cn_paren'),
]

LOOSE_RULES = [
    (re.compile(r'^[=\-_~#*\uff9f\u2014\u2026]{3,}\s*.+?\s*[=\-_~#*\uff9f\u2014\u2026]{3,}$'), 'decorator'),
    (re.compile(r'^(?:前言|序|楔子|引子|后记|尾声|跋|附录)'), 'sp_loose'),
    (re.compile(r'^\S{2,25}[（\(][\d一二三四五六七八九十百零]+[）\)]'), 'cn_paren_loose'),
]

BLOCK_RULES = [
    re.compile(r'^(?:内容简介|作品简介|内容介绍|简介|author|书名|正文|目录|更新时间)\b', re.I),
    re.compile(r'^\s*[""\u201c\u201d\'\u300c\u300d].+[""\u201c\u201d\'\u300c\u300d]\s*$'),
]

SEMANTIC_LEVEL = {
    '卷': 1, '部': 1, '篇': 1, '编': 1, '集': 1,
    '章': 2, '回': 2,
    '节': 3, '条': 3,
}

PUNCTUATION_END = set('，。、！？；：,.;:!?\u2026\u2014）」】')

SENTENCE_STARTERS = (
    'the ', 'a ', 'this ', 'that ', 'it ', 'he ', 'she ', 'they ', 'we ', 'you ', 'i ',
    '在', '到', '从', '把', '被', '让', '给', '用', '因为', '虽然', '但是',
    '然后', '忽然', '这时', '只见', '听到',
)

def count_blank_lines(lines, lineno, direction='before'):
    count = 0
    if direction == 'before':
        i = lineno - 1
        while i >= 0 and not lines[i].strip():
            count += 1
            i -= 1
    else:
        i = lineno + 1
        while i < len(lines) and not lines[i].strip():
            count += 1
            i += 1
    return count

def content_between(lines, start_ln, end_ln):
    return sum(len(lines[i].strip()) for i in range(start_ln + 1, end_ln)
               if i < len(lines) and lines[i].strip())

def looks_like_prose(text):
    if not text:
        return False

    if text[-1] in '\u3002\uff01\uff1f\u2026':
        return True

    if text[-1] in '\u201d\u300d\u300f\u300b"\'\xbb':
        return True

    if len(text) > 15 and text[-1] in '\uff0c\uff1b\uff1a':
        return True

    if len(text) > 25:
        punct_count = sum(1 for c in text if c in '\uff0c\u3002\u3001\uff01\uff1f\uff1b\uff1a\u2026\u2014\u201c\u201d\u2018\u2019\'\"')
        if punct_count >= 3:
            return True

    if len(text) > 8:
        prose_markers = (
            '\u7684\u8bf4',
            '\u7b11\u9053',
            '\u54ed\u9053',
            '\u558a\u9053',
            '\u5410\u9053',
            '\u95ee\u9053',
            '\u7b54\u9053',
            '\u7b11\u4e86\u7b11',
            '\u60f3\u5230',
            '\u89c9\u5f97',
            '\u770b\u5230',
            '\u542c\u5230',
            '\u611f\u5230',
            '\u53d1\u73b0',
            '\u6447\u6447\u5934',
            '\u70b9\u70b9\u5934',
            '\u53f9\u4e86\u53e3\u6c14',
            '\u4e0d\u7531\u5f97',
            '\u5fcd\u4e0d\u4f4f',
            '\u7ad9\u4e86\u8d77\u6765',
            '\u8d70\u4e86\u8fc7\u53bb',
            '\u8f6c\u8fc7\u5934',
        )
        if any(p in text for p in prose_markers):
            return True

    if len(text) > 6:
        if text.startswith((
            '\u4ee5\u4e0b\u662f',
            '\u4e8e\u662f',
            '\u63a5\u7740',
            '\u7136\u540e',
            '\u540e\u6765',
            '\u8fd9\u65f6',
            '\u7a81\u7136',
            '\u5ffd\u7136',
            '\u6b64\u65f6',
            '\u5f53\u65f6',
        )):
            return True

    if re.search(r'\S{1,6}[\u8bf4\u9053\u95ee\u7b54\u558a\u53eb\u7b11\u54ed\u5410\u543c][:\uff1a]', text):
        return True

    return False

def is_blocked(text):
    if not text or len(text) > 80:
        return True
    return any(r.search(text) for r in BLOCK_RULES)

def _has_meta_marker(text):
    if not text:
        return False
    if '://' in text:
        return True
    if re.search(r'\S+@\S+\.\S+', text):
        return True
    for ch in text:
        cp = ord(ch)
        if (0x1F300 <= cp <= 0x1FAFF
            or 0x2600 <= cp <= 0x26FF
            or 0x2700 <= cp <= 0x27BF
            or cp == 0xFE0F
            or cp == 0x200D):
            return True
    return False

def find_content_start(lines, max_scan=500):
    last_meta = -1
    scan_end = min(150, len(lines))
    for i in range(scan_end):
        if _has_meta_marker(lines[i].strip()):
            last_meta = i

    if last_meta < 0 or last_meta > 120:
        return 0

    chp_patterns = [
        re.compile(r'^第\s*[\d一二三四五六七八九十百千万零]+\s*[卷部篇章回节条编集]'),
        re.compile(r'^(?:Chapter|Part|Section)\s+\d+', re.I),
        re.compile(r'^\d+[\.\u3001]\s*\S'),
        re.compile(r'^(?:前言|序[言章幕]?|楔子|引子|后记|尾声|跋)\s*$'),
        re.compile(r'^\d{1,4}\s+\S'),
        re.compile(r'^\S{2,25}[（\(][\d一二三四五六七八九十百零]+[）\)]'),
    ]

    search_start = last_meta + 1
    search_end = min(search_start + 300, len(lines))
    for i in range(search_start, search_end):
        text = lines[i].strip()
        if not text:
            continue
        for pat in chp_patterns:
            if pat.search(text):
                return max(last_meta + 1, i - 40)

    return last_meta + 1

def _has_blank_before(lines, lineno):
    """检查指定行前面是否有空行
    
    章节标题前必须有空行，这是区分标题和正文的关键特征。
    例如：
    - "他想到第一章说的内容..." → 正文，不应识别为章节
    - 空行 + "第一章 开始" → 真正的章节标题
    """
    if lineno == 0:
        return True
    return not lines[lineno - 1].strip()

def phase1_discover(lines):
    anchors = []
    loose_cands = []

    for i, line in enumerate(lines):
        text = line.strip()
        if not text or is_blocked(text):
            continue

        hit_anchor = False
        for rule, rtype in ANCHOR_RULES:
            if rule.search(text):
                if _has_blank_before(lines, i):
                    anchors.append({
                        'lineno': i, 'title': text,
                        'confidence': 1.0, 'source': 'anchor',
                        'rule_type': rtype,
                    })
                hit_anchor = True
                break

        if hit_anchor:
            continue

        for rule, rtype in LOOSE_RULES:
            if rule.search(text):
                conf = _calc_loose_confidence(text, lines, i)
                if conf > 0:
                    loose_cands.append({
                        'lineno': i, 'title': text,
                        'confidence': conf, 'source': 'loose',
                        'rule_type': rtype,
                    })
                break

    return anchors, loose_cands

def _calc_loose_confidence(text, lines, lineno):
    if lineno > 0 and lines[lineno - 1].strip():
        return 0.0

    if looks_like_prose(text):
        return 0.0

    conf = 0.5

    if lineno + 1 < len(lines) and not lines[lineno + 1].strip():
        conf += 0.15
    if len(text) <= 10:
        conf += 0.15
    elif len(text) < 20:
        conf += 0.1

    if text[-1] in PUNCTUATION_END:
        conf -= 0.2
    if text[0].islower():
        conf -= 0.15
    if text[:12].lower().startswith(SENTENCE_STARTERS):
        conf -= 0.15
    quote_count = len(re.findall(r'[""\u201c\u201d\'\u300c\u300d]', text))
    if quote_count >= 2:
        conf -= 0.25
    elif quote_count == 1:
        conf -= 0.1
    if len(text) > 25:
        conf -= 0.1

    return max(0.0, min(1.0, conf))

def phase2_learn_pattern(anchors, lines):
    if len(anchors) < 3:
        return None

    pattern = {}
    lengths = [len(a['title']) for a in anchors]
    pattern['min_len'] = max(3, min(lengths) * 0.5)
    pattern['max_len'] = max(lengths) * 2.5

    blanks_before = [count_blank_lines(lines, a['lineno'], 'before') for a in anchors]
    pattern['require_blank_before'] = (
        sum(1 for b in blanks_before if b > 0) > len(blanks_before) * 0.5
    )
    if pattern['require_blank_before']:
        pattern['min_blank'] = min(b for b in blanks_before if b > 0)

    gaps = []
    for i in range(1, len(anchors)):
        gap = content_between(lines, anchors[i - 1]['lineno'], anchors[i]['lineno'])
        if gap > 0:
            gaps.append(gap)
    if gaps:
        pattern['min_gap'] = median(gaps) * 0.15
        pattern['median_gap'] = median(gaps)
    else:
        pattern['min_gap'] = 0
        pattern['median_gap'] = 1000

    titles = [a['title'] for a in anchors]
    prefix_re = _extract_prefix_regex(titles)
    if prefix_re:
        pattern['prefix_re'] = prefix_re

    return pattern

def _extract_prefix_regex(titles):
    n = len(titles)

    if sum(1 for t in titles
           if re.match(r'^第\s*[\d一二三四五六七八九十百千万零]+\s*[卷部篇章回节条编集]', t)) > n * 0.7:
        return re.compile(r'^第\s*[\d一二三四五六七八九十百千万零]+\s*[卷部篇章回节条编集]')

    if sum(1 for t in titles if re.match(r'^(?:Chapter|Part|Section)\s+\d+', t, re.I)) > n * 0.7:
        return re.compile(r'^(?:Chapter|Part|Section)\s+\d+', re.I)

    if sum(1 for t in titles if re.match(r'^\d+[\.\u3001]', t)) > n * 0.7:
        return re.compile(r'^\d+[\.\u3001]\s*\S')

    if sum(1 for t in titles if re.match(r'^\d{1,4}\s+\S', t)) > n * 0.5:
        return re.compile(r'^\d{1,4}\s+\S')

    if sum(1 for t in titles if re.search(r'[（\(][\d一二三四五六七八九十百零]+[）\)]', t)) > n * 0.7:
        return re.compile(r'^\S{2,25}[（\(][\d一二三四五六七八九十百零]+[）\)]')

    return None

def phase3_expand(lines, pattern, anchors, loose_cands):
    existing = {a['lineno'] for a in anchors}
    existing.update(c['lineno'] for c in loose_cands)
    expanded = []

    has_prefix = 'prefix_re' in pattern

    for i, line in enumerate(lines):
        if i in existing:
            continue
        text = line.strip()
        if not text or is_blocked(text):
            continue

        if looks_like_prose(text):
            continue

        if not (pattern['min_len'] <= len(text) <= pattern['max_len']):
            continue

        if has_prefix:
            if pattern.get('require_blank_before'):
                blanks = count_blank_lines(lines, i, 'before')
                if blanks < pattern.get('min_blank', 1):
                    continue
        else:
            blanks = count_blank_lines(lines, i, 'before')
            if blanks < 1:
                continue

        if has_prefix:
            if not pattern['prefix_re'].search(text):
                continue

        expanded.append({
            'lineno': i, 'title': text,
            'confidence': 0.8, 'source': 'pattern',
            'rule_type': 'pattern',
        })
        existing.add(i)

    return expanded

def phase4_validate(all_candidates, lines):
    if len(all_candidates) <= 2:
        return all_candidates

    all_candidates.sort(key=lambda x: x['lineno'])
    remove = set()

    anchors_only = [c for c in all_candidates if c['source'] == 'anchor']

    if len(anchors_only) >= 3:
        anchor_gaps = []
        for i in range(1, len(anchors_only)):
            gap = content_between(lines,
                                  anchors_only[i - 1]['lineno'],
                                  anchors_only[i]['lineno'])
            if gap > 0:
                anchor_gaps.append(gap)

        if anchor_gaps:
            min_valid_gap = max(300, min(median(anchor_gaps) * 0.03, 2000))
        else:
            min_valid_gap = 300
    else:
        min_valid_gap = 300

    last_kept_idx = -1
    for i, c in enumerate(all_candidates):
        if i in remove:
            continue
        if last_kept_idx >= 0:
            gap = content_between(lines,
                                  all_candidates[last_kept_idx]['lineno'],
                                  c['lineno'])
            if gap < min_valid_gap and c['source'] != 'anchor':
                remove.add(i)
                continue
        last_kept_idx = i

    for i, c in enumerate(all_candidates):
        if c['confidence'] < 0.3 and i not in remove:
            remove.add(i)

    return [c for i, c in enumerate(all_candidates) if i not in remove]

def phase5_assign_levels(candidates):
    if not candidates:
        return

    for c in candidates:
        c['level'] = 2
        title_lower = c['title'].lower()
        for kw, lv in SEMANTIC_LEVEL.items():
            if kw in title_lower:
                c['level'] = lv
                break
        if re.match(r'^[=\-_~#*\uff9f\u2014\u2026]{3,}', c['title']):
            c['level'] = 1

    levels_present = set(c['level'] for c in candidates)
    if 2 in levels_present and 1 not in levels_present:
        for c in candidates:
            if re.search(r'世界[篇卷部]$|之[上中下篇卷部]|篇$|卷$', c['title']):
                c['level'] = 1
                break

    levels_present = set(c['level'] for c in candidates)
    if len(levels_present) == 1:
        for c in candidates:
            c['level'] = 1

def detect_chapters_from_lines(lines, log_callback=None):
    """从行列表检测章节
    
    Args:
        lines: 文本行列表
        log_callback: 日志回调函数（可选）
    
    Returns:
        list: 章节列表，每个元素包含 lineno, title, level, score
    """
    def log(msg):
        if log_callback:
            try:
                log_callback(msg)
            except Exception:
                pass

    log(f"总行数: {len(lines)}")

    content_start = find_content_start(lines)
    if content_start > 0:
        log(f"跳过文件头前 {content_start} 行（平台元数据区域）")
        lines = lines[content_start:]
    else:
        log("未检测到文件头元数据区域，从头开始")

    anchors, loose_cands = phase1_discover(lines)
    log(f"[Phase 1] 锚点: {len(anchors)}, 宽松候选: {len(loose_cands)}")

    pattern = phase2_learn_pattern(anchors, lines)
    if pattern:
        log(f"[Phase 2] 学习到的模式: 长度 {pattern['min_len']:.0f}~{pattern['max_len']:.0f}")

    expanded = []
    if pattern:
        expanded = phase3_expand(lines, pattern, anchors, loose_cands)
        log(f"[Phase 3] 模式扩展发现: {len(expanded)} 个新候选")

    all_candidates = anchors + loose_cands + expanded
    seen = set()
    unique = []
    for c in all_candidates:
        if c['lineno'] not in seen:
            seen.add(c['lineno'])
            unique.append(c)
    unique.sort(key=lambda x: x['lineno'])

    log(f"[合并后] 总候选: {len(unique)}")

    validated = phase4_validate(unique, lines)
    log(f"[Phase 4] 统计验证: 剩余 {len(validated)} 个")

    phase5_assign_levels(validated)

    log(f"[结果] 最终章节: {len(validated)} 个")

    return [
        {
            'lineno': c['lineno'] + content_start,
            'title': c['title'],
            'level': c['level'],
            'score': c['confidence'],
        }
        for c in validated
    ]

def detect_chapters(filepath, encoding=None, log_file=None):
    """V3.1 章节检测主入口 - 从文件检测
    
    Args:
        filepath: 文件路径
        encoding: 文件编码（可选，自动检测）
        log_file: 日志文件对象（可选）
    
    Returns:
        list: 章节列表，每个元素包含 lineno, title, level, score
    """
    from utils.file import detect_file_encoding
    
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    if encoding is None:
        encoding = detect_file_encoding(filepath)
    
    lines = raw.decode(encoding, errors='ignore').splitlines()

    def log(msg):
        if log_file:
            try:
                log_file.write(msg + '\n')
                log_file.flush()
            except Exception:
                pass

    log(f"文件: {filepath}")
    log(f"编码: {encoding}")
    
    return detect_chapters_from_lines(lines, log)

def parse_chapters_advanced(content):
    """高级章节解析 - 将小说内容解析为章节列表
    
    这是供 novel 模块使用的主要接口，返回格式与原 parser.py 兼容
    
    Args:
        content: 小说全文内容
    
    Returns:
        list: 章节列表，每个元素包含 name 和 content
    """
    if not content or not content.strip():
        return []
    
    lines = content.split('\n')
    
    chapters_info = detect_chapters_from_lines(lines)
    
    if not chapters_info:
        return [{
            'name': '正文',
            'content': content.strip()
        }]
    
    result = []
    for i, ch in enumerate(chapters_info):
        start_lineno = ch['lineno']
        
        if i + 1 < len(chapters_info):
            end_lineno = chapters_info[i + 1]['lineno']
            chapter_lines = lines[start_lineno:end_lineno]
        else:
            chapter_lines = lines[start_lineno:]
        
        chapter_content = '\n'.join(chapter_lines).strip()
        
        chapter_content = re.sub(r'^' + re.escape(ch['title']) + r'\s*\n?', '', chapter_content, count=1)
        
        result.append({
            'name': ch['title'],
            'content': chapter_content.strip()
        })
    
    if chapters_info and chapters_info[0]['lineno'] > 0:
        preface_lines = lines[:chapters_info[0]['lineno']]
        preface_content = '\n'.join(preface_lines).strip()
        if preface_content and len(preface_content) > 100:
            result.insert(0, {
                'name': '前言',
                'content': preface_content
            })
    
    return result
