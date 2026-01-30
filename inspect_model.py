import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mijiaAPI.devices import get_device_info

def inspect():
    model = "huca.switch.dh3"
    print(f"Fetching info for {model}...")
    try:
        info = get_device_info(model)
        print(json.dumps(info, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
