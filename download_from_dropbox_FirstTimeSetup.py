import os
from dotenv import load_dotenv, set_key
import webbrowser
from dropbox import DropboxOAuth2FlowNoRedirect

CONFIG_FILE = "download_from_dropbox.env"
load_dotenv(CONFIG_FILE)

def first_time_config():
    APP_KEY = os.getenv("APP_KEY")
    APP_SECRET = os.getenv("APP_SECRET")
    
    if not APP_KEY or not APP_SECRET:
        print("APP_KEY or APP_SECRET not found in download_from_dropbox.env. Please add them.")
        exit(1)
    
    flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET, token_access_type="offline")
    authorize_url = flow.start()

    print("Opening Dropbox authorization URL in your browser...")
    webbrowser.open(authorize_url)

    auth_code = input("Paste the authorization code here: ").strip()
    oauth_result = flow.finish(auth_code)

    set_key(CONFIG_FILE, "REFRESH_TOKEN", oauth_result.refresh_token)

    print("Configuration saved to .env")

# Main execution
if __name__ == "__main__":
    first_time_config()


