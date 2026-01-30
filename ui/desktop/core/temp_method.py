
    def control_mijia_device(self, device_id: str, action: str, params: Dict[str, Any]) -> bool:
        """
        控制米家设备
        
        Args:
            device_id: 设备 ID
            action: 动作名称 (set_power, set_mode, etc.)
            params: 参数字典
            
        Returns:
            是否成功
        """
        device = self.get_device(device_id)
        if not device or not device.is_mijia or not self._mijia_adapter:
            return False
            
        if action == "set_power":
            power_on = params.get("power", False)
            # 尝试设置 'on' 属性 (大多数设备使用这个)
            # 注意：某些设备可能使用不同的属性名，如 'power', 'switch' 等
            # 这里依赖 mijiaAPI 的统一或者需要更多映射逻辑
            
            # 首先尝试 set 'on'
            if self._mijia_adapter.set_device_prop(device.did, "on", power_on):
                return True
                
            # 如果失败，对于开关插座，可能需要其他方式，暂且只支持标准 spec
            print(f"[设备管理] 无法设置设备 {device.name} 的电源状态")
            return False
            
        return False
