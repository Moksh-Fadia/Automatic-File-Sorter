import os    
from os import scandir     # scandir() returns an iterator of DirEntry objects; a DirEntry object has attributes like name, path, is_file() [checks if its a file], is_dir() [checks if its a directory]
from os.path import splitext, exists, join   # join combines paths with /
import shutil
from shutil import move     
from time import sleep      
import logging    
# Watchdog: a python library that monitors folders for changes
from watchdog.observers import Observer    # triggers events when files/folders change
from watchdog.events import FileSystemEventHandler      # class to handle file system events like creation, modification, deletion
from concurrent.futures import ThreadPoolExecutor    # for concurrent processing of multiple files
from datetime import datetime
import sqlite3
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(BASE_DIR, exist_ok=True)

LOG_FILE = os.path.join(BASE_DIR, "file_mover.log")
DB_FILE = os.path.join(BASE_DIR, "files_db.db")

# Logging configuration
logging.basicConfig(
    filename=LOG_FILE,   # logs will be written to the file named file_mover.log; this file is pure record-keeping (we nerver edit it manualy) it basically keeps a record of what files moved, when, or if something failed; for debugging and tracking purposes
    level=logging.INFO,      # records INFO level and above (WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(message)s',     # timestamp - message
    datefmt='%Y-%m-%d %H:%M:%S')

# setup
source_dir = os.path.join(BASE_DIR, "FileSorter")      
dest_dir_music = os.path.join(source_dir, "Audio")
dest_dir_video = os.path.join(source_dir, "Videos")
dest_dir_image = os.path.join(source_dir, "Images")
dest_dir_documents = os.path.join(source_dir, "Documents")

# making sure all directories exist at startup
for folder in [source_dir, dest_dir_music, dest_dir_video, dest_dir_image, dest_dir_documents]:  
    os.makedirs(folder, exist_ok=True)

image_extensions = [".jpg", ".jpeg", ".jpe", ".jif", ".jfif", ".jfi", ".png", ".gif", ".webp", ".tiff", ".tif",
".psd", ".raw", ".arw", ".cr2", ".nrw", ".k25", ".bmp", ".dib", ".heif", ".heic", ".ind", ".indd", ".indt", ".jp2",
".j2k", ".jpf", ".jpf", ".jpx", ".jpm", ".mj2", ".svg", ".svgz", ".ai", ".eps", ".ico"]

video_extensions = [".webm", ".mpg", ".mp2", ".mpeg", ".mpe", ".mpv", ".ogg",
                    ".mp4", ".mp4v", ".m4v", ".avi", ".wmv", ".mov", ".qt", ".flv", ".swf", ".avchd"]

audio_extensions = [".m4a", ".flac", ".mp3", ".wav", ".wma", ".aac"]

document_extensions = [".doc", ".docx", ".odt",
                       ".pdf", ".xls", ".xlsx", ".ppt", ".pptx"]

executor = ThreadPoolExecutor(max_workers=4)    # executor = ThreadPoolExecutor object for concurrent processing of 4 files (audio, video, image, document) 

# function to make filename unique if it already exists ie. handle duplicates
def make_unique(dest, name):
    filename, extension = splitext(name)     # eg: file(1).txt on splitext gives filename = file(1), extension = .txt
    counter = 1

    while exists(join(dest, name)):      # looping until no file exists with that name in the destination
        name = f"{filename}({counter}){extension}"
        counter += 1
    return name


# dest here is the respective folder where the file is to be moved (ie. Music, Video, Image, Document)
# The source is always the top-level FileSorter folder (where the file is intially placed). The destination is the proper subfolder inside FileSorter (where the file is eventually moved to)

def move_file(file, conn=None):
    start_time = time.time()   # to find time taken to move the file and log it

    # Determine if input is DirEntry or string path
    if hasattr(file, "path"):  # DirEntry
        file_path = os.path.abspath(file.path)
        name = file.name
    else:  # string path
        file_path = os.path.abspath(file)
        name = os.path.basename(file_path)

    if name.startswith("."):  # skip hidden files like .DS_Store
        return

    ext = os.path.splitext(name)[1].lower()
    if ext in audio_extensions:
        dest = dest_dir_music
        file_type = "Audio"
    elif ext in video_extensions:
        dest = dest_dir_video
        file_type = "Video"
    elif ext in image_extensions:
        dest = dest_dir_image
        file_type = "Image"
    elif ext in document_extensions:
        dest = dest_dir_documents
        file_type = "Document"
    else:
        dest = os.path.join(source_dir, "Others")
        file_type = "Unknown"

    os.makedirs(dest, exist_ok=True)

    # Skip if already in destination
    if os.path.dirname(file_path) == dest:
        logging.info(f"File already in destination: {name}")
        return

    if exists(join(dest, name)):
        name = make_unique(dest, name)

    dest_path = os.path.join(dest, name)

    # Move the file
    shutil.move(file_path, dest_path)
    logging.info(f"[MOVED] {name} -> {dest_path}")

    # use the passed connection or create a new one
    own_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_FILE)
        own_conn = True
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM files_table WHERE source_path = ?", (file_path,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO files_table (filename, file_type, source_path, destination_path, moved_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, file_type, file_path, dest_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    if own_conn:
        conn.close()

    end_time = time.time()   # end timer
    print(f"[TIME] {name} processed in {end_time - start_time:.4f} sec")    

    return {"filename": name, "file_type": file_type, "destination": dest_path}


class MoverHandler(FileSystemEventHandler):      # base class to respond to file system events; its job is to define what should happen when files change in the folder

# Processes/works for all files that are created/modified in source_dir after startup ie. when script is running   
    def on_created(self, event):     # triggered when a new file is created in the monitored folder
# event eg: FileSorter/photo.jpg        
        if event.is_directory:      # ignore folders (.is_directory is for folders, we only want to process files)
            return

        file_path = event.src_path   # get path of the created file 
        print(f"[EVENT DETECTED] New file: {file_path}")

        executor.submit(move_file, file_path)   # this sends the file to move_file() to be processed in a separate thread, allowing the main thread to continue monitoring for new events without delay; move_file() will handle moving the file to the correct subfolder and logging the action; using executor.submit() allows us to process multiple files concurrently if they are created in quick succession, improving performance and responsiveness of the script              

# Processes/works for all files already present in source_dir at startup/before ie. when script has not yet started running
    def process_existing_files(self):
        with scandir(source_dir) as entries:
            for entry in entries:
                if entry.name.startswith(".") or not entry.is_file():
                    continue

                executor.submit(move_file, entry)   
                

if __name__ == "__main__":        # only runs if this python file is executed directly
    event_handler = MoverHandler()      # creates an instance of MoverHandler class (inherits from Watchdog); it is passed to observer.schedule() so that the observer knows which handler to call when files change
    event_handler.process_existing_files()  # process files already in folder
    observer = Observer()       # creates an observer object to observe the source_dir
    observer.schedule(event_handler, source_dir, recursive=True)     # schedules the event handler to monitor source_dir; recursive=True means it will monitor all subdfolders of source_dir too
    observer.start()       # starts monitoring the thread
    print(f"Monitoring {source_dir} ...")

    try:
        while True:
            sleep(1)     # main thread sleeps for 1 second and then checks again; to not consume too much CPU
    except KeyboardInterrupt:   # if user presses Ctrl+C to stop the program
        observer.stop()
    observer.join()     # waits for the observer thread to finish completely before exiting the program; without join() the program might exit immediately and leave Watchdog threads hanging  
     

