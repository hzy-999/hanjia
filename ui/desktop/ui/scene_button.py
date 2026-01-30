"""
AquaGuard UI - 场景按钮组件

模拟 HTML 中的 glass-card button
特点: 圆角大、带图标和文字、悬停效果
"""

import customtkinter as ctk
from typing import Callable, Optional
from .theme import Theme


class SceneButton(ctk.CTkFrame):
    """
    场景模式按钮
    
    Args:
        icon: 按钮图标 (Emoji)
        text: 按钮文字
        icon_color: 图标颜色
        command: 点击回调
    """
    
    def __init__(
        self,
        master,
        icon: str,
        text: str,
        icon_color: str,
        command: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self._command = command
        
        # 样式配置
        self.configure(
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.BUTTON_RADIUS,
            width=120,
            height=44
        )
        
        # 布局
        self.grid_propagate(False) # 固定大小
        
        # 内部容器 (用于居中)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        
        # 图标
        self.icon_label = ctk.CTkLabel(
            self.container,
            text=icon,
            font=(Theme.FONT_EMOJI, 18),
            text_color=icon_color
        )
        self.icon_label.pack(side="left", padx=(0, 6))
        
        # 文字
        self.text_label = ctk.CTkLabel(
            self.container,
            text=text,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.text_label.pack(side="left")
        
        # 事件绑定
        for widget in [self, self.container, self.icon_label, self.text_label]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            
    def _on_click(self, event=None):
        if self._command:
            self._command()
            
    def _on_enter(self, event=None):
        self.configure(fg_color=Theme.BG_CARD_HOVER)
        
    def _on_leave(self, event=None):
        self.configure(fg_color=Theme.BG_CARD)
