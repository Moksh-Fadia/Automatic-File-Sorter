# 🧠 File Organizer API

A **Dockerized backend system** that automatically organizes files from a source folder into categorized destinations (Audio, Videos, Images, Documents) while maintaining a complete record of every move inside an **SQLite database**.

It combines **file system automation** using `watchdog` with a **FastAPI-based REST API** to upload and manage files programmatically.
The code also includes comments for better readability and understanding.

---

## 🚀 Features

-> **Automatic Sorting:**  
Monitors a folder in real time and moves files to their respective subfolders based on type (audio, video, image, document).

-> **REST API Integration (FastAPI):**  
Upload files, trigger rescans, and list organized files via clean API endpoints.

-> **Database Logging (SQLite):**  
Every file move is stored with timestamps, source/destination paths, and type — ensuring traceability.

-> **Threaded Processing:**  
Uses `ThreadPoolExecutor` for efficient, concurrent file handling.

-> **Containerized (Docker):**  
Easily deployable anywhere — no dependency hell, no setup headaches.

-> **Logging:**  
Every file operation is tracked in `file_mover.log` for transparency and debugging.

---

## 🧩 Tech Stack


**Language**: Python 
**Backend Framework**: FastAPI 
**Database**: SQLite 
**File Monitoring**: Watchdog 
**Concurrency**: ThreadPoolExecutor 
**Containerization**: Docker 
**Logging**: Python’s `logging` module 

---

## 🗂 Folder Structure

File_Management/
│
├── main.py                # Core watcher + file moving logic
├── api.py                 # FastAPI app with upload, scan, and list endpoints
├── requirements.txt       # Dependencies
├── Dockerfile             # Docker build configuration
├── file_mover.log         # Log file for tracking file movements
├── files_db.db            # SQLite database for move history
└── /FileSorter            # The source directory being monitored
    ├── Audio/
    ├── Videos/
    ├── Images/
    └── Documents/

---

## ⚙️ How It Works

### 1️⃣ Watchdog + File Mover (`main.py`)
- Watches `/FileSorter` for new or modified files  
- Detects file type via extension  
- Moves it to the correct destination folder  
- Logs each move in:
  - `file_mover.log`
  - `files_db.db`

### 2️⃣ REST API (`api.py`)
- `/upload-file` → Upload a new file (auto-detected and moved)  
- `/scan-existing` → Scans all destination folders and adds missing DB entries  
- `/files` → Lists all records in the database (optional `file_type` filter)  

Example responses:
```json
POST /upload-file
{
  "status": "success",
  "message": "song.mp3 uploaded and moved to Audio"
}

---

🐳 Docker Setup

Build the image: docker build -t file-sorter-api .
Run the container: docker run -d -p 8000:8000 --name file-sorter-container file-sorter-api
Access the app:

- Swagger UI: http://localhost:8000/docs
- Redoc UI: http://localhost:8000/redoc

---

🧪 Example API Usage

1. Upload a File:
- POST /upload-file (use Swagger or Postman)
- Uploads file and moves it to appropriate folder.

2. Scan Existing Files:
- GET /scan-existing
- Refreshes DB with existing files in destination folders.

3. List Files:
- GET /files
- Returns all file records.

---

🧰 Requirements

Install dependencies (for local run): pip install -r requirements.txt

Run the watcher (local mode): python main.py

Run the API: uvicorn api:app --reload

