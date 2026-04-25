#!/usr/bin/env python3
"""Entry point script for running the Telegram betting bot."""

import os
from agent_bot.main import main

if __name__ == "__main__":
    # Check if debug mode is enabled
    if os.getenv("DEBUG_MODE") == "true":
        import debugpy
        debug_port = int(os.getenv("DEBUG_PORT", "5678"))
        print(f"Starting with debugpy on port {debug_port}...")
        debugpy.listen(("0.0.0.0", debug_port))
        print("Waiting for debugger to attach...")
        debugpy.wait_for_client()
        print("Debugger attached!")
    
    main()
