from peewee import Model, CharField, DateField, TimeField, BooleanField, PostgresqlDatabase
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
# Configuração do banco de dados SQLite
load_dotenv()

# Obter a string de conexão do banco de dados a partir do .env
database_url = os.getenv('DATABASE_URL')

# Configuração do banco de dados PostgreSQL
db = PostgresqlDatabase(database_url)


class BaseModel(Model):
    class Meta:
        database = db

class Agendamento(BaseModel):
    nome = CharField(max_length=100)
    cpf = CharField(max_length=14, null=True)
    telefone = CharField(max_length=15, null=True)
    data = DateField()
    horario = TimeField()
    presence = BooleanField(default=False)  # Adicionando o campo presence

class User(BaseModel):
    username = CharField(unique=True)
    password_hash = CharField()

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)




# Criar as tabelas se elas não existirem
if __name__ == '__main__':
    db.connect()
    db.create_tables([Agendamento, User], safe=True)
    