from pathlib import Path
from datetime import datetime
import gdrive

if __name__ == "__main__":
    current_date = datetime.now().strftime("%Y-%m-%d")
    folder_id = gdrive.create_drive_folder(current_date)
    
    # sqlite3
    file_name = 'db.sqlite3'
    gdrive.upload_file(folder_id, file_name, mtype='sqlite3')
