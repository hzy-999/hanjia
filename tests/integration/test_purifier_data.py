"""
净化器数据获取集成测试

原文件: verify_fix.py
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.WLW.desktop.core.mijia_adapter import MijiaAdapter


def get_default_auth_path():
    """获取默认认证文件路径"""
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(script_dir, "ui", "WLW", "desktop", ".mijia-api-data", "auth.json")


def test_purifier_data():
    """验证净化器数据获取"""
    print("验证净化器数据获取 (Verifying Purifier Data Fetching)...")
    adapter = MijiaAdapter(auth_path=get_default_auth_path())

    if not adapter.is_available:
        print("Mijia API 不可用 (Not available).")
        return False

    adapter._try_restore_auth()

    devices = adapter.get_devices()
    target_keywords = ["净化器", "Purifier", "air-purifier"]
    found = False

    for d in devices:
        print(f"Device: {d.name}, Model: {d.model}, Category: {d.category}")

        is_purifier_by_name = any(k.lower() in d.name.lower() for k in target_keywords) or \
                              any(k.lower() in d.model.lower() for k in target_keywords)

        if d.category == "purifier" or is_purifier_by_name:
            found = True
            print(f"\n--- 发现净化器 (Testing Device): {d.name} ---")

            status = adapter.get_device_status(d.did, category=d.category)

            print("Status Data (JSON):")
            print(json.dumps(status, ensure_ascii=False, indent=2))

            # Check for critical keys
            results = []
            if "temperature" in status:
                print("✅ 温度 (Temperature) 获取成功")
                results.append(True)
            else:
                print("❌ 温度 (Temperature) 缺失")
                results.append(False)

            if "humidity" in status:
                print("✅ 湿度 (Humidity) 获取成功")
                results.append(True)
            else:
                print("❌ 湿度 (Humidity) 缺失")
                results.append(False)

            if "pm25" in status:
                print("✅ PM2.5 获取成功")
                results.append(True)
            else:
                print("❌ PM2.5 缺失")
                results.append(False)

            return all(results)

    if not found:
        print("未找到净化器设备进行测试 (No purifier found).")
        return None  # No device to test

    return False


if __name__ == "__main__":
    result = test_purifier_data()
    if result is True:
        print("\n✅ 所有测试通过")
    elif result is False:
        print("\n❌ 测试失败")
    else:
        print("\n⚠️ 无设备可测试")
