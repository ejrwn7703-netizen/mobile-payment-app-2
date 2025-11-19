from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    DEBUG = os.getenv("DEBUG", "False") == "True"
    TESTING = os.getenv("TESTING", "False") == "True"
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///app.db")
    GPS_SERVICE_URL = os.getenv("GPS_SERVICE_URL", "https://api.example.com/gps")
    QR_SCANNER_API_URL = os.getenv("QR_SCANNER_API_URL", "https://api.example.com/qr")
    BARCODE_SCANNER_API_URL = os.getenv("BARCODE_SCANNER_API_URL", "https://api.example.com/barcode")