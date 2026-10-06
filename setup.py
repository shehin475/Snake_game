"""
Installation and Setup Script for Nokia Snake Game
Automatically installs all required dependencies
"""

import os
import subprocess
import sys

def main():
    """Main setup function"""
    print("Nokia Snake Game - Setup Script")
    print("=" * 50)

    requirements = os.path.join(os.path.dirname(__file__), "requirements.txt")
    print("Installing the pinned project dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements
        ])
    except subprocess.CalledProcessError:
        print("Dependency installation failed.")
        print("Please install them manually using:")
        print("  python -m pip install -r requirements.txt")
        return

    print()
    print("=" * 50)
    print("Setup completed successfully!")
    print()
    print("To start the game, run:")
    print("  python main.py")
    print()
    print("Game Controls:")
    print("- Move your hand up/down/left/right to control the snake")
    print("- Pinch thumb and index finger for speed boost")
    print("- Show 'UP' gesture when game over to restart")
    print("- Press ESC in game window to quit")
    print()
    print("Make sure your webcam is connected and working!")

if __name__ == "__main__":
    main()