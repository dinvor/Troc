import os

class Config:
    SECRET_KEY = "change_me"
    UPLOAD_FOLDER = os.path.join("static", "uploads")
