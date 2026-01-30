"""
AquaGuard 状态变更记录面板

显示设备状态变更的历史记录，支持已读/未读状态
"""

import customtkinter as ctk
from typing import Optional, Callable, List
from .theme import Theme


class NotificationLogPanel(ctk.CTkToplevel):
    """
    状态变更记录弹出面板
    """
    
    def __init__(
        self,
        master,
        logs: List[dict] = None,
        on_mark_read: Optional[Callable[[str], None]] = None,
        on_mark_all_read: Optional[Callable[[], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.logs = logs or []
        self._on_mark_read = on_mark_read
        self._on_mark_all_read = on_mark_all_read
        self._on_clear = on_clear
        self._on_close = on_close
        
        # 窗口配置
        self.title("设备状态变更记录")
        self.geometry("450x500")
        self.minsize(400, 400)
        self.configure(fg_color=Theme.BG_PRIMARY)
        
        # 置顶显示
        self.transient(master)
        self.grab_set()
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        
        self._create_ui()
        
        # 窗口居中显示
        self._center_window()
    
    def _create_ui(self):
        # 顶部标题栏
        self.header = ctk.CTkFrame(self, fg_color=Theme.BG_SECONDARY, height=60)
        self.header.pack(fill="x", padx=10, pady=10)
        self.header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            self.header,
            text="🔔 状态变更记录",
            font=(Theme.FONT_FAMILY, 18, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.pack(side="left", padx=15, pady=15)
        
        # 未读数量标签（保存引用以便更新）
        self.unread_badge = None
        self._update_badge()
        
        # 操作按钮区
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        mark_all_btn = ctk.CTkButton(
            btn_frame,
            text="全部已读",
            width=100,
            height=32,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            font=(Theme.FONT_FAMILY, 12),
            command=self._on_mark_all_click
        )
        mark_all_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="清空记录",
            width=100,
            height=32,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.ACCENT_ERROR,
            text_color=Theme.TEXT_SECONDARY,
            font=(Theme.FONT_FAMILY, 12),
            command=self._on_clear_click
        )
        clear_btn.pack(side="left", padx=5)
        
        # 消息列表（滚动）
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=Theme.BG_SECONDARY,
            corner_radius=10
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 渲染消息列表
        self._render_logs()
    
    def _render_logs(self):
        # 清除现有内容
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        if not self.logs:
            empty_label = ctk.CTkLabel(
                self.scroll_frame,
                text="暂无状态变更记录",
                font=(Theme.FONT_FAMILY, 14),
                text_color=Theme.TEXT_MUTED
            )
            empty_label.pack(pady=50)
            return
        
        # 按时间倒序显示（最新的在前）
        sorted_logs = sorted(self.logs, key=lambda x: x.get("timestamp", ""), reverse=True)
        
        for log in sorted_logs:
            self._create_log_item(log)
    
    def _create_log_item(self, log: dict):
        is_read = log.get("read", False)
        
        # 消息项容器
        item_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=Theme.BG_CARD if is_read else Theme.BG_CARD_HOVER,
            corner_radius=8,
            height=70
        )
        item_frame.pack(fill="x", pady=5, padx=5)
        item_frame.pack_propagate(False)
        
        # 左侧内容
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # 设备名称 + 动作
        device_name = log.get("device_name", "未知设备")
        action = log.get("action", "状态变更")
        
        title_text = f"{device_name} 已{action}"
        title_color = Theme.TEXT_PRIMARY if not is_read else Theme.TEXT_SECONDARY
        
        title_label = ctk.CTkLabel(
            content_frame,
            text=title_text,
            font=(Theme.FONT_FAMILY, 14, "bold" if not is_read else "normal"),
            text_color=title_color,
            anchor="w"
        )
        title_label.pack(fill="x")
        
        # 时间戳
        timestamp = log.get("timestamp", "")
        time_label = ctk.CTkLabel(
            content_frame,
            text=timestamp,
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_MUTED,
            anchor="w"
        )
        time_label.pack(fill="x")
        
        # 右侧：未读标记
        if not is_read:
            unread_dot = ctk.CTkLabel(
                item_frame,
                text="●",
                font=(Theme.FONT_FAMILY, 16),
                text_color=Theme.ACCENT_ERROR,
                width=30
            )
            unread_dot.pack(side="right", padx=10)
            
            # 点击标记已读
            item_frame.bind("<Button-1>", lambda e, lid=log.get("id"): self._on_item_click(lid))
            content_frame.bind("<Button-1>", lambda e, lid=log.get("id"): self._on_item_click(lid))
            title_label.bind("<Button-1>", lambda e, lid=log.get("id"): self._on_item_click(lid))
            time_label.bind("<Button-1>", lambda e, lid=log.get("id"): self._on_item_click(lid))
    
    def _on_item_click(self, log_id: str):
        """点击消息项标记已读"""
        if self._on_mark_read:
            self._on_mark_read(log_id)
        
        # 更新本地状态并刷新显示
        for log in self.logs:
            if log.get("id") == log_id:
                log["read"] = True
                break
        self._render_logs()
    
    def _on_mark_all_click(self):
        """全部标记已读"""
        if self._on_mark_all_read:
            self._on_mark_all_read()
        
        for log in self.logs:
            log["read"] = True
        self._refresh_ui()
    
    def _on_clear_click(self):
        """清空记录"""
        if self._on_clear:
            self._on_clear()
        
        self.logs = []
        self._refresh_ui()
    
    def _refresh_ui(self):
        """刷新UI（只更新未读标签和日志列表）"""
        self._update_badge()
        self._render_logs()
    
    def _update_badge(self):
        """更新未读数量标签"""
        # 销毁旧的badge
        if self.unread_badge:
            self.unread_badge.destroy()
            self.unread_badge = None
        
        # 计算未读数量
        unread_count = sum(1 for log in self.logs if not log.get("read", False))
        
        # 如果有未读，创建新的badge
        if unread_count > 0:
            self.unread_badge = ctk.CTkLabel(
                self.header,
                text=f"{unread_count} 未读",
                font=(Theme.FONT_FAMILY, 12),
                text_color=Theme.ACCENT_ERROR,
                fg_color=Theme.BG_CARD,
                corner_radius=10,
                width=60,
                height=24
            )
            self.unread_badge.pack(side="left", padx=5)
    
    def _handle_close(self):
        """关闭窗口"""
        if self._on_close:
            self._on_close()
        self.destroy()
    
    def update_logs(self, logs: List[dict]):
        """更新日志列表"""
        self.logs = logs
        self._render_logs()
    
    def _center_window(self):
        """将窗口居中显示在主窗口上"""
        self.update_idletasks()
        
        # 获取窗口尺寸
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # 获取主窗口位置和尺寸
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        
        # 计算居中位置
        x = master_x + (master_width - window_width) // 2
        y = master_y + (master_height - window_height) // 2
        
        # 设置窗口位置
        self.geometry(f"+{x}+{y}")
