from peewee import Model, CharField, DateField, TimeField, SqliteDatabase, BooleanField

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
    presence = BooleanField(default=False)  # Adicionando o campo presence

# Criar as tabelas se elas não existirem
if __name__ == '__main__':
    db.connect()
    db.create_tables([Agendamento], safe=True)