#!/usr/bin/env python3

import os
import sys
import subprocess
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, process):
        self.process = process
        self.last_reload = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith(('.py', '.html', '.css', '.js', '.env')):
            current_time = time.time()
            if current_time - self.last_reload > 1:  # Debounce
                print(f"File changed: {event.src_path}")
                self.restart_server()
                self.last_reload = current_time
    
    def restart_server(self):
        print("Restarting server...")
        self.process.terminate()
        self.process.wait()
        self.process = subprocess.Popen([sys.executable, "server.py"])

def main():
    print("Starting development server with auto-reload...")
    
    # Start the server
    process = subprocess.Popen([sys.executable, "server.py"])
    
    # Set up file watcher
    event_handler = ReloadHandler(process)
    observer = Observer()
    observer.schedule(event_handler, Path(__file__).parent, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        observer.stop()
        process.terminate()
        process.wait()
    
    observer.join()

if __name__ == '__main__':
    main()