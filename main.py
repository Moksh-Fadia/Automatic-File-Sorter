import os    
from os import scandir     # scandir() returns an iterator of DirEntry objects; a DirEntry object has attributes like name, path, is_file() [checks if its a file], is_dir() [checks if its a directory]
from os.path import splitext, exists, join   # join combines paths with /
import shutil   # shutil.move() is used to move files from source to destination: shutil is a high-level file operations library that provides functions for copying, moving, and deleting files and directories
from time import sleep      
import logging    
# Watchdog: a python library that monitors folders for changes
from watchdog.observers import Observer    # triggers events when files/folders change; Observer continuously watches a folder
from watchdog.events import FileSystemEventHandler      # class to handle file system events like creation, modification, deletion
from concurrent.futures import ThreadPoolExecutor    # for concurrent processing of multiple files (without this files will be moved sequentially ie. one at a time, which is slower)
from datetime import datetime
from db import get_connection, initialize_database
import time

# BASE_DIR dynamically determines the project root directory so that all paths are relative to the project instead of being hardcoded.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "file_mover.log")

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
dest_dir_others = os.path.join(source_dir, "Others")

# making sure all directories exist at startup
for folder in [source_dir, dest_dir_music, dest_dir_video, dest_dir_image, dest_dir_documents, dest_dir_others]:  
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

def move_file(file_path):
    start_time = time.time()   # to find time taken to move the file and log it

    file_path = os.path.abspath(file_path)
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
        dest = dest_dir_others
        file_type = "Unknown"

    os.makedirs(dest, exist_ok=True)    # make sure destination folder exists (it should already exist from the setup code, but this is just to be safe in case something deleted it or if we add new file types in the future with new folders) exist_ok=True means it will not raise an error if the folder already exists, it will just do nothing and continue; this ensures that the script does not crash if the folder is already there, and it also ensures that the folder is created if it is missing for some reason, making the script more robust and reliable

# if the file is already in the correct destination folder, we skip moving it again; this can happen if the script is restarted and there are already files in the subfolders, we dont want to move them again or log them again, we just want to ignore them and move on(Skip if already in destination)
    if os.path.dirname(file_path) == dest:   
        logging.info(f"File already in destination: {name}")
        return

    if exists(join(dest, name)):    # if a file with the same name already exists in the destination folder, we need to make the new file's name unique to avoid overwriting the existing file
        name = make_unique(dest, name)

    dest_path = os.path.join(dest, name)    # final destination path for the file (after ensuring uniqueness if needed)

    # Move the file
    shutil.move(file_path, dest_path)
    logging.info(f"[MOVED] {name} -> {dest_path}")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
            INSERT INTO files_table (filename, file_type, source_path, destination_path, moved_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, file_type, file_path, dest_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

    end_time = time.time()   # end timer
    print(f"[TIME] {name} processed in {end_time - start_time:.4f} sec")    

    return {"filename": name, "file_type": file_type, "destination": dest_path}


class MoverHandler(FileSystemEventHandler):      # base class to respond to file system events; its job is to define what should happen when files change in the folder

# on_created() is a method of the MoverHandler class that is called automatically by the Watchdog library whenever a new file is created in the monitored folder (source_dir). It receives an event object that contains information about the file creation event, such as the path of the new file and whether it is a directory or a file. This method checks if the event is for a file (not a directory) and then submits the file to be processed by the move_file() function in a separate thread using executor.submit(). 
    def on_created(self, event):     # triggered when a new file is created in the monitored folder 
# event eg: FileSorter/photo.jpg        
        if event.is_directory:      # ignore folders (.is_directory is for folders, we only want to process files)
            return

        file_path = event.src_path   # get path of the created file 
        print(f"[EVENT DETECTED] New file: {file_path}")

        executor.submit(move_file, file_path)   # this sends the file to move_file() to be processed in a separate thread, allowing the main thread to continue monitoring for new events without delay; move_file() will handle moving the file to the correct subfolder and logging the action; using executor.submit() allows us to process multiple files concurrently if they are created in quick succession improving performance             

# Processes/works for all files ALREADY present in source_dir at startup/before ie. when script has not yet started running
    def process_existing_files(self):
        with scandir(source_dir) as entries:
            for entry in entries:
                if entry.name.startswith(".") or not entry.is_file():
                    continue

                executor.submit(move_file, entry.path)   
                


if __name__ == "__main__":        # only runs if this python file is executed directly (like python main.py); if this file is imported as a module in another file, the code inside this block will not run (which was the motive, to prevent the script from running when imported)
    initialize_database()   # initializes the database and creates the files_table if it doesn't already exist; this ensures that the database is ready to store file information before we start monitoring for file changes
    event_handler = MoverHandler()    # creates an object of MoverHandler class (inherits from Watchdog); it is passed to observer.schedule() so that the observer knows which handler to call when files change
    event_handler.process_existing_files()  # process files already in folder
    observer = Observer()       # creates an observer object to observe the source_dir
    observer.schedule(event_handler, source_dir, recursive=True)     # schedules the event handler to monitor source_dir; recursive=True means it will monitor all subdfolders of source_dir too (basically telling telling Observer to watch this folder and When something happens, send events to event_handler)
    observer.start()       # starts monitoring the thread
    print(f"Monitoring {source_dir} ...")

    try:
        while True:   # keeps the main thread alive to allow the observer to keep running and monitoring for file changes; without this loop, the main thread would exit immediately after starting the observer, which would stop the observer from working; this loop keeps the program running infinitely until the user decides to stop it (like by pressing Ctrl+C)
            sleep(1)     # main thread sleeps for 1 second and then checks again; to not consume too much CPU
    except KeyboardInterrupt:   # if user presses Ctrl+C to stop the program
        observer.stop()
    observer.join()     # waits for the observer thread to finish completely before exiting the program; without join() the program might exit immediately and leave Watchdog threads hanging  
     
