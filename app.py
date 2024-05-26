from flask import Flask, render_template, redirect, url_for, request, flash
from forms import AgendamentoForm
from models import Agendamento, db
from peewee import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha_chave_secreta'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    form = AgendamentoForm()
    if form.validate_on_submit():
        try:
            novo_agendamento = Agendamento.create(
                nome=form.nome.data,
                cpf=form.cpf.data,
                telefone=form.telefone.data,
                data=form.data.data,
                horario=form.horario.data
            )
            flash('Agendamento criado com sucesso!', 'success')
            return redirect(url_for('listar'))
        except IntegrityError:
            flash('Erro: CPF já cadastrado!', 'danger')
    return render_template('agendar.html', form=form)

@app.route('/listar')
def listar():
    agendamentos = Agendamento.select()
    return render_template('listar.html', agendamentos=agendamentos)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    agendamento = Agendamento.get_or_none(Agendamento.id == id)
    if not agendamento:
        flash('Agendamento não encontrado!', 'danger')
        return redirect(url_for('listar'))

    form = AgendamentoForm(obj=agendamento)
    if form.validate_on_submit():
        agendamento.nome = form.nome.data
        agendamento.cpf = form.cpf.data
        agendamento.telefone = form.telefone.data
        agendamento.data = form.data.data
        agendamento.horario = form.horario.data
        agendamento.save()
        flash('Agendamento atualizado com sucesso!', 'success')
        return redirect(url_for('listar'))
    return render_template('editar.html', form=form)

@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    agendamento = Agendamento.get_or_none(Agendamento.id == id)
    if agendamento:
        agendamento.delete_instance()
        flash('Agendamento deletado com sucesso!', 'success')
    else:
        flash('Agendamento não encontrado!', 'danger')
    return redirect(url_for('listar'))

if __name__ == '__main__':
    app.run(debug=True)
 