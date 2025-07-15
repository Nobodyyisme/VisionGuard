# config.py
import os


class Config:
    MYSQL_HOST = '0.tcp.in.ngrok.io'
    MYSQL_PORT = 18473  # This is important to add
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''  # Add your local MySQL password if set
    MYSQL_DB = 'image_attendance'
    SECRET_KEY = 'super-secret-key'
    JWT_SECRET_KEY = os.getenv("bbbvvv38c8c26e13caa42d88a54b294ad47e3c27ee787170731e0fc21a45bb61")
