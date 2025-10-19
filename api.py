from fastapi import FastAPI, HTTPException      # httpexception is used to raise http errors (eg: 404, 400, 500)
import os    # to check if file exists
import sqlite3
from main import scan_existing_files, move_file, dest_dir_music, dest_dir_video, dest_dir_image, dest_dir_documents, image_extensions, audio_extensions, video_extensions, document_extensions
from os.path import join
from fastapi import UploadFile, File      # UploadFile handles incoming files accessing their data; File is used to specify that the endpoint expects a file upload

conn = sqlite3.connect("files_db.db")
cursor = conn.cursor()     # creates a cursor object to execute SQL commands
cursor.execute("""
CREATE TABLE IF NOT EXISTS files_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    file_type TEXT,
    source_path TEXT,
    destination_path TEXT,
    moved_at TEXT      
)
""")
conn.commit()     # commits the changes to the database

app = FastAPI(title="File Organizer API")    # creates fastapi application instance (we'' register endpoints to this app)

# creates and return a new sqlite3 connection for each request bcoz sqlite3 connections cannot be shared across threads 
# every time an endpoint is hit, get_db_connection() is called, it opens a fresh connection to the .db file, we use it for that one request, and close it when done (every request gets its own independent connection); this prevents “database is locked” errors 
def get_db_connection():
    conn = sqlite3.connect("files_db.db")
    return conn


# it triggers a one-time scan of existing files in the destination folders and add entries to the DB, meaning When this endpoint is called, it goes through the file directories (like music, videos, etc.) and updates the database with whatever files are already there; basically a refresh-data button
@app.get("/scan-existing")      # registers a GET endpoint
def scan_files():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
# instead of using a global cursor (which is thread-unsafe), we pass the cursor from the request-specific connection; this way each fastapi request uses its own db connection and cursor, preventing the SQLite threading error        
        scan_existing_files(cursor, conn)  # modified scan_existing_files to accept cursor
        conn.close()
        return {"status": "success", "message": "Existing files scanned and added to DB."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Note:- type of error which occurs when we dont this: 'SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 8382603584 and this is thread id 6109884416'
# it means we cannot share sqlite connection or cursor objects between threads. each thread must open its own connection and create its own cursor


# api endpoint (URL) that handles post requests (like file uploads)
@app.post("/upload-file")
def upload_file(file: UploadFile = File(...)):
# UploadFile = File(...): Expect an uploaded file, treat it as an UploadFile object, and receive it from the request using the File tool
# UploadFile object has properties like filename, content_type, and methods like .read()
# File(...) marks it as a required parameter   
  
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()     # gets the extension of the file

    # automatically detect type
    if ext in audio_extensions:
        dest = dest_dir_music
        file_type = "audio"
    elif ext in video_extensions:
        dest = dest_dir_video
        file_type = "video"
    elif ext in image_extensions:
        dest = dest_dir_image
        file_type = "image"
    elif ext in document_extensions:
        dest = dest_dir_documents
        file_type = "document"
    else:
        raise HTTPException(status_code=400, detail="Unknown file type")
    
    dest_path = join(dest, filename)  # combines the destination folder and the filename to get the full path where the file should be saved.

# save uploaded file directly to destination
    with open(dest_path, "wb") as f:    # opens a new file at dest_path in binary write mode 'wb'
        f.write(file.file.read())    # reads all the content of the uploaded file and writes that content to disk

# create a tiny object that mimics the DirEntry-like object your move_file func (from main.py) expects; to reuse the same move_file() function and avoid duplicating logic, we create a tiny object that mimics those attributes and methods
    class DummyEntry:
        def __init__(self, path, name): 
            self.path = path
            self.name = name
        def is_file(self):
            return True

    dummy = DummyEntry(dest_path, filename)     # creates an instance of the dummy object pointing to the file just saved

# move the file using your existing main.py logic
    try:    
        conn = get_db_connection()      # This ensures each request has its own SQLite connection
        move_file(dest, dummy, filename, file_type, conn=conn)
        conn.close()  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "message": f"{filename} uploaded and moved to {dest}"}


# GET endpoint that returns DB rows (files from files_table), optionally filtered by file_type query param
@app.get("/files")
def list_files(file_type: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if file_type:
            cursor.execute("SELECT * FROM files_table WHERE file_type = ?", (file_type,))
        else:
            cursor.execute("SELECT * FROM files_table")
        rows = cursor.fetchall()
    finally:
        conn.close()
    return {"files": rows}



