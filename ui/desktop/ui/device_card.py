"""
AquaGuard 韩家家庭智能系统 - 设备卡片组件

仿 Glassmorphism 卡片设计 (Henry's Home Style)
"""

import customtkinter as ctk
from typing import Callable, Optional
from .theme import Theme


class DeviceCard(ctk.CTkFrame):
    """
    大尺寸设备卡片
    
    Vertical Layout:
    [Icon Circle]
    [Title]
    [Status Text]
    [Action Button (Placeholder)]
    """
    
    def __init__(
        self,
        master,
        device_id: str,
        device_name: str,
        device_icon: str,
        device_color: str,
        is_online: bool = False,
        is_on: bool = False,
        status_text: str = "离线",
        on_click: Optional[Callable[[str], None]] = None,
        on_long_press: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.device_id = device_id
        self.device_name = device_name
        self.device_icon = device_icon
        self.device_color = device_color
        self._on_click = on_click
        self._on_long_press = on_long_press
        self._is_on = is_on
        
        # 卡片样式 (Large / Glass-like)
        self.configure(
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.CORNER_RADIUS,
            width=160,  # 稍微调小
            height=180, 
            border_width=0,
            bg_color=Theme.BG_SECONDARY  # 适配内容区 BG_SECONDARY
        )
        
        self.grid_propagate(False)
        
        # 内部容器
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
        
        # 1. 图标区 (顶部居中)
        self.icon_frame = ctk.CTkFrame(
            self.inner, 
            width=56,   
            height=56, 
            corner_radius=28, 
            fg_color=Theme.BG_PRIMARY  # 默认浅灰背景
        )
        self.icon_frame.pack(side="top", pady=(5, 5))
        self.icon_frame.pack_propagate(False)
        
        self.icon_label = ctk.CTkLabel(
            self.icon_frame,
            text=device_icon,
            font=(Theme.FONT_EMOJI, 28),
            text_color=Theme.TEXT_MUTED
        )
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # 2. 文字区 (中间居中)
        self.name_label = ctk.CTkLabel(
            self.inner,
            text=device_name,
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            justify="center",
            wraplength=140  # 防止文字过长溢出
        )
        self.name_label.pack(side="top", pady=(5, 2))
        
        self.status_label = ctk.CTkLabel(
            self.inner,
            text=status_text,
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_MUTED,
            justify="center"
        )
        self.status_label.pack(side="top")

        # 绑定事件
        self._bind_events()
        
        # 初始化状态
        self.update_status(is_online, status_text, is_on)
        
    def _bind_events(self):
        # 绑定整个卡片和内部组件
        for w in [self, self.inner, self.icon_frame, self.icon_label, self.name_label, self.status_label]:
            w.bind("<Button-1>", self._handle_click)
            w.bind("<Button-3>", self._handle_right_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _handle_click(self, event=None):
        if self._on_click:
            self._on_click(self.device_id)
            
    def _handle_right_click(self, event=None):
        if self._on_long_press:
            self._on_long_press(self.device_id)

    def _on_enter(self, event=None):
        if not self._is_on:
            self.configure(fg_color=Theme.BG_CARD_HOVER)

    def _on_leave(self, event=None):
        if not self._is_on:
            self.configure(fg_color=Theme.BG_CARD)

    def update_status(self, is_online: bool, status_text: str, is_on: bool = False):
        self._is_on = is_on
        
        # 更新文字
        self.status_label.configure(text=status_text)
        
        if is_online and is_on:
            # Active State: 白底，激活边框
            self.configure(
                fg_color=Theme.BG_CARD,
                border_width=2,
                border_color=Theme.ACCENT_PRIMARY # 使用统一的 Indigo 边框
            )
            
            # 图标背景亮起 (彩色背景 + 白图标)
            self.icon_frame.configure(fg_color=self.device_color) 
            self.icon_label.configure(text_color="#FFFFFF")
            
            self.name_label.configure(text_color=Theme.TEXT_PRIMARY)
            self.status_label.configure(text_color=Theme.ACCENT_PRIMARY)
            
        else:
            # Inactive State (Soft & Minimal)
            self.configure(
                fg_color=Theme.BG_CARD,
                border_width=1,
                border_color=Theme.BORDER_DEFAULT
            )
            
            # 恢复柔和灰色背景
            self.icon_frame.configure(fg_color=Theme.BG_SECONDARY)
            self.icon_label.configure(text_color=Theme.TEXT_MUTED)
            
            self.name_label.configure(text_color=Theme.TEXT_PRIMARY)
            self.status_label.configure(text_color=Theme.TEXT_MUTED)


class AddDeviceCard(ctk.CTkFrame):
    """添加设备卡片 (保持风格一致)"""
    
    def __init__(self, master, on_click=None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_click = on_click
        
        self.configure(
            fg_color="transparent",
            corner_radius=Theme.CORNER_RADIUS,
            border_width=2,
            border_color=Theme.BORDER_DEFAULT,
            width=160,
            height=180,
            bg_color=Theme.BG_SECONDARY  # 适配内容区 BG_SECONDARY
        )
        
        # ... (简化：居中加号)
        label = ctk.CTkLabel(self, text="+", font=("Arial", 40), text_color=Theme.TEXT_MUTED)
        label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.bind("<Button-1>", lambda e: on_click() if on_click else None)
        label.bind("<Button-1>", lambda e: on_click() if on_click else None)
