"""
AquaGuard 通知服务模块

负责发送微信推送通知 (目前支持 PushPlus)
"""

import requests
import json
import threading
from typing import Optional

class NotificationService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._token = ""
                cls._instance._enabled = False
        return cls._instance

    def set_config(self, token: str, enabled: bool = True):
        """配置通知服务"""
        self._token = token
        self._enabled = enabled

    def get_config(self) -> dict:
        """获取当前配置"""
        return {
            "token": self._token,
            "enabled": self._enabled
        }

    def send_push(self, title: str, content: str = "") -> bool:
        """
        发送 PushPlus 推送
        
        Args:
            title: 消息标题
            content: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        if not self._enabled or not self._token:
            return False

        def _send():
            try:
                url = "http://www.pushplus.plus/send"
                # PushPlus 要求 content 不能为空，如果为空则使用 title
                actual_content = content if content else title
                payload = {
                    "token": self._token,
                    "title": title,
                    "content": actual_content,
                    "template": "txt"  # 使用纯文本模板，更简洁
                }
                headers = {'Content-Type': 'application/json'}
                
                resp = requests.post(url, data=json.dumps(payload), headers=headers, timeout=5)
                result = resp.json()
                
                if result.get("code") == 200:
                    print(f"[通知] 推送成功: {title}")
                else:
                    print(f"[通知] 推送失败: {result.get('msg')}")
            except Exception as e:
                print(f"[通知] 发送异常: {e}")

        # 异步发送，避免阻塞主线程
        threading.Thread(target=_send, daemon=True).start()
        return True
