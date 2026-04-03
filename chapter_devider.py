# -*- coding: utf-8 -*-
"""
章节检测 V3.1 — 锚点学习 + 统计验证

V3.1 修复（相对于 V3）：
1. find_content_start 完全重写：emoji/URL检测 + 首个章节标题定位
2. looks_like_prose 移除 len<8 短路，大幅增强散文检测信号
3. Phase3 无前缀模式时强制要求前空行
4. Phase4 置信度底线提高

用法: python chapter_v3.py 小说.txt
"""
import re
import os
import sys
import glob
from statistics import median

# ============================================================
#  配置区 — 规则少而精，职责分明
# ============================================================

# 锚点规则：极严格，宁可漏不可错（置信度 = 1.0）
ANCHOR_RULES = [
    (re.compile(r'^第\s*[\d一二三四五六七八九十百千万零]+\s*[卷部篇章回节条编集]'), 'cn'),
    (re.compile(r'^(?:Chapter|Part|Section)\s+\d+', re.I), 'en'),
    (re.compile(r'^\d+[\.\u3001]\s*\S'), 'num'),
    (re.compile(r'^(?:前言|序[言章幕]?|楔子|引子|后记|尾声|跋)\s*$'), 'sp'),
    # ↓↓↓ 新增：中文"标题（数字）"格式，要求 ）在行尾，极低误判率 ↓↓↓
    (re.compile(r'^\S{2,25}[（\(][\d一二三四五六七八九十百零]+[）\)]\s*$'), 'cn_paren'),
]


# 宽松规则：可能产生噪声，需要后续验证（置信度起步 0.5）
LOOSE_RULES = [
    (re.compile(r'^[=\-_~#*\uff9f\u2014\u2026]{3,}\s*.+?\s*[=\-_~#*\uff9f\u2014\u2026]{3,}$'), 'decorator'),
    (re.compile(r'^(?:前言|序|楔子|引子|后记|尾声|跋|附录)'), 'sp_loose'),
    # ↓↓↓ 新增：标题（数字）后可能有额外文字（如"二更""沈x萧"等） ↓↓↓
    (re.compile(r'^\S{2,25}[（\(][\d一二三四五六七八九十百零]+[）\)]'), 'cn_paren_loose'),
]


# 拦截规则：确定不是章节标题
BLOCK_RULES = [
    re.compile(r'^(?:内容简介|作品简介|内容介绍|简介|author|书名|正文|目录|更新时间)\b', re.I),
    re.compile(r'^\s*[""\u201c\u201d\'\u300c\u300d].+[""\u201c\u201d\'\u300c\u300d]\s*$'),
]

# 层级语义表
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

# ============================================================
#  工具函数
# ============================================================

def detect_encoding(raw_bytes):
    if raw_bytes.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    for enc in ('utf-8', 'gbk'):
        try:
            raw_bytes.decode(enc)
            return enc
        except UnicodeDecodeError:
            pass
    return 'utf-8'


def count_blank_lines(lines, lineno, direction='before'):
    """统计指定行前方/后方的连续空行数"""
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
    """两行之间的纯内容字符数（不含两端的行本身）"""
    return sum(len(lines[i].strip()) for i in range(start_ln + 1, end_ln)
               if i < len(lines) and lines[i].strip())


def looks_like_prose(text):
    """通用判断：该行是否更像正文句子而非章节标题

    标题 vs 正文在形式上有系统性差异：
    - 标题：短小精悍，不含句末标点，不含成对引号对话
    - 正文：可能以句号/感叹号/问号结尾，可能以右引号结尾，含对话标记

    注意：不再有 len < 8 短路（这是 V3 的关键 bug，导致"沉默。""不要回答！"
    等 3~6 字的短句全部漏过）。
    """
    if not text:
        return False

    # ── 强信号：几乎一定是正文（任一命中即返回 True）──

    # 以句号/感叹号/问号/省略号结尾 → 标题不会用这些结尾
    if text[-1] in '\u3002\uff01\uff1f\u2026':
        return True

    # 以右引号/右书名号结尾 → 正文对话或引用
    if text[-1] in '\u201d\u300d\u300f\u300b"\'\xbb':
        return True

    # 以逗号/分号/冒号结尾（且行足够长）→ 正文句子
    if len(text) > 15 and text[-1] in '\uff0c\uff1b\uff1a':
        return True

    # ── 中等信号：需要结合行长度等条件 ──

    # 长行 + 多标点 → 正文（标题标点通常很少）
    if len(text) > 25:
        punct_count = sum(1 for c in text if c in '\uff0c\u3002\u3001\uff01\uff1f\uff1b\uff1a\u2026\u2014\u201c\u201d\u2018\u2019\'\"')
        if punct_count >= 3:
            return True

    # 包含对话/叙述标记词（这些词几乎只出现在正文中）
    if len(text) > 8:
        prose_markers = (
            '\u7684\u8bf4',   # 的说
            '\u7b11\u9053',   # 笑道
            '\u54ed\u9053',   # 哭道
            '\u558a\u9053',   # 喊道
            '\u5410\u9053',   # 吐道
            '\u95ee\u9053',   # 问道
            '\u7b54\u9053',   # 答道
            '\u7b11\u4e86\u7b11', # 笑了笑
            '\u60f3\u5230',   # 想到
            '\u89c9\u5f97',   # 觉得
            '\u770b\u5230',   # 看到
            '\u542c\u5230',   # 听到
            '\u611f\u5230',   # 感到
            '\u53d1\u73b0',   # 发现
            '\u6447\u6447\u5934', # 摇摇头
            '\u70b9\u70b9\u5934', # 点点头
            '\u53f9\u4e86\u53e3\u6c14', # 叹了口气
            '\u4e0d\u7531\u5f97', # 不由得
            '\u5fcd\u4e0d\u4f4f', # 忍不住
            '\u7ad9\u4e86\u8d77\u6765', # 站了起来
            '\u8d70\u4e86\u8fc7\u53bb', # 走了过去
            '\u8f6c\u8fc7\u5934', # 转过头
        )
        if any(p in text for p in prose_markers):
            return True

    # 以叙述过渡词开头（正文特征，标题不会这样开头）
    if len(text) > 6:
        if text.startswith((
            '\u4ee5\u4e0b\u662f',  # 以下是
            '\u4e8e\u662f',        # 于是
            '\u63a5\u7740',        # 接着
            '\u7136\u540e',        # 然后
            '\u540e\u6765',        # 后来
            '\u8fd9\u65f6',        # 这时
            '\u7a81\u7136',        # 突然
            '\u5ffd\u7136',        # 忽然
            '\u6b64\u65f6',        # 此时
            '\u5f53\u65f6',        # 当时
        )):
            return True

    # 包含 "X说/道/问：对话" 模式
    if re.search(r'\S{1,6}[\u8bf4\u9053\u95ee\u7b54\u558a\u53eb\u7b11\u54ed\u5410\u543c][:\uff1a]', text):
        return True

    return False


def is_blocked(text):
    """是否被拦截（确定不是章节标题）"""
    if not text or len(text) > 80:
        return True
    return any(r.search(text) for r in BLOCK_RULES)


def _has_meta_marker(text):
    """该行是否包含平台元数据标记（emoji / URL / 邮箱）"""
    if not text:
        return False
    # URL
    if '://' in text:
        return True
    # 邮箱
    if re.search(r'\S+@\S+\.\S+', text):
        return True
    # Emoji：检测常见 emoji Unicode 范围
    for ch in text:
        cp = ord(ch)
        if (0x1F300 <= cp <= 0x1FAFF    # 各种 emoji 块
            or 0x2600 <= cp <= 0x26FF   # 杂项符号
            or 0x2700 <= cp <= 0x27BF   # 装饰符号
            or cp == 0xFE0F             # 变体选择器
            or cp == 0x200D):           # 零宽连接符
            return True
    return False


def find_content_start(lines, max_scan=500):
    """通用方法：跳过文件头的平台元数据区域

    策略（两步法）：
    Step 1 — 在前 150 行中找到最后一个含 emoji/URL/邮箱 的行
             （这些是平台导出元数据的典型特征，实际正文几乎不会在标题里用 emoji）
    Step 2 — 从该行之后搜索第一个"章节标题样式"的行
             章节标题 = 匹配锚点规则 OR "数字+空格+标题"格式
             找到后回退一些行以保留可能的序言/前言内容

    如果文件没有平台元数据（Step 1 找不到），返回 0（从头开始）。
    """
    # ── Step 1: 找平台元数据区域的末尾 ──
    last_meta = -1
    scan_end = min(150, len(lines))
    for i in range(scan_end):
        if _has_meta_marker(lines[i].strip()):
            last_meta = i

    # 没有检测到元数据，或元数据延伸太远（可能是正文中的 emoji）
    if last_meta < 0 or last_meta > 120:
        return 0

    # ── Step 2: 从元数据之后找第一个章节标题 ──
    # 用比 ANCHOR_RULES 更宽泛的模式来定位（不作为锚点，只用于定位起点）
    chp_patterns = [
        re.compile(r'^第\s*[\d一二三四五六七八九十百千万零]+\s*[卷部篇章回节条编集]'),
        re.compile(r'^(?:Chapter|Part|Section)\s+\d+', re.I),
        re.compile(r'^\d+[\.\u3001]\s*\S'),
        re.compile(r'^(?:前言|序[言章幕]?|楔子|引子|后记|尾声|跋)\s*$'),
        re.compile(r'^\d{1,4}\s+\S'),
        # ↓↓↓ 新增 ↓↓↓
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
                # 找到了第一个章节标题
                # 回退一些行以保留序言/前言等有价值内容
                return max(last_meta + 1, i - 40)

    # 没找到章节标题，就跳过元数据区域即可
    return last_meta + 1


# ============================================================
#  Phase 1: 发现 — 锚点 + 宽松候选
# ============================================================

def phase1_discover(lines):
    anchors = []
    loose_cands = []

    for i, line in enumerate(lines):
        text = line.strip()
        if not text or is_blocked(text):
            continue

        # 先尝试锚点规则（锚点不受 looks_like_prose 影响）
        hit_anchor = False
        for rule, rtype in ANCHOR_RULES:
            if rule.search(text):
                anchors.append({
                    'lineno': i, 'title': text,
                    'confidence': 1.0, 'source': 'anchor',
                    'rule_type': rtype,
                })
                hit_anchor = True
                break

        if hit_anchor:
            continue

        # 再尝试宽松规则
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
    """宽松匹配的置信度计算"""
    # ────── 硬性拦截（返回 0 = 直接丢弃）──────

    # 宽松候选必须有前空行
    # 理由：中文小说章节标题前几乎必有空行，这是区分"标题"与"正文短句"最可靠的单一信号
    if lineno > 0 and lines[lineno - 1].strip():
        return 0.0

    # 散文检测
    if looks_like_prose(text):
        return 0.0

    # ────── 计算置信度 ──────

    conf = 0.5

    # --- 加分项 ---
    if lineno + 1 < len(lines) and not lines[lineno + 1].strip():
        conf += 0.15
    if len(text) <= 10:
        conf += 0.15
    elif len(text) < 20:
        conf += 0.1

    # --- 减分项 ---
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


# ============================================================
#  Phase 2: 模式学习
# ============================================================

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

    # "数字 空格 标题" 格式（如 "1 科学边界"、"35 虫子"）
    if sum(1 for t in titles if re.match(r'^\d{1,4}\s+\S', t)) > n * 0.5:
        return re.compile(r'^\d{1,4}\s+\S')
    # ↓↓↓ 新增：学习（数字）格式作为前缀模式 ↓↓↓
    if sum(1 for t in titles if re.search(r'[（\(][\d一二三四五六七八九十百零]+[）\)]', t)) > n * 0.7:
        return re.compile(r'^\S{2,25}[（\(][\d一二三四五六七八九十百零]+[）\)]')

    return None


# ============================================================
#  Phase 3: 模式扩展 — 用学到的模式搜索遗漏的章节
# ============================================================

def phase3_expand(lines, pattern, anchors, loose_cands):
    """用学习的模式在全文搜索，补充遗漏的章节。

    V3.1 关键改动：当没有 prefix_re 时，强制要求前空行。
    理由：没有前缀模式意味着锚点格式很杂（无法学到可靠模式），
    此时如果不要求空行，Phase3 会匹配海量正文行。
    """
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

        # 【关键】散文过滤
        if looks_like_prose(text):
            continue

        # 长度检查
        if not (pattern['min_len'] <= len(text) <= pattern['max_len']):
            continue

        # ── 空行检查（V3.1 核心修复）──
        if has_prefix:
            # 有前缀模式时，按学习的模式来
            if pattern.get('require_blank_before'):
                blanks = count_blank_lines(lines, i, 'before')
                if blanks < pattern.get('min_blank', 1):
                    continue
        else:
            # 【无前缀模式 → 强制要求前空行】
            # 这是过滤正文行最有效的单一手段：
            # 章节标题前几乎必有空行，而正文中的句子前不会有空行
            blanks = count_blank_lines(lines, i, 'before')
            if blanks < 1:
                continue

        # 前缀匹配
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


# ============================================================
#  Phase 4: 统计验证 — 两阶段间距验证
# ============================================================

def phase4_validate(all_candidates, lines):
    """两阶段统计验证

    Pass 1 — 仅从锚点计算"正常章节间距"（锚点置信度 1.0，几乎无误检）
    Pass 2 — 用锚点间距过滤非锚点候选
    Pass 3 — 置信度底线兜底
    """
    if len(all_candidates) <= 2:
        return all_candidates

    all_candidates.sort(key=lambda x: x['lineno'])
    remove = set()

    # ═══ Pass 1: 从锚点计算正常章节间距 ═══
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

    # ═══ Pass 2: 用间距过滤非锚点候选 ═══
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

    # ═══ Pass 3: 置信度底线兜底 ═══
    for i, c in enumerate(all_candidates):
        if c['confidence'] < 0.3 and i not in remove:
            remove.add(i)

    return [c for i, c in enumerate(all_candidates) if i not in remove]


# ============================================================
#  Phase 5: 层级推断
# ============================================================

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


# ============================================================
#  主入口
# ============================================================

def detect_v3(filepath, encoding=None, log_file=None):
    """V3.1 章节检测主入口"""
    with open(filepath, 'rb') as f:
        raw = f.read()
    if encoding is None:
        encoding = detect_encoding(raw)
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
    log(f"总行数: {len(lines)}")

    # ── 跳过文件头的平台元数据区域 ──
    content_start = find_content_start(lines)
    if content_start > 0:
        log(f"跳过文件头前 {content_start} 行（平台元数据区域）")
        lines = lines[content_start:]
    else:
        log("未检测到文件头元数据区域，从头开始")

    # Phase 1: 发现
    anchors, loose_cands = phase1_discover(lines)
    log(f"\n[Phase 1] 锚点: {len(anchors)}, 宽松候选: {len(loose_cands)}")
    for a in anchors:
        log(f"  [ANCHOR] L{a['lineno']:04d} {a['title'][:40]}")
    for c in loose_cands:
        log(f"  [LOOSE]  L{c['lineno']:04d} conf={c['confidence']:.2f} {c['title'][:40]}")

    # Phase 2: 模式学习
    pattern = phase2_learn_pattern(anchors, lines)
    if pattern:
        log(f"\n[Phase 2] 学习到的模式:")
        log(f"  标题长度: {pattern['min_len']:.0f} ~ {pattern['max_len']:.0f}")
        log(f"  要求前空行: {pattern.get('require_blank_before', False)}")
        log(f"  最小间距: {pattern.get('min_gap', 0):.0f} 字符")
        log(f"  中位间距: {pattern.get('median_gap', 0):.0f} 字符")
        if 'prefix_re' in pattern:
            log(f"  前缀模式: {pattern['prefix_re'].pattern}")
    else:
        log(f"\n[Phase 2] 锚点不足({len(anchors)}<3)，跳过模式学习")

    # Phase 3: 模式扩展
    expanded = []
    if pattern:
        expanded = phase3_expand(lines, pattern, anchors, loose_cands)
        log(f"\n[Phase 3] 模式扩展发现: {len(expanded)} 个新候选")
        for c in expanded:
            log(f"  [PATTERN] L{c['lineno']:04d} {c['title'][:40]}")

    # 合并所有候选
    all_candidates = anchors + loose_cands + expanded
    seen = set()
    unique = []
    for c in all_candidates:
        if c['lineno'] not in seen:
            seen.add(c['lineno'])
            unique.append(c)
    unique.sort(key=lambda x: x['lineno'])

    log(f"\n[合并后] 总候选: {len(unique)} "
        f"(锚点={sum(1 for c in unique if c['source'] == 'anchor')}, "
        f"宽松={sum(1 for c in unique if c['source'] == 'loose')}, "
        f"模式={sum(1 for c in unique if c['source'] == 'pattern')})")

    # Phase 4: 统计验证
    validated = phase4_validate(unique, lines)
    removed = len(unique) - len(validated)
    log(f"\n[Phase 4] 统计验证: 移除 {removed} 个, 剩余 {len(validated)} 个")

    # Phase 5: 层级推断
    phase5_assign_levels(validated)

    log(f"\n[结果] 最终章节: {len(validated)} 个")
    for c in validated:
        log(f"  L{c['lineno']:04d} [L{c['level']}] conf={c['confidence']:.2f} {c['title'][:40]}")

    return [
        {
            'lineno': c['lineno'] + content_start,  # 恢复原始行号
            'title': c['title'],
            'level': c['level'],
            'score': c['confidence'],
        }
        for c in validated
    ]


# ============================================================
#  命令行入口
# ============================================================

if __name__ == "__main__":
    txt_dir = r"d:\项目文件\newhttptxt\txt"
    out_dir = r"d:\项目文件\newhttptxt\out"
    os.makedirs(out_dir, exist_ok=True)

    for txt_file in glob.glob(os.path.join(txt_dir, "*.txt")):
        basename = os.path.basename(txt_file)
        out_file = os.path.join(out_dir, basename.replace(".txt", "_result.txt"))
        debug_file = os.path.join(out_dir, basename.replace(".txt", "_debug.txt"))

        log_f = None
        try:
            log_f = open(debug_file, 'w', encoding='utf-8')
        except Exception:
            pass

        chs = detect_v3(txt_file, log_file=log_f)

        if log_f:
            log_f.close()

        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(f"文件: {basename}\n")
            f.write(f"检测到 {len(chs)} 个章节\n")
            f.write("=" * 70 + "\n")
            for i, c in enumerate(chs, 1):
                indent = "  " * (c['level'] - 1)
                f.write(f"  {i:3d}. {indent}[L{c['level']}] {c['title']}\n")

        print(f"{basename}: {len(chs)} 个章节 -> {out_file}")
