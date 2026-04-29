import os
import yaml
from config import Config

NAV_FILE_PATH = os.path.join(Config.INSTANCE_DIR, 'nav.yml')

def init_nav_file():
    if not os.path.exists(NAV_FILE_PATH):
        with open(NAV_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('# 导航配置文件\n')
            f.write('# \n')
            f.write('# 格式示例:\n')
            f.write('# onlineplayer:\n')
            f.write('#   name: 视频播放器\n')
            f.write('#   link: https://192.168.1.2:5003/player\n')
            f.write('#   category: tools\n')
            f.write('#   description: 本地视频播放程序 \\n一个更成熟的替代方案\n')
            f.write('#   icon: play_circle\n')
            f.write('# \n')
            f.write('# 说明:\n')
            f.write('#   - name: 显示名称\n')
            f.write('#   - link: 链接地址（外部链接以http开头，内部路径以/开头）\n')
            f.write('#   - category: 分类 (tools/games/other)\n')
            f.write('#   - description: 描述信息，支持\\n换行符\n')
            f.write('#   - icon: Material Icons图标ID，不存在则使用默认链接图标\n')
        print('已创建 nav.yml 配置文件')

def get_nav_items():
    if not os.path.exists(NAV_FILE_PATH):
        return []
    
    try:
        with open(NAV_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return []
            data = yaml.safe_load(content)
            if not data:
                return []
            
            items = []
            for key, value in data.items():
                if isinstance(value, dict) and 'name' in value and 'link' in value:
                    items.append({
                        'id': key,
                        'name': value.get('name', key),
                        'link': value.get('link', ''),
                        'category': value.get('category', 'tools'),
                        'description': value.get('description', ''),
                        'icon': value.get('icon', '')
                    })
            return items
    except Exception as e:
        print(f'读取 nav.yml 失败: {e}')
        return []
