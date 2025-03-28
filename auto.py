# os module provides functions to interact with the operating system, like handling files and directories.
from os import scandir, rename          # scandir() → Lists files in a directory, rename() → Renames a file.
from os.path import splitext, exists, join     # exists() → Checks if a file exists, join() → Joins folder and file names to form a path.

# shutil used for high-level file operations like copying and moving files.
from shutil import move     # move() → Moves a file from one location to another.

from time import sleep      # sleep() → Pauses the program for a given number of seconds.

# logging module helps in logging messages to track program execution.
import logging      # basicConfig() → Configures logging format and level, info() → Logs an info message.

# watchdog module monitors file system changes in real-time.
from watchdog.observers import Observer         # Observer() → Watches a directory for changes.
from watchdog.events import FileSystemEventHandler     # FileSystemEventHandler() → Triggers actions when changes occur.

import tkinter as tk
from tkinter import scrolledtext
from threading import Thread

from concurrent.futures import ThreadPoolExecutor   # ThreadPoolExecutor lets us run multiple tasks in parallel using threads. 
# Instead of waiting for each file to be processed one by one, multiple files are handled at the same time

import json  # Used to store file paths in a JSON file


logging.basicConfig(filename="file_mover.log", level=logging.INFO, 
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


source_dir = "C:\\Users\\YourName\\FileSorter"        # main folder (source)
# sub folders (destination):
dest_dir_music = "C:\\Users\\YourName\\FileSorter\\Music"
dest_dir_video = "C:\\Users\\YourName\\FileSorter\\Videos"
dest_dir_image = "C:\\Users\\YourName\\FileSorter\\Images"
dest_dir_documents = "C:\\Users\\YourName\\FileSorter\\Documents"


image_extensions = [".jpg", ".jpeg", ".jpe", ".jif", ".jfif", ".jfi", ".png", ".gif", ".webp", ".tiff", ".tif",
".psd", ".raw", ".arw", ".cr2", ".nrw", ".k25", ".bmp", ".dib", ".heif", ".heic", ".ind", ".indd", ".indt", ".jp2",
".j2k", ".jpf", ".jpf", ".jpx", ".jpm", ".mj2", ".svg", ".svgz", ".ai", ".eps", ".ico"]

# ? supported Video types
video_extensions = [".webm", ".mpg", ".mp2", ".mpeg", ".mpe", ".mpv", ".ogg",
                    ".mp4", ".mp4v", ".m4v", ".avi", ".wmv", ".mov", ".qt", ".flv", ".swf", ".avchd"]

# ? supported Audio types
audio_extensions = [".m4a", ".flac", "mp3", ".wav", ".wma", ".aac"]

# ? supported Document types
document_extensions = [".doc", ".docx", ".odt",
                       ".pdf", ".xls", ".xlsx", ".ppt", ".pptx"]


undo_log = "undo_log.json"      # This file will store the original and new paths of files before they are moved

executor = ThreadPoolExecutor(max_workers=4)  # max_workers=4 means 4 tasks can run at the same time
# (You can increase this number if you have a powerful computer)


# If a file is moved by mistake, store its original path and allow restoring
def save_undo_entry(src, dest):
    try:
        if exists(undo_log):  # Check if undo_log.json already exists
            with open(undo_log, "r") as file:
                data = json.load(file)  # Load existing file history
        else:
            data = {}  # If file doesn’t exist, create an empty dictionary

        data[src] = dest  # We store the original file path (src) and its new location (dest)

        with open(undo_log, "w") as file:
            json.dump(data, file, indent=4)  # Save updated data in JSON format

    except Exception as e:
        logging.error(f"Error saving undo entry: {e}")  # Log any errors


def move_file(dest, entry, name):
    original_path = entry.path  # Get the original path (current location) of the file

    if exists(f"{dest}/{name}"):            # if file with same name exists
        unique_name = make_unique(dest, name)
        oldName = join(dest, name)
        newName = join(dest, unique_name)
        rename(oldName, newName)

    move(entry, dest)
    save_undo_entry(original_path, join(dest, name))  # saves the original and new paths in undo_log.json for future restoration


def make_unique(dest, name):
    filename, extension = splitext(name)
    counter = 1
    # IF FILE WITH SAME EXISTS, ADDS NUMBER TO THE END OF THE FILENAME
    while exists(f"{dest}/{name}"):
        name = f"{filename}({str(counter)}){extension}"
        counter += 1

    return name


class MoverHandler(FileSystemEventHandler):
    # THIS FUNCTION WILL RUN WHENEVER THERE IS A CHANGE IN "source_dir"
    # .upper is for not missing out on files with uppercase extensions

    def on_modified(self, event):       # this is a built-in func in the MoverHandler Class
        with scandir(source_dir) as entries:        # scans the main folder
            for entry in entries:     # entry is an object representing a file or folder inside source_dir (eg: <DirEntry 'image.jpg'>) [it basically contains the file details]
                name = entry.name     # This is a string that contains just the file's name, including its extension. (eg: image.jpg)
# Submit each file-processing function to the ThreadPoolExecutor                
                executor.submit(self.check_audio_files, entry, name)    # Starts processing audio files in a separate thread
                executor.submit(self.check_video_files, entry, name)    # Starts processing video files in a separate thread
                executor.submit(self.check_image_files, entry, name)    # Starts processing image files in a separate thread
                executor.submit(self.check_document_files, entry, name) # Starts processing document files in a separate thread
                app.log_message(f"Moved file: {name}")  # Update log in GUI
# Instead of processing one file at a time, multiple files are processed simultaneously, making the script much faster

    def check_audio_files(self, entry, name):  # * Checks all Audio Files
        for audio_extension in audio_extensions:
            if name.endswith(audio_extension) or name.endswith(audio_extension.upper()):
                move_file(dest_dir_music, entry, name)

    def check_video_files(self, entry, name):  # * Checks all Video Files
        for video_extension in video_extensions:
            if name.endswith(video_extension) or name.endswith(video_extension.upper()):
                move_file(dest_dir_video, entry, name)

    def check_image_files(self, entry, name):  # * Checks all Image Files
        for image_extension in image_extensions:
            if name.endswith(image_extension) or name.endswith(image_extension.upper()):
                move_file(dest_dir_image, entry, name)

    def check_document_files(self, entry, name):  # * Checks all Document Files
        for documents_extension in document_extensions:
            if name.endswith(documents_extension) or name.endswith(documents_extension.upper()):
                move_file(dest_dir_documents, entry, name)


# GUI application class
class FileMoverApp:         # It represents the GUI application for organizing files
    def __init__(self, root):       # This method sets up the GUI (window title, buttons, log area, etc.)
        self.root = root        # root is the Tkinter window (the main GUI frame)
        self.root.title("Automated File Organizer")
        self.root.geometry("500x400")       # (width)x(height) pixels
        
        # Status label - Creates a label that shows the current status of file monitoring
        self.status_label = tk.Label(root, text="Status: Stopped", fg="red")    # The default text is "Stopped" (monitoring not started yet)
        self.status_label.pack(pady=10)     # padding (vertically) 10 pixels
        
        # Buttons - Creates a button labeled "Start Monitoring"
        self.start_button = tk.Button(root, text="Start Monitoring", command=self.start_monitoring)  #  When clicked, it runs the start_monitoring() method
        self.start_button.pack(pady=5)      # Adds 5 pixels of vertical spacing
        
        self.stop_button = tk.Button(root, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)  # state=tk.DISABLED → Disabled initially (can’t be clicked until monitoring starts) 
        # command=self.stop_monitoring → Runs stop_monitoring() when clicked
        self.stop_button.pack(pady=5)
        
        # Log display - Creates a scrollable text box to display logs
        self.log_text = scrolledtext.ScrolledText(root, width=60, height=15, state=tk.DISABLED) # 60 characters wide, 15 rows tall, Disabled initially so users can’t edit the log manually
        self.log_text.pack(pady=10)     #  Adds spacing below the log area
        
        self.observer = None
    
    def start_monitoring(self):     # Runs when "Start Monitoring" is clicked, Starts the Observer (watchdog) to monitor file changes
        global observer
        self.status_label.config(text="Status: Running", fg="green")    #  Changes status text to "Running" and color to green
        self.start_button.config(state=tk.DISABLED)   # Disables "Start Monitoring" button (prevents multiple clicks)
        self.stop_button.config(state=tk.NORMAL)    # Enables "Stop Monitoring" button (so we can stop it)
        
        self.observer = Observer()      # Creates a watchdog observer to monitor file changes
        event_handler = MoverHandler()  # Creates an event handler (from your existing code) to process file movements
        self.observer.schedule(event_handler, source_dir, recursive=True)   # Tells watchdog to watch the source folder (source_dir), recursive=True means it also watches subfolders
        observer_thread = Thread(target=self.run_observer)     # Creates a new thread to run run_observer() without freezing the GUI.
        observer_thread.daemon = True       # Ensures that if the GUI is closed, the thread stops automatically
        observer_thread.start()     # Starts the background thread
    
    def run_observer(self):   # This keeps the watchdog running Continuously
        self.observer.start()
        try:
            while True:
                sleep(10)      # It checks for file changes every 10 seconds
        except KeyboardInterrupt:       # If the program is interrupted (Ctrl+C), it stops the observer
            self.observer.stop()
        self.observer.join()
    
    def stop_monitoring(self):   # Runs when "Stop Monitoring" is clicked, Stops the watchdog observer and resets the GUI
        if self.observer:   # If the observer is running, it stops and waits until it fully exits
            self.observer.stop()
            self.observer.join()
        self.status_label.config(text="Status: Stopped", fg="red")   # Changes status to "Stopped" (red text)
        self.start_button.config(state=tk.NORMAL)       # Re-enables "Start Monitoring" button
        self.stop_button.config(state=tk.DISABLED)      # Disables "Stop Monitoring" button
    
    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)      # Enables the log box so we can add text
        self.log_text.insert(tk.END, message + "\n")    # Adds a new message at the end
        self.log_text.config(state=tk.DISABLED)     # Disables text box again
        self.log_text.yview(tk.END)     # Scrolls to the bottom automatically


if __name__ == "__main__":      # Running the GUI
    root = tk.Tk()      # Creates the main Tkinter window
    app = FileMoverApp(root)      # Creates an instance of our GUI class
    root.mainloop()     # Starts the Tkinter event loop (keeps the GUI running)