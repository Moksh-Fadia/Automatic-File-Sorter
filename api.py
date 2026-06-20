from fastapi import FastAPI, HTTPException     # httpexception is used to raise http errors (eg: 404, 400, 500) when api fails
import os    # to check if file exists
from db import get_connection, initialize_database
from main import move_file, source_dir
from fastapi import UploadFile, File      # UploadFile handles incoming files accessing their data; File is used to specify that the endpoint expects a file upload
from typing import List

initialize_database()    # initialize the database and create the files_table if it doesn't exist; this ensures that the database is ready to store file metadata before any API requests are processed

app = FastAPI(title="File Organizer API")    # creates fastapi application instance (we register endpoints to this app)

# api endpoint (URL) that handles post requests (like file uploads)
@app.post("/upload-files")
def upload_file(files: List[UploadFile] = File(...)):
# List[UploadFile] = File(...): Expects multiple uploaded files, treat them as an UploadFile object, and receive it from the request using the File tool
# UploadFile object has properties like filename, content_type, and methods like .read()
# File(...) marks it as a required parameter   

    os.makedirs(source_dir, exist_ok=True)   # create source folder (source_dir) if it doesn't exist (in case user tries to upload before running main.py for the first time, which creates the source_dir) - this prevents "No such file or directory" error when trying to save the uploaded file

    processed_files = []

    try:
        for file in files:      # for each uploaded file through the endpoint
            temp_path = os.path.join(source_dir, file.filename)     # create a temporary path for the uploaded file in the source_dir
        
            with open(temp_path, "wb") as f:
                f.write(file.file.read())   # read the contents of the uploaded file and write it to the temp_path; we open the file in binary mode ("wb") to ensure that all types of files (text, images, pdf, etc.) are handled correctly without encoding issues
        # file.file.read() reads the entire content of the uploaded file into memory, and f.write() writes that content to the temporary file on disk. This effectively saves the uploaded file to the source_dir 

        # these above 2 steps basically save the uploaded file temporarily in the main FileSorter folder. this is done bcoz move_file() expects the file to be in the source_dir and we are uploading the file through the FastAPI endpoint (SwaggerUI), so technically the file isnt yet present in the FileSorter folder (for it to start the file sorting process). So we first save it there so move_file() can process it  
    
            move_file(temp_path)   # automatically moves it to the correct subfolder
            processed_files.append(file.filename)

    except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "processed_files": processed_files}


# GET endpoint that returns DB rows (files from files_table)
@app.get("/files")
def list_files():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM files_table")

    rows = cursor.fetchall()

    conn.close()
    return {"files": rows}
# this basically fetches all the records from the files_table and returns them as a JSON response when the /files endpoint is accessed with a GET request. Each record contains metadata about the files that have been uploaded and moved, such as filename, file type, source path, destination path, and the time they were moved.





