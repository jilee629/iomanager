from pathlib import Path
from datetime import datetime
import gdrive

BASE_DIR = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    current_date = datetime.now().strftime("%Y-%m-%d")
    folder_id = gdrive.create_drive_folder(current_date)
    
    # sqlite3
    dir_path = BASE_DIR
    file_name = 'db.sqlite3'
    gdrive.upload_file(folder_id, dir_path, file_name, mtype='sqlite')

    # text log
    dir_path = BASE_DIR / logs
    file_name = 'alimtalk.log'
    gdrive.upload_file(folder_id, dir_path, file_name)
