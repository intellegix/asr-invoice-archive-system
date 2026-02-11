#!/usr/bin/env python3
"""
ASR Document Scanner Startup Script
Simple launcher for the desktop scanning client
"""

import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path so we can import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the main scanner module
from main_scanner import main

if __name__ == "__main__":
    print("🚀 Starting ASR Document Scanner v2.0.0...")
    print("📁 Desktop scanning client with offline capabilities")
    print("=" * 60)

    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔄 Scanner application interrupted by user")
    except Exception as e:
        print(f"\n❌ Scanner startup failed: {e}")
        sys.exit(1)