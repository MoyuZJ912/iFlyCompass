import json
import re
import requests
import threading
from flask import jsonify, request, Response, stream_with_context
from flask_login import login_required, current_user
from config import get_config, save_config, encrypt_value, decrypt_value
from . import ai_chat_bp

# In-memory conversation history: {user_id: [{"role": "user"/"assistant", "content": "..."}]}
_conversations = {}
_conversations_lock = threading.Lock()
MAX_HISTORY = 40  # max message pairs to keep per user

def _normalize_api_url(url):
    """Normalize API URL: append /v1/chat/completions if missing."""
    url = url.strip().rstrip('/')
    if not url:
        return 'https://api.deepseek.com/v1/chat/completions'
    # If URL already contains the full path, return as-is
    if '/chat/completions' in url:
        return url
    # Otherwise append the standard OpenAI-compatible endpoint path
    return url + '/v1/chat/completions'


def _get_api_config():
    """Get AI API configuration from config file."""
    config = get_config()
    ai_config = config.get('ai', {})
    raw_url = ai_config.get('api_url', 'https://api.deepseek.com/v1/chat/completions')
    
    # Read API key — decrypt if encrypted, otherwise auto-migrate plaintext
    raw_key = ai_config.get('api_key', '')
    if raw_key and not raw_key.startswith('enc:'):
        # Plaintext key found — encrypt and save back
        encrypted = encrypt_value(raw_key)
        if 'ai' not in config:
            config['ai'] = {}
        config['ai']['api_key'] = encrypted
        save_config(config)
    
    return {
        'api_url': _normalize_api_url(raw_url),
        'api_key': decrypt_value(raw_key) if raw_key else '',
        'model': ai_config.get('model', 'deepseek-chat'),
        'max_tokens': ai_config.get('max_tokens', 2048),
        'temperature': ai_config.get('temperature', 0.7),
        'system_prompt': ai_config.get('system_prompt', '你是一个有用的AI助手，请用中文回答用户的问题。'),
        'reasoning_effort': ai_config.get('reasoning_effort', None),
        'thinking_enabled': ai_config.get('thinking_enabled', False)
    }

def _save_api_config(key, value):
    """Save a single AI config value."""
    config = get_config()
    if 'ai' not in config:
        config['ai'] = {}
    config['ai'][key] = value
    save_config(config)

def _get_conversation(user_id):
    """Get or create conversation history for a user."""
    with _conversations_lock:
        if user_id not in _conversations:
            _conversations[user_id] = []
        return _conversations[user_id]

def _add_message(user_id, role, content):
    """Add a message to conversation history."""
    with _conversations_lock:
        if user_id not in _conversations:
            _conversations[user_id] = []
        _conversations[user_id].append({"role": role, "content": content})
        # Trim old messages
        if len(_conversations[user_id]) > MAX_HISTORY * 2:
            _conversations[user_id] = _conversations[user_id][-(MAX_HISTORY * 2):]

def _clear_conversation(user_id):
    """Clear conversation history for a user."""
    with _conversations_lock:
        _conversations[user_id] = []

@ai_chat_bp.route('/api/ai-chat/config', methods=['GET'])
@login_required
def get_ai_config():
    """Get AI config (without API key for security)."""
    if not (current_user.is_admin or current_user.is_super_admin):
        return jsonify({'error': '权限不足'}), 403
    
    config = _get_api_config()
    # Mask the API key - only show first 4 and last 4 chars
    api_key = config['api_key']
    if api_key and len(api_key) > 8:
        masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
    elif api_key:
        masked_key = api_key[:2] + '****'
    else:
        masked_key = ''
    
    return jsonify({
        'api_url': config['api_url'],
        'api_key_masked': masked_key,
        'has_api_key': bool(api_key),
        'model': config['model'],
        'max_tokens': config['max_tokens'],
        'temperature': config['temperature'],
        'system_prompt': config['system_prompt'],
        'reasoning_effort': config['reasoning_effort'],
        'thinking_enabled': config['thinking_enabled']
    })

@ai_chat_bp.route('/api/ai-chat/config', methods=['PUT'])
@login_required
def update_ai_config():
    """Update AI configuration (admin only). API key cannot be viewed after saving."""
    if not (current_user.is_admin or current_user.is_super_admin):
        return jsonify({'error': '权限不足'}), 403
    
    data = request.json
    
    if 'api_key' in data and data['api_key']:
        # Only update if a new key is provided (not masked)
        key = data['api_key'].strip()
        if key and not key.startswith('****') and '*' not in key:
            _save_api_config('api_key', encrypt_value(key))
    
    if 'api_url' in data:
        url = data['api_url'].strip()
        if url:
            _save_api_config('api_url', url)
    
    if 'model' in data:
        model = data['model'].strip()
        if model:
            _save_api_config('model', model)
    
    if 'max_tokens' in data:
        try:
            mt = int(data['max_tokens'])
            if 100 <= mt <= 16384:
                _save_api_config('max_tokens', mt)
        except (ValueError, TypeError):
            pass
    
    if 'temperature' in data:
        try:
            temp = float(data['temperature'])
            if 0.0 <= temp <= 2.0:
                _save_api_config('temperature', temp)
        except (ValueError, TypeError):
            pass
    
    if 'system_prompt' in data:
        sp = data['system_prompt'].strip()
        if sp:
            _save_api_config('system_prompt', sp)
    
    if 'reasoning_effort' in data:
        re_val = data['reasoning_effort']
        if re_val is None or re_val in ('low', 'medium', 'high'):
            _save_api_config('reasoning_effort', re_val)
    
    if 'thinking_enabled' in data:
        _save_api_config('thinking_enabled', bool(data['thinking_enabled']))
    
    return jsonify({'success': True, 'message': 'AI配置已保存'})

@ai_chat_bp.route('/api/ai-chat/send', methods=['POST'])
@login_required
def send_message():
    """Send a message to AI and get response."""
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': '消息不能为空'}), 400
    
    if len(message) > 4000:
        return jsonify({'error': '消息过长，请限制在4000字以内'}), 400
    
    config = _get_api_config()
    
    if not config['api_key']:
        return jsonify({'error': 'AI API Key 未配置，请联系管理员在系统设置中配置'}), 400
    
    # Build messages
    messages = [{"role": "system", "content": config['system_prompt']}]
    
    # Add conversation history
    history = _get_conversation(current_user.id)
    messages.extend(history[-MAX_HISTORY:])
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # Save user message to history
    _add_message(current_user.id, "user", message)
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config["api_key"]}'
        }
        
        payload = {
            'model': config['model'],
            'messages': messages,
            'max_tokens': config['max_tokens'],
            'temperature': config['temperature']
        }
        
        # DeepSeek-specific: reasoning_effort
        if config.get('reasoning_effort'):
            payload['reasoning_effort'] = config['reasoning_effort']
        
        # DeepSeek-specific: thinking mode
        if config.get('thinking_enabled'):
            payload['thinking'] = {'type': 'enabled'}
        
        resp = requests.post(
            config['api_url'],
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if resp.status_code != 200:
            error_detail = resp.text
            try:
                error_json = resp.json()
                if 'error' in error_json:
                    error_detail = error_json['error'].get('message', resp.text)
            except Exception:
                pass
            if resp.status_code == 404:
                hint = '请检查 API URL 配置是否正确（通常应包含 /v1/chat/completions 路径）'
                error_detail = f'{error_detail}。{hint}'
            return jsonify({'error': f'AI API 错误 ({resp.status_code}): {error_detail}'}), 502
        
        result = resp.json()
        assistant_message = result['choices'][0]['message']['content']
        
        # Save assistant response to history
        _add_message(current_user.id, "assistant", assistant_message)
        
        # Get token usage
        usage = result.get('usage', {})
        
        return jsonify({
            'success': True,
            'message': assistant_message,
            'usage': {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'AI API 请求超时，请稍后重试'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': '无法连接到 AI API 服务器，请检查 API URL 配置'}), 502
    except Exception as e:
        return jsonify({'error': f'请求失败: {str(e)}'}), 500

@ai_chat_bp.route('/api/ai-chat/stream', methods=['POST'])
@login_required
def send_message_stream():
    """Send a message to AI and get streaming response."""
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': '消息不能为空'}), 400
    
    if len(message) > 4000:
        return jsonify({'error': '消息过长，请限制在4000字以内'}), 400
    
    config = _get_api_config()
    
    if not config['api_key']:
        return jsonify({'error': 'AI API Key 未配置，请联系管理员在系统设置中配置'}), 400
    
    # Build messages
    messages = [{"role": "system", "content": config['system_prompt']}]
    history = _get_conversation(current_user.id)
    messages.extend(history[-MAX_HISTORY:])
    messages.append({"role": "user", "content": message})
    
    # Save user message to history
    _add_message(current_user.id, "user", message)
    
    def generate():
        full_response = ""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {config["api_key"]}'
            }
            
            payload = {
                'model': config['model'],
                'messages': messages,
                'max_tokens': config['max_tokens'],
                'temperature': config['temperature'],
                'stream': True
            }
            
            # DeepSeek-specific: reasoning_effort
            if config.get('reasoning_effort'):
                payload['reasoning_effort'] = config['reasoning_effort']
            
            # DeepSeek-specific: thinking mode
            if config.get('thinking_enabled'):
                payload['thinking'] = {'type': 'enabled'}
            
            resp = requests.post(
                config['api_url'],
                headers=headers,
                json=payload,
                timeout=120,
                stream=True
            )
            
            if resp.status_code != 200:
                error_detail = resp.text
                try:
                    error_json = resp.json()
                    if 'error' in error_json:
                        error_detail = error_json['error'].get('message', resp.text)
                except Exception:
                    pass
                if resp.status_code == 404:
                    hint = '请检查 API URL 配置是否正确（通常应包含 /v1/chat/completions 路径）'
                    error_detail = f'{error_detail}。{hint}'
                yield f"data: {json.dumps({'error': f'AI API 错误 ({resp.status_code}): {error_detail}'})}\n\n"
                return
            
            for line in resp.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            # Check for usage in final chunk
                            if 'usage' in chunk:
                                yield f"data: {json.dumps({'usage': chunk['usage']})}\n\n"
                        except json.JSONDecodeError:
                            continue
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except requests.exceptions.Timeout:
            yield f"data: {json.dumps({'error': 'AI API 请求超时，请稍后重试'})}\n\n"
        except requests.exceptions.ConnectionError:
            yield f"data: {json.dumps({'error': '无法连接到 AI API 服务器，请检查 API URL 配置'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': f'请求失败: {str(e)}'})}\n\n"
        
        # Save assistant response to history
        if full_response:
            _add_message(current_user.id, "assistant", full_response)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@ai_chat_bp.route('/api/ai-chat/history', methods=['GET'])
@login_required
def get_history():
    """Get conversation history for current user."""
    history = _get_conversation(current_user.id)
    return jsonify({
        'success': True,
        'history': history
    })

@ai_chat_bp.route('/api/ai-chat/history', methods=['DELETE'])
@login_required
def clear_history():
    """Clear conversation history for current user."""
    _clear_conversation(current_user.id)
    return jsonify({'success': True, 'message': '对话历史已清空'})
