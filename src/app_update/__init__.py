import os
from src.logger import create_logger

logger = create_logger()

DOWNLOADS_FOLDER = os.path.join(os.getcwd(), "Downloads")

UPDATE_LATEST_URL = "https://api.github.com/repos/Manbeardo/MTGA_Draft_17Lands/releases/latest"
UPDATE_FILENAME = "MTGA_Draft_Tool_Setup.exe"

if not os.path.exists(DOWNLOADS_FOLDER):
    os.makedirs(DOWNLOADS_FOLDER)


