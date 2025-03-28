# Automatic File Sorter

An automatic file sorting tool that organizes files into designated folders (Music, Videos, Images, Documents) based on their file types. Built using Python, leveraging `watchdog` for real-time monitoring.

## Features

- ✅ Automatically monitors a specified folder for changes.
- ✅ Sorts files into subfolders (`Music`, `Videos`, `Images`, `Documents`) based on file type.
- ✅ Uses multithreading for faster file processing.
- ✅ Provides a simple GUI using `Tkinter`.
- ✅ Logs all activities in a `file_mover.log` file.
- ✅ Supports undoing file moves through a `undo_log.json` file.

## Technologies Used

- **Python Modules:**
  - `os`, `shutil`, `json`, `logging`, `threading`
  - `watchdog` for monitoring file changes in real-time
  - `concurrent.futures` for multi-threading support

## Supported File Types

- **Images:** jpg, jpeg, png, gif, webp, tiff, bmp, svg, etc.
- **Videos:** mp4, avi, mov, flv, mpeg, etc.
- **Music:** mp3, wav, m4a, flac, aac, etc.
- **Documents:** doc, docx, pdf, xls, xlsx, ppt, pptx, etc.

## Folder Structure

automatic-file-sorter/
│
├── your_script_name.py        # The main Python script
├── file_mover.log             # Log file for all sorting operations
├── undo_log.json              # Log file for undoing file moves
├── README.md                  # Project documentation
├── Music/                     # Directory for sorted music files
├── Videos/                    # Directory for sorted video files
├── Images/                    # Directory for sorted image files
└── Documents/                 # Directory for sorted document files
