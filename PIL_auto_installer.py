import subprocess
import sys

def install_pil():
    """
    Check if PIL/Pillow is installed, if not install it automatically
    """
    try:
        from PIL import Image
        print("PIL/Pillow is already installed ✓")
        return True
    except ImportError:
        print("PIL/Pillow not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
            print("PIL/Pillow installed successfully ✓")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install PIL/Pillow ✗")
            print("Please install manually: pip install Pillow")
            return False

if __name__ == "__main__":
    install_pil()