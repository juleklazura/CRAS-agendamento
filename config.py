import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'minha_chave_secreta'
    DATABASE_URL = os.environ.get('DATABASE_URL')