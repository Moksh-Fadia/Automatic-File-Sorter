import os    
from os import scandir     # scandir() returns an iterator of DirEntry objects; a DirEntry object has attributes like name, path, is_file() [checks if its a file], is_dir() [checks if its a directory]
from os.path import splitext, exists, join, basename    # join combines paths with /
from shutil import move     
from time import sleep      
import logging    
# Watchdog: a python library that monitors folders for changes
from watchdog.observers import Observer    # triggers events when files/folders change
from watchdog.events import FileSystemEventHandler      # class to handle file system events like creation, modification, deletion
from concurrent.futures import ThreadPoolExecutor    # for concurrent processing of multiple files
from datetime import datetime
import sqlite3
from fastapi import HTTPException

# Logging configuration
logging.basicConfig(
    filename="file_mover.log",   # logs will be written to the file named file_mover.log; this file is pure record-keeping (we nerver edit it manualy) it basically keeps a record of what files moved, when, or if something failed; for debugging and tracking purposes
    level=logging.INFO,      # records INFO level and above (WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(message)s',     # timestamp - message
    datefmt='%Y-%m-%d %H:%M:%S')

# setup
source_dir = "./FileSorter"       
dest_dir_music = join(source_dir, "Audio")   
dest_dir_video = join(source_dir, "Videos")     
dest_dir_image = join(source_dir, "Images")
dest_dir_documents = join(source_dir, "Documents")

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
def move_file(dest, entry, name, file_type, conn=None):    # this func expects a DirEntry-like object  
    if name.startswith("."):  # skip hidden files like .DS_Store
        return

    # Skip if the file is already in the correct subfolder
    if entry.path == dest:
        logging.info(f"File already in destination: {name}")
        return

    if exists(join(dest, name)):         # if any file with same name existing in destination folder (duplicate)
        name = make_unique(dest, name)

# entry.path = (built-in attribute of DirEntry object) gets the full path of the file to be moved
    src_path = os.path.abspath(entry.path)
    dest_path = os.path.abspath(join(dest, name))
    move(src_path, dest_path)

    logging.info(f"Moved file: {name} to {dest}")     # writing info to log file

# inserting record
    moved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")     # timestamp

    # use the passed connection or create a new one
    own_conn = False    
    if conn is None:
        conn = sqlite3.connect("files_db.db")
        own_conn = True
    cursor = conn.cursor()   

    cursor.execute("""
        SELECT COUNT(*) FROM files_table WHERE source_path = ?           -- counts the number of rows with this source_path (ie. to avoid duplicate entries in database)
    """, (entry.path,))
    if cursor.fetchone()[0] == 0:    # if count is 0, ie. no such entry exists in database
        cursor.execute("""
            INSERT INTO files_table (filename, file_type, source_path, destination_path, moved_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, file_type, entry.path, join(dest, name), moved_at))
        conn.commit()

    if own_conn:
        conn.close()


# this func determines the file type, finds the correct destination folder, and moves the file using move_file()
def move_any_file(filepath):
    filename = basename(filepath)
    ext = os.path.splitext(filename)[1].lower()      # gets the extension of the file

    if ext in audio_extensions:
        dest = dest_dir_music
        file_type = "Audio"
    elif ext in video_extensions:
        dest = dest_dir_video
        file_type = "Videos"
    elif ext in image_extensions:
        dest = dest_dir_image
        file_type = "Images"
    elif ext in document_extensions:
        dest = dest_dir_documents
        file_type = "Documents"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown file type: {filename}"
        )

# create a tiny object that mimics the DirEntry-like object your move_file func (from main.py) expects; to reuse the same move_file() function and avoid duplicating logic, we create a tiny object that mimics those attributes and methods
    class DummyEntry:
        def __init__(self, path, name):
            self.path = path
            self.name = name
        def is_file(self):
            return True

    dummy = DummyEntry(filepath, filename)      # creates an instance of the dummy object pointing to the file just saved
    move_file(dest, dummy, filename, file_type)    


# scans existing files (those files which were already present before script started running) in destination folders and adds them to the database if not already present
def scan_existing_files(cursor, conn):
    categories = {
        "Audio": dest_dir_music,
        "Videos": dest_dir_video,
        "Images": dest_dir_image,
        "Documents": dest_dir_documents
    }

    for file_type, folder in categories.items():     
# file_type = key (Audio, Videos, Images, Documents); folder = value (respective folder path)
        if not os.path.exists(folder):
            continue
        for filename in os.listdir(folder):  
            if filename.startswith("."):     # skips .DS_Store and any hidden files
                continue 
# os.listdir(folder) returns a list of all entries (ie. files and subfolders) in that respective folder
            file_path = os.path.join(folder, filename)     # combines the folder path and the filename to get the full path to the file
            if os.path.isfile(file_path):   # checks if the path is a file (not a directory)
                cursor.execute("SELECT COUNT(*) FROM files_table WHERE source_path = ?", (file_path,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO files_table (filename, file_type, source_path, destination_path, moved_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (filename, file_type, file_path, file_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()   


class MoverHandler(FileSystemEventHandler):      # base class to respond to file system events; its job is to define what should happen when files change in the folder

# Processes/works for all files that are created/modified in source_dir after startup ie. when script is running   
    def on_modified(self):     # called automatically when any file in source_dir changes (created, edited)
        with scandir(source_dir) as entries:     # iterates over all files in source_dir (FileSorter folder)
            for entry in entries:      # entry is a DirEntry object with attributes like name, path, is_file(), is_dir()        
# each entry is a file/folder in source_dir (FileSorter)
                if entry.name.startswith(".") or not entry.is_file():
                    continue

                name = entry.name           
                executor.submit(self.check_audio_files, entry, name)    
                executor.submit(self.check_video_files, entry, name)    
                executor.submit(self.check_image_files, entry, name)    
                executor.submit(self.check_document_files, entry, name)
# executor.submit = instead of checking one after another sequentially, it submits all 4 checks (audio, video, image, document) to run concurrently in separate threads                  

# Processes/works for all files already present in source_dir at startup/before ie. when script has not yet started running
    def process_existing_files(self):
        with scandir(source_dir) as entries:
            for entry in entries:
                if entry.name.startswith(".") or not entry.is_file():
                    continue

                name = entry.name
                executor.submit(self.check_audio_files, entry, name)
                executor.submit(self.check_video_files, entry, name)
                executor.submit(self.check_image_files, entry, name)
                executor.submit(self.check_document_files, entry, name)    


    def check_audio_files(self, entry, name):
        if name.startswith(".") or not entry.is_file():  # skip hidden files and folders
            return
        if any(name.lower().endswith(ext) for ext in audio_extensions):
            move_file(dest_dir_music, entry, name, "audio")

    def check_video_files(self, entry, name):
        if name.startswith(".") or not entry.is_file():  # skip hidden files and folders
            return        
        if any(name.lower().endswith(ext) for ext in video_extensions):
            move_file(dest_dir_video, entry, name, "video")

    def check_image_files(self, entry, name):
        if name.startswith(".") or not entry.is_file():  # skip hidden files and folders
            return        
        if any(name.lower().endswith(ext) for ext in image_extensions):
            move_file(dest_dir_image, entry, name, "image")

    def check_document_files(self, entry, name):
        if name.startswith(".") or not entry.is_file():  # skip hidden files and folders
            return        
        if any(name.lower().endswith(ext) for ext in document_extensions):
            move_file(dest_dir_documents, entry, name, "document")


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
     

