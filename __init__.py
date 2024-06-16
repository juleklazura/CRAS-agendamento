from flask import Flask
from flask_wtf.csrf import CSRFProtect
from app.routes import bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha_chave_secreta'
csrf = CSRFProtect(app)

app.register_blueprint(bp)

if __name__ == '__main__':
    app.run(debug=True)