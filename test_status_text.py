import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.WLW.desktop.core.device import Device, DeviceType

def verify_status_text():
    print("Testing Device.get_status_text()...")
    
    # Case 1: All data present
    d1 = Device(name="Test Purifier", type=DeviceType.MIJIA)
    d1.mark_online()
    d1.data = {
        "pm25": 15, 
        "temperature": 24.5,
        "humidity": 45
    }
    print(f"Case 1 (Full Data): {d1.get_status_text()}")
    
    # Case 2: Partial data
    d2 = Device(name="Test Purifier Partial", type=DeviceType.MIJIA)
    d2.mark_online()
    d2.data = {
        "pm25": 10,
        "is_purifier": True # Logic checks keys
    }
    print(f"Case 2 (Partial Data): {d2.get_status_text()}")
    
    # Case 3: No purifier data (Generic Mijia)
    d3 = Device(name="Generic Switch", type=DeviceType.MIJIA)
    d3.mark_online()
    d3.data = {"power": "on"}
    print(f"Case 3 (Generic Switch): {d3.get_status_text()}")

if __name__ == "__main__":
    verify_status_text()
