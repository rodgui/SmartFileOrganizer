#!/usr/bin/env python3
"""
Smart File Organizer - Unified Entry Point

Usage:
    python organize.py scan ~/Documents --local
    python organize.py plan ~/Downloads --gemini
    python organize.py execute plan.json --apply
    python organize.py info
    
    # Or open GUI (legacy)
    python organize.py --gui
"""
import sys

def main():
    # Check if user wants GUI
    if "--gui" in sys.argv or len(sys.argv) == 1:
        # Remove --gui from args if present
        if "--gui" in sys.argv:
            sys.argv.remove("--gui")
        
        # If no args or --gui, open GUI
        if len(sys.argv) == 1:
            print("Starting GUI... (use 'python organize.py --help' for CLI)")
            from src.gui import main as gui_main
            gui_main()
        else:
            # Has other args, use CLI
            from src.organizer.cli import cli
            cli()
    else:
        # Use CLI
        from src.organizer.cli import cli
        cli()

if __name__ == "__main__":
    main()
