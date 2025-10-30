"""
PyPotteryLayout - Flask Launcher for Executable
Launches the Flask app and opens the default browser
"""

import sys
import os
import threading
import time
import webbrowser
import logging

# Configure logging to file when running as exe
if getattr(sys, 'frozen', False):
    log_file = os.path.join(os.path.dirname(sys.executable), 'pypotterylayout.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

from app import app

def open_browser(port=5000, delay=1.5):
    """Open the default web browser after a delay"""
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(f'http://127.0.0.1:{port}')
            if getattr(sys, 'frozen', False):
                logging.info(f"Browser opened at http://127.0.0.1:{port}")
        except Exception as e:
            if getattr(sys, 'frozen', False):
                logging.error(f"Failed to open browser: {e}")
    
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()

def show_error(message):
    """Show error message in a dialog (Windows only)"""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "PyPotteryLayout Error", 0x10)
    except:
        pass

def main():
    """Main entry point for the executable"""
    PORT = 5000
    
    if getattr(sys, 'frozen', False):
        # Running as executable
        logging.info("PyPotteryLayout starting...")
        logging.info(f"Base path: {os.path.dirname(sys.executable)}")
    
    # Open browser after a short delay
    open_browser(PORT)
    
    # Start Flask app
    try:
        app.run(
            host='127.0.0.1',
            port=PORT,
            debug=False,
            use_reloader=False  # Important: disable reloader in executable
        )
    except Exception as e:
        error_msg = f"Error starting server: {e}"
        if getattr(sys, 'frozen', False):
            logging.error(error_msg)
            show_error(error_msg + "\n\nCheck pypotterylayout.log for details")
        else:
            print(f"\n\n{error_msg}")
        sys.exit(1)

if __name__ == '__main__':
    main()
