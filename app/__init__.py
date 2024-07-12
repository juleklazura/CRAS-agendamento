from flask import Flask
from flask_wtf.csrf import CSRFProtect
from app.routes import bp

app = Flask(__name__)
csrf = CSRFProtect(app)

# Registrar o blueprint
app.register_blueprint(bp)
import config

# Configura a aplicação usando as configurações do arquivo config.py
app.config.from_object(config.Config)

from app import routes