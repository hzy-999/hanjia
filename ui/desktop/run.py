import sys
import os

# Add the current directory to sys.path to ensure 'core' and 'ui' are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    try:
        from ui.app import run_app
        run_app()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
