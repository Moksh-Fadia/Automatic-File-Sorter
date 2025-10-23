# 🧠 File Organizer API

A **backend system** that automatically organizes files from a source folder into categorized destinations (Audio, Videos, Images, Documents) while maintaining a complete record of every move inside an **SQLite database**.

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

**Logging**: Python’s `logging` module 

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
- `/files` → Lists all records in the database 

---

## 🧪 Example API Usage

1. Upload a File:
- POST /upload-file (use Swagger or Postman)
- Uploads file and moves it to appropriate folder.

2. List Files:
- GET /files
- Returns all file records.

---

## 🧰 Requirements

- Install dependencies (for local run): pip install -r requirements.txt

- Run the watcher (local mode): python main.py

- Run the API: uvicorn api:app --reload

- Access the API documentation:
1) Swagger UI: http://127.0.0.1:8000/docs
2) Redoc UI: http://127.0.0.1:8000/redoc

