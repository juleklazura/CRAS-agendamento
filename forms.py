from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Length

class AgendamentoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    cpf = StringField('CPF', validators=[Length(min=0, max=11)])
    telefone = StringField('Telefone', validators=[Length(min=0, max=15)])
    data = DateField('Data', validators=[DataRequired()], format='%Y-%m-%d')
    horario = TimeField('Horário', validators=[DataRequired()], format='%H:%M')
    submit = SubmitField('Agendar')
