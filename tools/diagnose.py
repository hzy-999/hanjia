"""
统一诊断工具 - 用于诊断米家设备

用法:
    python -m tools.diagnose --type mijia     # 诊断双键/三键开关等设备
    python -m tools.diagnose --type purifier  # 诊断净化器设备
    python -m tools.diagnose --type all       # 诊断所有设备
"""
import sys
import os
import json
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.WLW.desktop.core.mijia_adapter import MijiaAdapter


# 设备类型关键词配置
DEVICE_KEYWORDS = {
    "mijia": ["双键", "三键", "Double", "Triple"],
    "purifier": ["净化器", "Purifier", "air-purifier"],
}


def get_default_auth_path():
    """获取默认认证文件路径"""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(script_dir, "ui", "WLW", "desktop", ".mijia-api-data", "auth.json")


def is_target_device(device, keywords: list) -> bool:
    """检查设备是否匹配目标关键词"""
    name_lower = device.name.lower()
    model_lower = device.model.lower()
    for k in keywords:
        if k.lower() in name_lower or k.lower() in model_lower:
            return True
    return False


def diagnose_device(adapter, device):
    """诊断单个设备，打印所有属性"""
    print(f"\n--- 设备: {device.name} ---")
    print(f"  DID: {device.did}")
    print(f"  Model: {device.model}")
    print(f"  Category: {device.category}")

    print("  正在检查属性...")
    mijia_device = adapter.get_mijia_device(device.did)
    if mijia_device:
        try:
            print(f"  可用属性: {list(mijia_device.prop_list.keys())}")

            for p in mijia_device.prop_list:
                try:
                    val = mijia_device.get(p)
                    print(f"    {p}: {val}")
                except Exception as e:
                    print(f"    {p}: <错误: {e}>")
        except Exception as e:
            print(f"  检查设备时出错: {e}")


def diagnose(device_type: str = "all", auth_path: str = None):
    """
    诊断米家设备

    Args:
        device_type: 设备类型 ("mijia", "purifier", "all")
        auth_path: 认证文件路径
    """
    if auth_path is None:
        auth_path = get_default_auth_path()

    print(f"正在初始化米家适配器...")
    print(f"认证文件: {auth_path}")
    adapter = MijiaAdapter(auth_path=auth_path)

    if not adapter.is_available:
        print("米家 API 不可用。")
        return

    # 尝试恢复认证
    adapter._try_restore_auth()

    if not adapter.is_logged_in:
        print("未登录。请先在应用中登录。")
        return

    print("正在获取设备列表...")
    devices = adapter.get_devices()
    print(f"找到 {len(devices)} 个设备。")

    # 确定要匹配的关键词
    if device_type == "all":
        keywords = []
        for kw_list in DEVICE_KEYWORDS.values():
            keywords.extend(kw_list)
    else:
        keywords = DEVICE_KEYWORDS.get(device_type, [])

    found_count = 0
    for device in devices:
        # 如果是 "all" 类型或者设备匹配关键词
        if device_type == "all" or is_target_device(device, keywords):
            diagnose_device(adapter, device)
            found_count += 1
        elif device_type == "all":
            # 对于 "all" 类型，只打印基本信息
            print(f"\n设备: {device.name} (Model: {device.model}, Category: {device.category})")

    if found_count == 0 and device_type != "all":
        print(f"\n未找到匹配 '{device_type}' 类型的设备。")


def main():
    parser = argparse.ArgumentParser(description="米家设备诊断工具")
    parser.add_argument(
        "--type", "-t",
        choices=["mijia", "purifier", "all"],
        default="all",
        help="要诊断的设备类型 (默认: all)"
    )
    parser.add_argument(
        "--auth", "-a",
        default=None,
        help="认证文件路径"
    )

    args = parser.parse_args()
    diagnose(device_type=args.type, auth_path=args.auth)


if __name__ == "__main__":
    main()
