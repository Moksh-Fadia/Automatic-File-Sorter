from os import scandir, rename       
from os.path import splitext, exists, join   

from shutil import move     

from time import sleep      

import logging   

from watchdog.observers import Observer   
from watchdog.events import FileSystemEventHandler     

import tkinter as tk
from tkinter import scrolledtext
from threading import Thread

from concurrent.futures import ThreadPoolExecutor   

import json 


logging.basicConfig(filename="file_mover.log", level=logging.INFO, 
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


source_dir = "C:\\Users\\YourName\\FileSorter"       

dest_dir_music = "C:\\Users\\YourName\\FileSorter\\Music"
dest_dir_video = "C:\\Users\\YourName\\FileSorter\\Videos"
dest_dir_image = "C:\\Users\\YourName\\FileSorter\\Images"
dest_dir_documents = "C:\\Users\\YourName\\FileSorter\\Documents"


image_extensions = [".jpg", ".jpeg", ".jpe", ".jif", ".jfif", ".jfi", ".png", ".gif", ".webp", ".tiff", ".tif",
".psd", ".raw", ".arw", ".cr2", ".nrw", ".k25", ".bmp", ".dib", ".heif", ".heic", ".ind", ".indd", ".indt", ".jp2",
".j2k", ".jpf", ".jpf", ".jpx", ".jpm", ".mj2", ".svg", ".svgz", ".ai", ".eps", ".ico"]

video_extensions = [".webm", ".mpg", ".mp2", ".mpeg", ".mpe", ".mpv", ".ogg",
                    ".mp4", ".mp4v", ".m4v", ".avi", ".wmv", ".mov", ".qt", ".flv", ".swf", ".avchd"]

audio_extensions = [".m4a", ".flac", "mp3", ".wav", ".wma", ".aac"]

document_extensions = [".doc", ".docx", ".odt",
                       ".pdf", ".xls", ".xlsx", ".ppt", ".pptx"]


undo_log = "undo_log.json"     

executor = ThreadPoolExecutor(max_workers=4) 

def save_undo_entry(src, dest):
    try:
        if exists(undo_log):
            with open(undo_log, "r") as file:
                data = json.load(file) 
        else:
            data = {}  

        data[src] = dest  

        with open(undo_log, "w") as file:
            json.dump(data, file, indent=4)  

    except Exception as e:
        logging.error(f"Error saving undo entry: {e}")  


def move_file(dest, entry, name):
    original_path = entry.path  

    if exists(f"{dest}/{name}"):            
        unique_name = make_unique(dest, name)
        oldName = join(dest, name)
        newName = join(dest, unique_name)
        rename(oldName, newName)

    move(entry, dest)
    save_undo_entry(original_path, join(dest, name))  


def make_unique(dest, name):
    filename, extension = splitext(name)
    counter = 1

    while exists(f"{dest}/{name}"):
        name = f"{filename}({str(counter)}){extension}"
        counter += 1

    return name


class MoverHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_modified(self, event):      
        with scandir(source_dir) as entries:     
            for entry in entries:     
                name = entry.name     
              
                executor.submit(self.check_audio_files, entry, name)    
                executor.submit(self.check_video_files, entry, name)    
                executor.submit(self.check_image_files, entry, name)    
                executor.submit(self.check_document_files, entry, name)
                self.app.log_message(f"Moved file: {name}") 

    def check_audio_files(self, entry, name):  
        for audio_extension in audio_extensions:
            if name.endswith(audio_extension) or name.endswith(audio_extension.upper()):
                move_file(dest_dir_music, entry, name)

    def check_video_files(self, entry, name):  
        for video_extension in video_extensions:
            if name.endswith(video_extension) or name.endswith(video_extension.upper()):
                move_file(dest_dir_video, entry, name)

    def check_image_files(self, entry, name): 
        for image_extension in image_extensions:
            if name.endswith(image_extension) or name.endswith(image_extension.upper()):
                move_file(dest_dir_image, entry, name)

    def check_document_files(self, entry, name):  
        for documents_extension in document_extensions:
            if name.endswith(documents_extension) or name.endswith(documents_extension.upper()):
                move_file(dest_dir_documents, entry, name)

if __name__ == "__main__":
    event_handler = MoverHandler()
    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=True)
    observer.start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
     

