import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
load_dotenv(os.path.join(basedir, '.flaskenv'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    AUDITORIA_LOG_FILE = os.environ.get('AUDITORIA_LOG_FILE') or \
        os.path.join(basedir, 'auditoria_log.txt')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')