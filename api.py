from fastapi import FastAPI, HTTPException      # httpexception is used to raise http errors (eg: 404, 400, 500)
import os    # to check if file exists
from os import makedirs
import sqlite3
from main import scan_existing_files, move_file, dest_dir_music, dest_dir_video, dest_dir_image, dest_dir_documents, image_extensions, audio_extensions, video_extensions, document_extensions, move_any_file
from os.path import join
from fastapi import UploadFile, File      # UploadFile handles incoming files accessing their data; File is used to specify that the endpoint expects a file upload
from typing import Optional

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

    # Ensure source and destination folders exist at runtime
    source_dir = "./FileSorter"
    dest_dirs = {
        "Audio": join(source_dir, "Audio"),
        "Videos": join(source_dir, "Videos"),
        "Images": join(source_dir, "Images"),
        "Documents": join(source_dir, "Documents")
    }
    makedirs(source_dir, exist_ok=True)
    for folder in dest_dirs.values():
        makedirs(folder, exist_ok=True)

    # save the uploaded file temporarily in the main FileSorter folder
    temp_path = join(source_dir, file.filename)
    with open(temp_path, "wb") as f:
        f.write(file.file.read())

    try:
        move_any_file(temp_path)   # automatically moves it to the correct subfolder
    except Exception as e:
        print(f"[ERROR] move_any_file failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "message": f"{file.filename} uploaded and moved successfully."}


# GET endpoint that returns DB rows (files from files_table), optionally filtered by file_type query param
@app.get("/files")
def list_files(file_type: Optional[str] = None):
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





