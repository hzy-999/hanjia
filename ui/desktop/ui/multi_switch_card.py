"""
AquaGuard 韩家家庭智能系统 - 多键开关卡片组件

将多键开关显示为一个卡片，点击进入详情页控制
"""

import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from .theme import Theme


class MultiSwitchCard(ctk.CTkFrame):
    """
    多键开关卡片（首页简化版）
    
    显示多键开关的基本信息，点击进入详情页控制各个按键
    """
    
    def __init__(
        self,
        master,
        device_id: str,  # 主设备 ID (real_did)
        device_name: str,  # 显示名称
        switches: List[Dict],  # 子开关列表 [{id, name, is_on}, ...]
        device_icon: str = "🔌",
        device_color: str = "#888888",
        is_online: bool = False,
        on_click: Optional[Callable[[str, List[Dict]], None]] = None,  # (device_id, switches)
        on_long_press: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.device_id = device_id
        self.device_name = device_name
        self.switches = switches
        self.device_icon = device_icon
        self.device_color = device_color
        self._on_click = on_click
        self._on_long_press = on_long_press
        self._is_online = is_online
        
        # 计算开启的开关数量
        self._on_count = sum(1 for s in switches if s.get("is_on", False))
        
        # 卡片样式
        self.configure(
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.CORNER_RADIUS,
            width=160,  # 稍微调小
            height=180,
            border_width=0,
            bg_color=Theme.BG_SECONDARY
        )
        
        self.grid_propagate(False)
        
        # 内部容器
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
        
        # 1. 图标区 (顶部居中)
        self.icon_frame = ctk.CTkFrame(
            self.inner,
            width=56,   # 稍微调小图标
            height=56,
            corner_radius=28,
            fg_color=Theme.BG_PRIMARY
        )
        self.icon_frame.pack(side="top", pady=(5, 5))
        self.icon_frame.pack_propagate(False)
        
        self.icon_label = ctk.CTkLabel(
            self.icon_frame,
            text=device_icon,
            font=(Theme.FONT_EMOJI, 28),
            text_color=device_color if is_online else Theme.TEXT_MUTED
        )
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # 2. 设备名
        self.name_label = ctk.CTkLabel(
            self.inner,
            text=device_name,
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            justify="center",
            wraplength=140
        )
        self.name_label.pack(side="top", pady=(5, 2))
        
        # 3. 状态文字 (显示开关数量和开启状态)
        status_text = self._get_status_text()
        self.status_label = ctk.CTkLabel(
            self.inner,
            text=status_text,
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.ACCENT_PRIMARY if self._on_count > 0 else Theme.TEXT_MUTED,
            justify="center"
        )
        self.status_label.pack(side="top")

        
        # 绑定事件
        self._bind_events()
        
        # 设置边框表示有开关打开
        if is_online and self._on_count > 0:
            self.configure(border_width=2, border_color=Theme.BORDER_ACTIVE)
            self.icon_frame.configure(fg_color=device_color)
            self.icon_label.configure(text_color="#FFFFFF")
        else:
            self.configure(border_width=0)
            self.icon_frame.configure(fg_color=Theme.BG_PRIMARY)
            self.icon_label.configure(text_color=Theme.TEXT_MUTED)
    
    def _get_status_text(self) -> str:
        """获取状态文字"""
        if not self._is_online:
            return "离线"
        total = len(self.switches)
        if self._on_count == 0:
            return f"全部关闭 ({total}键)"
        elif self._on_count == total:
            return f"全部打开 ({total}键)"
        else:
            return f"{self._on_count}/{total} 个打开"
    
    def _bind_events(self):
        """绑定点击事件"""
        for w in [self, self.inner, self.icon_frame, self.icon_label, 
                  self.name_label, self.status_label]:
            w.bind("<Button-1>", self._handle_click)
            w.bind("<Button-3>", self._handle_right_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
    
    def _handle_click(self, event=None):
        """点击进入详情"""
        if self._on_click:
            self._on_click(self.device_id, self.switches)
    
    def _handle_right_click(self, event=None):
        """右键菜单"""
        if self._on_long_press:
            self._on_long_press(self.device_id)
    
    def _on_enter(self, event=None):
        self.configure(fg_color=Theme.BG_CARD_HOVER)
    
    def _on_leave(self, event=None):
        self.configure(fg_color=Theme.BG_CARD)
    
    def update_switch_state(self, switch_id: str, is_on: bool):
        """更新开关状态"""
        for switch in self.switches:
            if switch.get("id") == switch_id:
                switch["is_on"] = is_on
                break
        
        # 重新计算开启数量
        self._on_count = sum(1 for s in self.switches if s.get("is_on", False))
        
        # 更新状态显示
        self.status_label.configure(
            text=self._get_status_text(),
            text_color=Theme.ACCENT_PRIMARY if self._on_count > 0 else Theme.TEXT_MUTED
        )
        
        # 更新边框和图标 (Premium Style)
        if self._is_online and self._on_count > 0:
            self.configure(border_width=2, border_color=Theme.ACCENT_PRIMARY)
            self.icon_frame.configure(fg_color=self.device_color)
            self.icon_label.configure(text_color="#FFFFFF")
        else:
            self.configure(border_width=1, border_color=Theme.BORDER_DEFAULT)
            self.icon_frame.configure(fg_color=Theme.BG_SECONDARY)
            self.icon_label.configure(text_color=Theme.TEXT_MUTED)
    
    def update_online_status(self, is_online: bool):
        """更新在线状态"""
        self._is_online = is_online
        
        # 更新边框和图标 (复用逻辑)
        if self._is_online and self._on_count > 0:
            self.configure(border_width=2, border_color=Theme.ACCENT_PRIMARY)
            self.icon_frame.configure(fg_color=self.device_color)
            self.icon_label.configure(text_color="#FFFFFF")
        else:
            self.configure(border_width=1, border_color=Theme.BORDER_DEFAULT)
            self.icon_frame.configure(fg_color=Theme.BG_SECONDARY)
            self.icon_label.configure(text_color=Theme.TEXT_MUTED)
        
        self.status_label.configure(
            text=self._get_status_text(),
            text_color=Theme.ACCENT_PRIMARY if self._on_count > 0 else Theme.TEXT_MUTED
        )
    
    def get_switch_ids(self) -> List[str]:
        """获取所有子开关 ID"""
        return [s.get("id") for s in self.switches if s.get("id")]
