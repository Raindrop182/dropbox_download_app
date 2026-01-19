import os
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import dropbox
from dropbox.files import FileMetadata, FolderMetadata
from dropbox import DropboxOAuth2FlowNoRedirect

load_dotenv("download_from_dropbox.env")

APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
DROPBOX_FOLDER = os.getenv("DROPBOX_FOLDER")
DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 4*1024*1024))  # default 4 MB

if not all([APP_KEY, APP_SECRET, REFRESH_TOKEN, DROPBOX_FOLDER, DOWNLOAD_FOLDER]):
    raise ValueError("Missing configuration in .env. Provide APP_KEY, APP_SECRET, REFRESH_TOKEN, DROPBOX_FOLDER, DOWNLOAD_FOLDER.")
    
# Ensure the download folder exists
try:
    Path(DOWNLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
except Exception as e:
    raise ValueError(f"Failed to create download folder '{DOWNLOAD_FOLDER}': {e}")
    
# --- Initialize Dropbox client ---
dbx = dropbox.Dropbox(
    app_key=APP_KEY,
    app_secret=APP_SECRET,
    oauth2_refresh_token=REFRESH_TOKEN
)

def download_file(dbx,dbx_path, local_path):
    """Download a single file from Dropbox in chunks (good for large files)."""
    print(f"Downloading: {dbx_path} -> {local_path}")
    try:
        metadata, res = dbx.files_download(dbx_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True) #makes the download folder if it doesn't exist
        
        #download the file in chunks (good for large files)
        with open(local_path, 'wb') as f:
            for chunk in res.iter_content(CHUNK_SIZE):
                f.write(chunk)
    except Exception as e:
        print(f"Error downloading {dbx_path}: {e}")
        
def download_folder(dbx,dbx_folder, local_folder):
    """Download all files in a Dropbox folder."""
    try:
        result = dbx.files_list_folder(dbx_folder) #collect a list of all files in the folder
    except dropbox.exceptions.ApiError as e:
        print(f"Failed to list folder {dbx_folder}: {e}")
        return
    
    download_list(dbx,result,local_folder)

    #result=dbx.files_lsit_folder(dbx_folder) only returns the first 2000 elements in the folder.
    #if there are more than 2000 files, this next section iterates through them
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        
        download_list(dbx,result,local_folder)
        
def download_list(dbx,result,local_folder):
    for entry in result.entries: 
        local_path = os.path.join(local_folder, entry.name)
        
        if isinstance(entry, FileMetadata):
            if os.path.exists(local_path) and os.path.getsize(local_path) == entry.size:
                print(f"Skipping (already exists): {local_path}")
                continue
            download_file(dbx,entry.path_lower, local_path) #if it is a file, download it
        elif isinstance(entry, FolderMetadata):
            download_folder(dbx,entry.path_lower, local_path) #if it is a subfolder, download the files inside that subfolder
        
def first_time_config(APP_KEY, APP_SECRET):
    flow = DropboxOAuth2FlowNoRedirect(
        APP_KEY,
        APP_SECRET,
        token_access_type="offline"
    )

    # Step A: open this URL in your browser
    authorize_url = flow.start()
    print("1) Go to this URL and click Allow:")
    print(authorize_url)

    # Step B: Dropbox shows you a short code
    auth_code = input("2) Paste the authorization code here: ").strip()

    # Step C: exchange code for tokens
    oauth_result = flow.finish(auth_code)

    print("\nSAVE THIS — YOU WILL NOT SEE IT AGAIN")
    print("Refresh token:", oauth_result.refresh_token)

if __name__ == "__main__":
    print(f"Downloading Dropbox folder '{DROPBOX_FOLDER}' to local folder '{DOWNLOAD_FOLDER}'...\n")
    download_folder(dbx, DROPBOX_FOLDER, DOWNLOAD_FOLDER)
    print("\nDownload completed!")
    
if __name__ == '__main__':
        
    download_folder(dbx,DROPBOX_FOLDER, DOWNLOAD_FOLDER)
