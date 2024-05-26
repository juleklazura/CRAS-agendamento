from peewee import Model, CharField, DateField, TimeField, SqliteDatabase

# Configuração do banco de dados SQLite
db = SqliteDatabase('agendamentos.db')

class BaseModel(Model):
    class Meta:
        database = db

class Agendamento(BaseModel):
    nome = CharField(max_length=100)
    cpf = CharField(max_length=11, null=True)
    telefone = CharField(max_length=15, null=True)
    data = DateField()
    horario = TimeField()

# Criar as tabelas se elas não existirem
db.connect()
db.create_tables([Agendamento], safe=True)
