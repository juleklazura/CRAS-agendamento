from app import app  # Importa a aplicação do pacote 'app'
import config

# Configura a aplicação usando as configurações do arquivo config.py
app.config.from_object(config.Config)

if __name__ == '__main__':
    app.run(debug=True)