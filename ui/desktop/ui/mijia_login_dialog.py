"""
AquaGuard 韩家家庭智能系统 - 米家登录对话框

提供二维码扫码登录米家账户的功能
"""

import customtkinter as ctk
from typing import Optional, Callable
import threading

from .theme import Theme

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class MijiaLoginDialog(ctk.CTkToplevel):
    """
    米家登录对话框
    
    显示二维码供用户使用米家APP扫码登录
    """
    
    def __init__(
        self,
        master,
        mijia_adapter,
        on_login_success: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None
    ):
        """
        初始化登录对话框
        
        Args:
            master: 父窗口
            mijia_adapter: MijiaAdapter 实例
            on_login_success: 登录成功回调
            on_close: 对话框关闭回调
        """
        super().__init__(master)
        
        self.mijia_adapter = mijia_adapter
        self.on_login_success = on_login_success
        self.on_close = on_close
        self._qr_image = None
        self._polling = False
        
        # 窗口设置
        self.title("绑定米家账户")
        self.geometry("400x500")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_PRIMARY)
        
        # 设置为模态
        self.transient(master)
        self.grab_set()
        
        # 创建 UI
        self._create_ui()
        
        # 开始获取二维码
        self.after(100, self._load_qr_code)
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_dialog_close)
    
    def _create_ui(self) -> None:
        """创建 UI 组件"""
        # 主框架
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text="📱 绑定米家账户",
            font=(Theme.FONT_FAMILY, 20, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title_label.pack(pady=(0, 10))
        
        # 说明文字
        desc_label = ctk.CTkLabel(
            main_frame,
            text="请使用米家APP扫描下方二维码登录",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY
        )
        desc_label.pack(pady=(0, 20))
        
        # 二维码容器
        self.qr_frame = ctk.CTkFrame(
            main_frame,
            fg_color=Theme.BG_CARD,
            corner_radius=20,
            width=280,
            height=280
        )
        self.qr_frame.pack(pady=10)
        self.qr_frame.pack_propagate(False)
        
        # 状态标签 (初始显示加载中)
        self.status_label = ctk.CTkLabel(
            self.qr_frame,
            text="⏳ 正在获取二维码...",
            font=(Theme.FONT_FAMILY, 14),
            text_color=Theme.TEXT_SECONDARY
        )
        self.status_label.pack(expand=True)
        
        # 二维码图片标签 (稍后显示)
        self.qr_label = None
        
        # 提示信息
        tip_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tip_frame.pack(fill="x", pady=20)
        
        tips = [
            "1. 打开手机米家APP",
            "2. 点击右上角 '+' → 扫一扫",
            "3. 扫描上方二维码完成登录"
        ]
        
        for tip in tips:
            ctk.CTkLabel(
                tip_frame,
                text=tip,
                font=(Theme.FONT_FAMILY, 11),
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w", pady=2)
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        # 刷新按钮
        self.refresh_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 刷新二维码",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.BUTTON_RADIUS,
            command=self._load_qr_code
        )
        self.refresh_btn.pack(side="left", expand=True, padx=5)
        
        # 取消按钮
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.ACCENT_ERROR,
            hover_color="#DC2626",
            text_color="#FFFFFF",
            corner_radius=Theme.BUTTON_RADIUS,
            command=self._on_dialog_close
        )
        cancel_btn.pack(side="right", expand=True, padx=5)
    
    def _load_qr_code(self) -> None:
        """加载二维码"""
        self.status_label.configure(text="⏳ 正在获取二维码...")
        self.refresh_btn.configure(state="disabled")
        
        # 清除旧的二维码图片
        if self.qr_label:
            self.qr_label.destroy()
            self.qr_label = None
        
        # 在后台线程获取二维码
        def fetch_qr():
            try:
                qr_image = self.mijia_adapter.get_qr_image()
                
                if qr_image is None:
                    # 可能已经登录
                    if self.mijia_adapter.is_logged_in:
                        self.after(0, lambda: self._on_login_complete(True, "已登录"))
                    else:
                        self.after(0, lambda: self._show_error("无法获取二维码"))
                    return
                
                # 转换为 CTk 可用的格式
                if PIL_AVAILABLE:
                    # 调整大小
                    qr_image = qr_image.resize((240, 240), Image.Resampling.LANCZOS)
                    self._qr_image = qr_image
                    self.after(0, self._display_qr_image)
                    
                    # 开始轮询登录状态
                    self.mijia_adapter.set_login_callback(self._on_login_callback)
                    self.mijia_adapter.start_login_polling()
                else:
                    self.after(0, lambda: self._show_error("缺少 Pillow 库"))
                    
            except Exception as e:
                self.after(0, lambda: self._show_error(f"获取失败: {e}"))
        
        threading.Thread(target=fetch_qr, daemon=True).start()
    
    def _display_qr_image(self) -> None:
        """显示二维码图片"""
        if not self._qr_image or not PIL_AVAILABLE:
            return
        
        self.status_label.pack_forget()
        
        # 创建图片标签
        photo = ImageTk.PhotoImage(self._qr_image)
        self.qr_label = ctk.CTkLabel(
            self.qr_frame,
            text="",
            image=photo
        )
        self.qr_label.image = photo  # 保持引用
        self.qr_label.pack(expand=True)
        
        self.refresh_btn.configure(state="normal")
        self._polling = True
    
    def _show_error(self, message: str) -> None:
        """显示错误信息"""
        self.status_label.configure(
            text=f"❌ {message}",
            text_color=Theme.ACCENT_ERROR
        )
        self.status_label.pack(expand=True)
        self.refresh_btn.configure(state="normal")
    
    def _on_login_callback(self, success: bool, message: str) -> None:
        """登录回调 (从后台线程调用)"""
        self.after(0, lambda: self._on_login_complete(success, message))
    
    def _on_login_complete(self, success: bool, message: str) -> None:
        """登录完成处理"""
        self._polling = False
        
        if success:
            # 显示成功信息
            if self.qr_label:
                self.qr_label.destroy()
            self.status_label.configure(
                text="✅ 登录成功！",
                text_color=Theme.ACCENT_SUCCESS
            )
            self.status_label.pack(expand=True)
            
            # 延迟关闭并触发回调
            if self.on_login_success:
                self.after(1000, self.on_login_success)
            self.after(1500, self.destroy)
        else:
            self._show_error(message)
    
    def _on_dialog_close(self) -> None:
        """对话框关闭处理"""
        self._polling = False
        if self.on_close:
            self.on_close()
        self.destroy()


class MijiaSettingsPanel(ctk.CTkFrame):
    """
    米家设置面板
    
    显示米家绑定状态和操作按钮
    """
    
    def __init__(
        self,
        master,
        device_manager,
        on_bind: Optional[Callable[[], None]] = None,
        on_unbind: Optional[Callable[[], None]] = None,
        on_sync: Optional[Callable[[], None]] = None
    ):
        super().__init__(master, fg_color="transparent")
        
        self.device_manager = device_manager
        self.on_bind = on_bind
        self.on_unbind = on_unbind
        self.on_sync = on_sync
        
        self._create_ui()
        self._update_status()
    
    def _create_ui(self) -> None:
        """创建 UI"""
        # 标题
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="📱 米家智能设备",
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")
        
        # 状态指示器
        self.status_indicator = ctk.CTkLabel(
            title_frame,
            text="",
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_SECONDARY
        )
        self.status_indicator.pack(side="right")
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        # 绑定/解绑按钮
        self.bind_btn = ctk.CTkButton(
            btn_frame,
            text="绑定账户",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.ACCENT_PRIMARY,
            hover_color=Theme.ACCENT_HOVER,
            corner_radius=Theme.BUTTON_RADIUS,
            command=self._on_bind_click
        )
        self.bind_btn.pack(side="left", padx=(0, 5))
        
        # 同步设备按钮
        self.sync_btn = ctk.CTkButton(
            btn_frame,
            text="同步设备",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.BUTTON_RADIUS,
            command=self._on_sync_click
        )
        self.sync_btn.pack(side="left")
    
    def _update_status(self) -> None:
        """更新状态显示"""
        if not self.device_manager.is_mijia_available():
            self.status_indicator.configure(
                text="⚠️ 未安装 mijiaAPI",
                text_color=Theme.ACCENT_WARNING
            )
            self.bind_btn.configure(state="disabled")
            self.sync_btn.configure(state="disabled")
            return
        
        if self.device_manager.is_mijia_logged_in():
            self.status_indicator.configure(
                text="🟢 已绑定",
                text_color=Theme.ACCENT_SUCCESS
            )
            self.bind_btn.configure(text="解绑账户")
            self.sync_btn.configure(state="normal")
        else:
            self.status_indicator.configure(
                text="⚪ 未绑定",
                text_color=Theme.TEXT_MUTED
            )
            self.bind_btn.configure(text="绑定账户")
            self.sync_btn.configure(state="disabled")
    
    def _on_bind_click(self) -> None:
        """绑定/解绑按钮点击"""
        if self.device_manager.is_mijia_logged_in():
            # 解绑
            if self.on_unbind:
                self.on_unbind()
        else:
            # 绑定
            if self.on_bind:
                self.on_bind()
    
    def _on_sync_click(self) -> None:
        """同步按钮点击"""
        if self.on_sync:
            self.on_sync()
    
    def refresh(self) -> None:
        """刷新状态"""
        self._update_status()
