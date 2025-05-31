import os
from app.taiga_client import TaigaClient

def create_taiga_client():
    base_url = os.getenv("TAIGA_BASE_URL")
    username = os.getenv("TAIGA_USERNAME")
    password = os.getenv("TAIGA_PASSWORD")
    projectid = int(os.getenv("TAIGA_PROJECT_ID"))

    return TaigaClient(base_url, username, password, projectid)