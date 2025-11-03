"""
PingMonitor Pro v2.0 - No Console Launcher
Launches the application without showing a console window
"""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir.parent))

# Import and run main
from src.main import main

if __name__ == '__main__':
    main()
