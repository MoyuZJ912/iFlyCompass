import re

PASSWORD_STRENGTH_LEVELS = {
    1: {
        'name': '至少6位字母数字组合',
        'description': '密码至少包含6位字母和数字的组合'
    },
    2: {
        'name': '至少6位大小写字母和数字组合',
        'description': '密码至少包含6位，必须同时包含大写字母、小写字母和数字'
    },
    3: {
        'name': '至少8位大小写字母和数字及特殊符号组合',
        'description': '密码至少包含8位，必须同时包含大写字母、小写字母、数字和特殊符号'
    },
    4: {
        'name': '无任何要求',
        'description': '密码无任何限制'
    }
}

def validate_password_strength(password, level):
    """
    验证密码强度
    
    Args:
        password: 密码字符串
        level: 强度等级 (1-4)
            1: 至少6位字母数字组合
            2: 至少6位大小写字母和数字组合
            3: 至少8位大小写字母和数字及特殊符号组合
            4: 无任何要求
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, '密码不能为空'
    
    if level == 4:
        return True, None
    
    if level == 1:
        if len(password) < 6:
            return False, '密码长度至少6位'
        if not re.search(r'[a-zA-Z]', password):
            return False, '密码必须包含字母'
        if not re.search(r'[0-9]', password):
            return False, '密码必须包含数字'
        return True, None
    
    elif level == 2:
        if len(password) < 6:
            return False, '密码长度至少6位'
        if not re.search(r'[a-z]', password):
            return False, '密码必须包含小写字母'
        if not re.search(r'[A-Z]', password):
            return False, '密码必须包含大写字母'
        if not re.search(r'[0-9]', password):
            return False, '密码必须包含数字'
        return True, None
    
    elif level == 3:
        if len(password) < 8:
            return False, '密码长度至少8位'
        if not re.search(r'[a-z]', password):
            return False, '密码必须包含小写字母'
        if not re.search(r'[A-Z]', password):
            return False, '密码必须包含大写字母'
        if not re.search(r'[0-9]', password):
            return False, '密码必须包含数字'
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
            return False, '密码必须包含特殊符号'
        return True, None
    
    return True, None

def is_weak_password(password):
    """
    检查是否为弱密码
    
    弱密码定义：
    - 长度小于6位
    - 纯数字
    - 纯字母
    - 常见弱密码（如123456, password等）
    """
    if len(password) < 6:
        return True
    
    if password.isdigit():
        return True
    
    if password.isalpha():
        return True
    
    weak_passwords = [
        '123456', 'password', '12345678', 'qwerty', '123456789',
        '12345', '1234', '111111', '1234567', 'dragon',
        '123123', 'baseball', 'iloveyou', 'trustno1', 'sunshine',
        'master', 'welcome', 'shadow', 'ashley', 'football',
        'jesus', 'michael', 'ninja', 'mustang', 'password1'
    ]
    
    if password.lower() in weak_passwords:
        return True
    
    return False

def validate_username(username, min_length, max_length):
    """
    验证用户名
    
    Args:
        username: 用户名字符串
        min_length: 最小长度
        max_length: 最大长度
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username:
        return False, '用户名不能为空'
    
    if len(username) < min_length:
        return False, f'用户名长度至少{min_length}位'
    
    if len(username) > max_length:
        return False, f'用户名长度不能超过{max_length}位'
    
    if not re.match(r'^[\w\u4e00-\u9fa5]+$', username):
        return False, '用户名只能包含中文、英文、数字和下划线'
    
    return True, None

def validate_nickname(nickname, min_length, max_length):
    """
    验证昵称
    
    Args:
        nickname: 昵称字符串
        min_length: 最小长度
        max_length: 最大长度
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not nickname:
        return True, None
    
    if len(nickname) < min_length:
        return False, f'昵称长度至少{min_length}位'
    
    if len(nickname) > max_length:
        return False, f'昵称长度不能超过{max_length}位'
    
    return True, None
