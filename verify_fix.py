import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.WLW.desktop.core.mijia_adapter import MijiaAdapter

def verify():
    print("验证净化器数据获取 (Verifying Purifier Data Fetching)...")
    adapter = MijiaAdapter(auth_path=r"d:\Users\18126\Desktop\mijia-api-main\ui\WLW\desktop\.mijia-api-data\auth.json")
    
    if not adapter.is_available:
        print("Mijia API 不可用 (Not available).")
        return

    adapter._try_restore_auth()
    
    devices = adapter.get_devices()
    target_keywords = ["净化器", "Purifier", "air-purifier"]
    
    for d in devices:
        print(f"Device: {d.name}, Model: {d.model}, Category: {d.category}")
        
        target_keywords = ["净化器", "Purifier", "air-purifier"]
        is_purifier_by_name = any(k.lower() in d.name.lower() for k in target_keywords) or \
                              any(k.lower() in d.model.lower() for k in target_keywords)
        
        if d.category == "purifier" or is_purifier_by_name:
            found = True
            print(f"\n--- 发现净化器 (Testing Device): {d.name} ---")
            
            # Use the new logic
            # Explicitly force category if needed for test, but get_device_status uses internal cache
            # We pass category to get_device_status just in case, or rely on internal logic
            # The method signature is get_device_status(did, category="other")
            # But the method itself tries to look up category from cache
            
            status = adapter.get_device_status(d.did, category=d.category)

            print("Status Data (JSON):")
            print(json.dumps(status, ensure_ascii=False, indent=2))
            
            # Check for critical keys
            if "temperature" in status:
                print("✅ 温度 (Temperature) 获取成功")
            else:
                print("❌ 温度 (Temperature) 缺失")
                
            if "humidity" in status:
                print("✅ 湿度 (Humidity) 获取成功")
            else:
                 print("❌ 湿度 (Humidity) 缺失")
                 
            if "pm25" in status:
                print("✅ PM2.5 获取成功")
            else:
                 print("❌ PM2.5 缺失")
            break

    if not found:
        print("未找到净化器设备进行测试 (No purifier found).")

if __name__ == "__main__":
    verify()
