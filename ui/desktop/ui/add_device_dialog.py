"""
AquaGuard 韩家家庭智能系统 - 添加设备对话框

用于添加新设备的弹窗
"""

import customtkinter as ctk
from typing import Callable, Optional
from .theme import Theme


class AddDeviceDialog(ctk.CTkToplevel):
    """
    添加设备对话框
    
    让用户输入设备名称、类型和 IP 地址
    """
    
    def __init__(
        self,
        master,
        on_save: Optional[Callable[[str, str, str], None]] = None,
        **kwargs
    ):
        """
        初始化对话框
        
        Args:
            master: 父窗口
            on_save: 保存回调，参数为 (name, type, ip)
        """
        super().__init__(master, **kwargs)
        
        self._on_save = on_save
        
        # 窗口配置
        self.title("添加设备")
        self.geometry("400x380")
        self.resizable(False, False)
        
        self.configure(fg_color=Theme.BG_PRIMARY)
        
        # 居中显示
        self.transient(master)
        self.grab_set()
        
        # 主容器
        container = ctk.CTkFrame(
            self, 
            fg_color=Theme.BG_CARD, 
            corner_radius=Theme.CORNER_RADIUS
        )
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title = ctk.CTkLabel(
            container,
            text="添加新设备",
            font=(Theme.FONT_FAMILY, 20, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.pack(pady=(20, 20))
        
        # 设备类型
        type_label = ctk.CTkLabel(
            container,
            text="设备类型",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        type_label.pack(fill="x", padx=20)
        
        self.type_var = ctk.StringVar(value="light")
        self.type_menu = ctk.CTkOptionMenu(
            container,
            values=["light", "sensor"],
            variable=self.type_var,
            fg_color=Theme.BG_PRIMARY,
            button_color=Theme.ACCENT_PRIMARY,
            button_hover_color=Theme.ACCENT_HOVER,
            dropdown_fg_color=Theme.BG_CARD,
            dropdown_hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            font=(Theme.FONT_FAMILY, 12),
            width=320 
        )
        self.type_menu.pack(fill="x", padx=20, pady=(5, 15))
        
        # 设备名称
        name_label = ctk.CTkLabel(
            container,
            text="设备名称",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        name_label.pack(fill="x", padx=20)
        
        self.name_entry = ctk.CTkEntry(
            container,
            placeholder_text="例如：卧室灯",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.BG_PRIMARY,
            border_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            height=40
        )
        self.name_entry.pack(fill="x", padx=20, pady=(5, 15))
        
        # IP 地址
        ip_label = ctk.CTkLabel(
            container,
            text="IP 地址",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        ip_label.pack(fill="x", padx=20)
        
        self.ip_entry = ctk.CTkEntry(
            container,
            placeholder_text="例如：192.168.1.100",
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.BG_PRIMARY,
            border_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            height=40
        )
        self.ip_entry.pack(fill="x", padx=20, pady=(5, 20))
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # 取消按钮
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            fg_color=Theme.BG_PRIMARY,
            text_color=Theme.TEXT_PRIMARY,
            hover_color=Theme.BG_CARD_HOVER,
            font=(Theme.FONT_FAMILY, 12),
            width=100,
            command=self.destroy
        )
        cancel_btn.pack(side="left", expand=True, padx=5)
        
        # 保存按钮
        save_btn = ctk.CTkButton(
            btn_frame,
            text="添加",
            fg_color=Theme.ACCENT_PRIMARY,
            text_color="#FFFFFF",
            hover_color=Theme.ACCENT_HOVER,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            width=100,
            command=self._on_save_click
        )
        save_btn.pack(side="right", expand=True, padx=5)
    
    def _on_save_click(self) -> None:
        """保存按钮点击"""
        name = self.name_entry.get().strip()
        # 使用 type_menu.get() 更安全，防止 StringVar 丢失
        device_type = self.type_menu.get()
        ip = self.ip_entry.get().strip()
        
        print(f"[UI] 尝试保存设备: {name}, 类型: {device_type}, IP: {ip}")
        
        # 简单验证
        if not name:
            self.name_entry.configure(border_color=Theme.ACCENT_ERROR)
            return
        
        if not ip:
            self.ip_entry.configure(border_color=Theme.ACCENT_ERROR)
            return
        
        try:
            if self._on_save:
                self._on_save(name, device_type, ip)
            self.destroy()
        except Exception as e:
            print(f"[UI] 保存设备出错: {e}")
            import traceback
            traceback.print_exc()


class EditDeviceDialog(ctk.CTkToplevel):
    """
    编辑设备对话框
    
    让用户修改设备名称和 IP 地址
    """
    
    def __init__(
        self,
        master,
        device_id: str,
        device_name: str,
        device_ip: str,
        on_save: Optional[Callable[[str, str, str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """
        初始化对话框
        
        Args:
            master: 父窗口
            device_id: 设备 ID
            device_name: 当前名称
            device_ip: 当前 IP
            on_save: 保存回调，参数为 (device_id, name, ip)
            on_delete: 删除回调，参数为 device_id
        """
        super().__init__(master, **kwargs)
        
        self._device_id = device_id
        self._on_save = on_save
        self._on_delete = on_delete
        
        # 窗口配置
        self.title("编辑设备")
        self.geometry("400x350")
        self.resizable(False, False)
        
        self.configure(fg_color=Theme.BG_PRIMARY)
        
        # 居中显示
        self.transient(master)
        self.grab_set()
        
        # 主容器
        container = ctk.CTkFrame(
            self, 
            fg_color=Theme.BG_CARD, 
            corner_radius=Theme.CORNER_RADIUS
        )
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title = ctk.CTkLabel(
            container,
            text="编辑设备",
            font=(Theme.FONT_FAMILY, 20, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.pack(pady=(20, 20))
        
        # 设备名称
        name_label = ctk.CTkLabel(
            container,
            text="设备名称",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        name_label.pack(fill="x", padx=20)
        
        self.name_entry = ctk.CTkEntry(
            container,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.BG_PRIMARY,
            border_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            height=40
        )
        self.name_entry.insert(0, device_name)
        self.name_entry.pack(fill="x", padx=20, pady=(5, 15))
        
        # IP 地址
        ip_label = ctk.CTkLabel(
            container,
            text="IP 地址",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        )
        ip_label.pack(fill="x", padx=20)
        
        self.ip_entry = ctk.CTkEntry(
            container,
            font=(Theme.FONT_FAMILY, 12),
            fg_color=Theme.BG_PRIMARY,
            border_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            height=40
        )
        self.ip_entry.insert(0, device_ip)
        self.ip_entry.pack(fill="x", padx=20, pady=(5, 20))
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # 删除按钮
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="删除",
            fg_color=Theme.ACCENT_ERROR,
            hover_color="#CC0000",
            text_color="#FFFFFF",
            font=(Theme.FONT_FAMILY, 12),
            width=80,
            command=self._on_delete_click
        )
        delete_btn.pack(side="left", padx=5)
        
        # 取消按钮
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            fg_color=Theme.BG_PRIMARY,
            text_color=Theme.TEXT_PRIMARY,
            hover_color=Theme.BG_CARD_HOVER,
            font=(Theme.FONT_FAMILY, 12),
            width=80,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=5)
        
        # 保存按钮
        save_btn = ctk.CTkButton(
            btn_frame,
            text="保存",
            fg_color=Theme.ACCENT_PRIMARY,
            text_color="#FFFFFF",
            hover_color=Theme.ACCENT_HOVER,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            width=80,
            command=self._on_save_click
        )
        save_btn.pack(side="right", padx=5)
    
    def _on_save_click(self) -> None:
        """保存按钮点击"""
        name = self.name_entry.get().strip()
        ip = self.ip_entry.get().strip()
        
        if not name or not ip:
            return
        
        if self._on_save:
            self._on_save(self._device_id, name, ip)
        
        self.destroy()
    
    def _on_delete_click(self) -> None:
        """删除按钮点击"""
        if self._on_delete:
            self._on_delete(self._device_id)
        
        self.destroy()
