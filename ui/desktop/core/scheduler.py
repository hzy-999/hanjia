"""
AquaGuard 韩家家庭智能系统 - 定时任务调度模块

负责自动刷新数据和定时开关灯
"""

import threading
import time
from datetime import datetime
from typing import Callable, Optional


class Scheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # 回调函数
        self._on_refresh: Optional[Callable] = None
        self._on_schedule_action: Optional[Callable[[str], None]] = None
        
        # 配置
        self._refresh_interval_ms = 3000
        self._schedule_enabled = False
        self._on_time = "09:00"
        self._off_time = "23:00"
        
        # 状态跟踪
        self._last_schedule_check = ""
    
    def set_refresh_callback(self, callback: Callable) -> None:
        """设置数据刷新回调"""
        self._on_refresh = callback
    
    def set_schedule_callback(self, callback: Callable[[str], None]) -> None:
        """设置定时操作回调，参数为 'on' 或 'off'"""
        self._on_schedule_action = callback
    
    def set_refresh_interval(self, interval_ms: int) -> None:
        """设置刷新间隔（毫秒）"""
        self._refresh_interval_ms = max(1000, interval_ms)
    
    def set_schedule(self, enabled: bool, on_time: str, off_time: str) -> None:
        """设置定时开关灯"""
        self._schedule_enabled = enabled
        self._on_time = on_time
        self._off_time = off_time
        print(f"[调度] 定时设置: 启用={enabled}, 开={on_time}, 关={off_time}")
    
    def start(self) -> None:
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("[调度] 调度器已启动")
    
    def stop(self) -> None:
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        print("[调度] 调度器已停止")
    
    def _run_loop(self) -> None:
        """调度循环"""
        last_refresh = 0
        
        while self._running:
            current_time = time.time() * 1000  # 毫秒
            
            # 检查数据刷新
            if current_time - last_refresh >= self._refresh_interval_ms:
                last_refresh = current_time
                if self._on_refresh:
                    try:
                        self._on_refresh()
                    except Exception as e:
                        print(f"[调度] 刷新回调出错: {e}")
            
            # 检查定时任务（每分钟检查一次）
            self._check_schedule()
            
            # 短暂休眠
            time.sleep(0.5)
    
    def _check_schedule(self) -> None:
        """检查定时任务"""
        if not self._schedule_enabled:
            return
        
        now = datetime.now()
        current_hm = now.strftime("%H:%M")
        
        # 避免同一分钟重复触发
        if current_hm == self._last_schedule_check:
            return
        
        self._last_schedule_check = current_hm
        
        # 检查开灯时间
        if current_hm == self._on_time:
            print(f"[调度] 定时开灯: {current_hm}")
            if self._on_schedule_action:
                try:
                    self._on_schedule_action("on")
                except Exception as e:
                    print(f"[调度] 定时开灯出错: {e}")
        
        # 检查关灯时间
        elif current_hm == self._off_time:
            print(f"[调度] 定时关灯: {current_hm}")
            if self._on_schedule_action:
                try:
                    self._on_schedule_action("off")
                except Exception as e:
                    print(f"[调度] 定时关灯出错: {e}")


class AlertManager:
    """报警管理器"""
    
    def __init__(self):
        self._on_alert: Optional[Callable[[str, str], None]] = None
        self._alert_history: list = []
        self._max_history = 100
        
        # 报警阈值
        self.min_temp = 20.0
        self.max_temp = 30.0
        self.max_tds = 300
        
        # 防抖动：记录上次报警类型
        self._last_alert_types: set = set()
    
    def set_alert_callback(self, callback: Callable[[str, str], None]) -> None:
        """设置报警回调，参数为 (类型, 消息)"""
        self._on_alert = callback
    
    def set_thresholds(self, min_temp: float, max_temp: float, max_tds: int) -> None:
        """设置报警阈值"""
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.max_tds = max_tds
    
    def check(self, temperature: float, tds_value: int, water_level: int) -> list:
        """
        检查传感器数据，返回报警列表
        
        Returns:
            [(alert_type, message), ...]
        """
        alerts = []
        current_alert_types = set()
        
        # 检查温度
        if temperature > self.max_temp:
            alert_type = "temp_high"
            current_alert_types.add(alert_type)
            if alert_type not in self._last_alert_types:
                alerts.append((alert_type, f"⚠️ 水温过高: {temperature:.1f}°C (上限: {self.max_temp}°C)"))
        
        elif temperature < self.min_temp:
            alert_type = "temp_low"
            current_alert_types.add(alert_type)
            if alert_type not in self._last_alert_types:
                alerts.append((alert_type, f"⚠️ 水温过低: {temperature:.1f}°C (下限: {self.min_temp}°C)"))
        
        # 检查 TDS
        if tds_value > self.max_tds:
            alert_type = "tds_high"
            current_alert_types.add(alert_type)
            if alert_type not in self._last_alert_types:
                alerts.append((alert_type, f"⚠️ 水质较差: TDS={tds_value} ppm (上限: {self.max_tds} ppm)"))
        
        # 检查水位
        if water_level == 0:
            alert_type = "water_low"
            current_alert_types.add(alert_type)
            if alert_type not in self._last_alert_types:
                alerts.append((alert_type, "⚠️ 水位过低，请及时加水！"))
        
        # 更新报警类型
        self._last_alert_types = current_alert_types
        
        # 触发回调并记录历史
        for alert_type, message in alerts:
            self._add_to_history(alert_type, message)
            if self._on_alert:
                try:
                    self._on_alert(alert_type, message)
                except Exception as e:
                    print(f"[报警] 回调出错: {e}")
        
        return alerts
    
    def _add_to_history(self, alert_type: str, message: str) -> None:
        """添加到历史记录"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._alert_history.append({
            "time": timestamp,
            "type": alert_type,
            "message": message
        })
        
        # 限制历史记录数量
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history:]
    
    def get_history(self) -> list:
        """获取报警历史"""
        return self._alert_history.copy()
    
    def clear_history(self) -> None:
        """清除报警历史"""
        self._alert_history.clear()
