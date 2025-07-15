# config.py
import os
import pymysql
pymysql.install_as_MySQLdb()

class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'image_attendance'
    SECRET_KEY = 'super-secret-key'
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
