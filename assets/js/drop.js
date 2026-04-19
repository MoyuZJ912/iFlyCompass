(function() {
    var DropManager = {
        lastId: 0,
        pollInterval: null,
        container: null,
        STORAGE_KEY: 'drop_last_id',
        
        init: function() {
            this.loadLastId();
            this.createContainer();
            this.startPolling();
        },
        
        loadLastId: function() {
            try {
                var saved = localStorage.getItem(this.STORAGE_KEY);
                if (saved) {
                    this.lastId = parseInt(saved, 10) || 0;
                }
            } catch (e) {
                console.error('[Drop] 读取 localStorage 失败:', e);
            }
        },
        
        saveLastId: function(id) {
            try {
                localStorage.setItem(this.STORAGE_KEY, id.toString());
            } catch (e) {
                console.error('[Drop] 保存 localStorage 失败:', e);
            }
        },
        
        createContainer: function() {
            if (document.getElementById('drop-container')) {
                return;
            }
            
            var container = document.createElement('div');
            container.id = 'drop-container';
            document.body.appendChild(container);
            this.container = container;
        },
        
        startPolling: function() {
            var self = this;
            this.poll();
            this.pollInterval = setInterval(function() {
                self.poll();
            }, 10000);
        },
        
        poll: function() {
            var self = this;
            var url = '/api/drop/poll?last_id=' + this.lastId;
            
            fetch(url)
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    if (data.enabled && data.drops && data.drops.length > 0) {
                        var maxId = self.lastId;
                        data.drops.forEach(function(drop) {
                            self.showDrop(drop);
                            if (drop.id > maxId) {
                                maxId = drop.id;
                            }
                        });
                        self.lastId = maxId;
                        self.saveLastId(maxId);
                    }
                })
                .catch(function(error) {
                    console.error('[Drop] 轮询失败:', error);
                });
        },
        
        showDrop: function(drop) {
            var self = this;
            
            var bubble = document.createElement('div');
            bubble.className = 'drop-bubble';
            bubble.innerHTML = 
                '<div class="drop-bubble-header">' +
                    '<span class="drop-sender-name">' + this.escapeHtml(drop.sender_name) + '</span>' +
                    '<button class="drop-close-btn" title="关闭">&times;</button>' +
                '</div>' +
                '<div class="drop-bubble-content">' + this.escapeHtml(drop.content) + '</div>' +
                '<div class="drop-bubble-footer">' +
                    '<button class="drop-block-btn" data-sender-id="' + drop.sender_id + '" data-sender-name="' + this.escapeHtml(drop.sender_name) + '">屏蔽该用户</button>' +
                    '<button class="drop-settings-btn">Drop设置</button>' +
                '</div>';
            
            this.container.appendChild(bubble);
            
            setTimeout(function() {
                bubble.classList.add('show');
            }, 10);
            
            var closeBtn = bubble.querySelector('.drop-close-btn');
            closeBtn.onclick = function() {
                self.hideDrop(bubble);
            };
            
            var blockBtn = bubble.querySelector('.drop-block-btn');
            blockBtn.onclick = function() {
                self.blockUser(drop.sender_id, drop.sender_name, bubble);
            };
            
            var settingsBtn = bubble.querySelector('.drop-settings-btn');
            settingsBtn.onclick = function() {
                window.location.href = '/drop/settings';
            };
            
            setTimeout(function() {
                self.hideDrop(bubble);
            }, 15000);
        },
        
        hideDrop: function(bubble) {
            var self = this;
            bubble.classList.remove('show');
            bubble.classList.add('hide');
            setTimeout(function() {
                if (bubble.parentNode) {
                    bubble.parentNode.removeChild(bubble);
                }
            }, 300);
        },
        
        blockUser: function(userId, senderName, bubble) {
            var self = this;
            
            if (window.ELEMENT && window.ELEMENT.MessageBox) {
                window.ELEMENT.MessageBox.confirm(
                    '屏蔽后将不再收到该用户的 Drop 消息',
                    '确定要屏蔽用户 "' + senderName + '" 吗？',
                    {
                        confirmButtonText: '确定',
                        cancelButtonText: '取消',
                        type: 'warning'
                    }
                ).then(function() {
                    self.doBlockUser(userId, senderName, bubble);
                }).catch(function() {});
            } else if (confirm('确定要屏蔽用户 "' + senderName + '" 吗？屏蔽后将不再收到该用户的 Drop 消息。')) {
                self.doBlockUser(userId, senderName, bubble);
            }
        },
        
        doBlockUser: function(userId, senderName, bubble) {
            var self = this;
            
            fetch('/api/drop/blacklist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: userId })
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    self.showMessage('success', '已屏蔽用户 ' + senderName);
                    self.hideDrop(bubble);
                } else {
                    self.showMessage('error', data.error || '屏蔽失败');
                }
            })
            .catch(function(error) {
                console.error('[Drop] 屏蔽用户失败:', error);
                self.showMessage('error', '屏蔽失败，请稍后重试');
            });
        },
        
        showMessage: function(type, message) {
            if (window.ELEMENT && window.ELEMENT.Message) {
                window.ELEMENT.Message({
                    message: message,
                    type: type
                });
            } else {
                alert(message);
            }
        },
        
        escapeHtml: function(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };
    
    var DropSender = {
        dialogVisible: false,
        globalCooldown: 0,
        userCooldown: 0,
        statusInterval: null,
        
        openDialog: function() {
            if (this.dialogVisible) {
                return;
            }
            this.dialogVisible = true;
            this.createDialog();
            this.loadStatus();
            this.startStatusPolling();
        },
        
        closeDialog: function() {
            this.dialogVisible = false;
            this.stopStatusPolling();
            var dialog = document.getElementById('drop-send-dialog');
            if (dialog) {
                dialog.parentNode.removeChild(dialog);
            }
        },
        
        createDialog: function() {
            var self = this;
            
            var overlay = document.createElement('div');
            overlay.id = 'drop-send-dialog';
            overlay.className = 'drop-dialog-overlay';
            overlay.innerHTML = 
                '<div class="drop-dialog">' +
                    '<div class="drop-dialog-header">' +
                        '<h3>发送 Drop</h3>' +
                        '<button class="drop-dialog-close">&times;</button>' +
                    '</div>' +
                    '<div class="drop-dialog-body">' +
                        '<div class="drop-cooldown-info">' +
                            '<div class="drop-cooldown-item">' +
                                '<span class="drop-cooldown-label">全服冷却</span>' +
                                '<span id="drop-global-cooldown" class="drop-cooldown-value">0秒</span>' +
                            '</div>' +
                            '<div class="drop-cooldown-item">' +
                                '<span class="drop-cooldown-label">个人冷却</span>' +
                                '<span id="drop-user-cooldown" class="drop-cooldown-value">0秒</span>' +
                            '</div>' +
                        '</div>' +
                        '<textarea id="drop-content-input" class="drop-textarea" placeholder="输入 Drop 消息（最多200字）" maxlength="200"></textarea>' +
                        '<div class="drop-char-count"><span id="drop-char-count">0</span>/200</div>' +
                    '</div>' +
                    '<div class="drop-dialog-footer">' +
                        '<button id="drop-cancel-btn" class="drop-btn drop-btn-secondary">取消</button>' +
                        '<button id="drop-send-btn" class="drop-btn drop-btn-primary" disabled>发送</button>' +
                    '</div>' +
                '</div>';
            
            document.body.appendChild(overlay);
            
            overlay.querySelector('.drop-dialog-close').onclick = function() {
                self.closeDialog();
            };
            
            overlay.querySelector('#drop-cancel-btn').onclick = function() {
                self.closeDialog();
            };
            
            overlay.onclick = function(e) {
                if (e.target === overlay) {
                    self.closeDialog();
                }
            };
            
            var textarea = overlay.querySelector('#drop-content-input');
            var charCount = overlay.querySelector('#drop-char-count');
            var sendBtn = overlay.querySelector('#drop-send-btn');
            
            textarea.oninput = function() {
                charCount.textContent = textarea.value.length;
                self.updateSendButton();
            };
            
            sendBtn.onclick = function() {
                self.sendDrop();
            };
        },
        
        loadStatus: function() {
            var self = this;
            
            fetch('/api/drop/status')
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    self.globalCooldown = data.global_cooldown;
                    self.userCooldown = data.user_cooldown;
                    self.updateCooldownDisplay();
                    self.updateSendButton();
                })
                .catch(function(error) {
                    console.error('[Drop] 获取状态失败:', error);
                });
        },
        
        startStatusPolling: function() {
            var self = this;
            this.statusInterval = setInterval(function() {
                self.loadStatus();
            }, 1000);
        },
        
        stopStatusPolling: function() {
            if (this.statusInterval) {
                clearInterval(this.statusInterval);
                this.statusInterval = null;
            }
        },
        
        updateCooldownDisplay: function() {
            var globalEl = document.getElementById('drop-global-cooldown');
            var userEl = document.getElementById('drop-user-cooldown');
            
            if (globalEl) {
                if (this.globalCooldown > 0) {
                    globalEl.textContent = this.globalCooldown + '秒';
                    globalEl.className = 'drop-cooldown-value cooling';
                } else {
                    globalEl.textContent = '就绪';
                    globalEl.className = 'drop-cooldown-value ready';
                }
            }
            if (userEl) {
                if (this.userCooldown > 0) {
                    userEl.textContent = this.userCooldown + '秒';
                    userEl.className = 'drop-cooldown-value cooling';
                } else {
                    userEl.textContent = '就绪';
                    userEl.className = 'drop-cooldown-value ready';
                }
            }
        },
        
        updateSendButton: function() {
            var sendBtn = document.getElementById('drop-send-btn');
            var textarea = document.getElementById('drop-content-input');
            
            if (!sendBtn || !textarea) {
                return;
            }
            
            var canSend = this.globalCooldown === 0 && 
                          this.userCooldown === 0 && 
                          textarea.value.trim().length > 0;
            
            sendBtn.disabled = !canSend;
            
            if (this.globalCooldown > 0) {
                sendBtn.textContent = '全服冷却中';
            } else if (this.userCooldown > 0) {
                sendBtn.textContent = '个人冷却中';
            } else {
                sendBtn.textContent = '发送';
            }
        },
        
        sendDrop: function() {
            var self = this;
            var textarea = document.getElementById('drop-content-input');
            var content = textarea.value.trim();
            
            if (!content) {
                return;
            }
            
            var sendBtn = document.getElementById('drop-send-btn');
            sendBtn.disabled = true;
            sendBtn.textContent = '发送中...';
            
            fetch('/api/drop/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: content })
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    DropManager.showMessage('success', 'Drop 发送成功！');
                    self.closeDialog();
                } else {
                    DropManager.showMessage('error', data.error || '发送失败');
                    self.loadStatus();
                    self.updateSendButton();
                }
            })
            .catch(function(error) {
                console.error('[Drop] 发送失败:', error);
                DropManager.showMessage('error', '发送失败，请稍后重试');
                self.loadStatus();
                self.updateSendButton();
            });
        }
    };
    
    window.DropManager = DropManager;
    window.DropSender = DropSender;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            DropManager.init();
        });
    } else {
        DropManager.init();
    }
})();
