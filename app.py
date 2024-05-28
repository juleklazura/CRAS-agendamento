from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from forms import AgendamentoForm
from models import Agendamento, db
from peewee import IntegrityError
from datetime import datetime, timedelta, date
from operator import itemgetter
import calendar

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha_chave_secreta'

def get_available_slots(data):
    hora_inicio_manha = datetime.strptime('08:30', '%H:%M').time()
    hora_fim_manha = datetime.strptime('11:30', '%H:%M').time()
    hora_inicio_tarde = datetime.strptime('13:00', '%H:%M').time()
    hora_fim_tarde = datetime.strptime('16:00', '%H:%M').time()
    intervalo = timedelta(minutes=15)

    horarios_disponiveis = []
    horario_atual = hora_inicio_manha
    while datetime.combine(data, horario_atual) <= datetime.combine(data, hora_fim_manha):
        horario_atual_str = horario_atual.strftime('%H:%M')
        if not Agendamento.select().where(Agendamento.data == data, Agendamento.horario == horario_atual_str).exists():
            horarios_disponiveis.append(horario_atual_str)
        horario_atual = (datetime.combine(data, horario_atual) + intervalo).time()

    horario_atual = hora_inicio_tarde
    while datetime.combine(data, horario_atual) <= datetime.combine(data, hora_fim_tarde):
        horario_atual_str = horario_atual.strftime('%H:%M')
        if not Agendamento.select().where(Agendamento.data == data, Agendamento.horario == horario_atual_str).exists():
            horarios_disponiveis.append(horario_atual_str)
        horario_atual = (datetime.combine(data, horario_atual) + intervalo).time()

    return horarios_disponiveis

def get_all_slots_for_month(year, month):
    _, last_day = calendar.monthrange(year, month)
    all_slots = {}
    for day in range(1, last_day + 1):
        current_date = date(year, month, day)
        if current_date.weekday() < 5:  # Exclude weekends
            available_slots = get_available_slots(current_date)
            agendamentos = Agendamento.select().where(Agendamento.data == current_date)
            scheduled_slots = {agendamento.horario.strftime('%H:%M') for agendamento in agendamentos}

            # Criar uma lista de horários com disponibilidade inicialmente
            all_times = [{'time': time, 'agendamento': None} for time in available_slots if time not in scheduled_slots]

            # Para os horários agendados, adicionar à lista
            for agendamento in agendamentos:
                all_times.append({'time': agendamento.horario.strftime('%H:%M'), 'agendamento': agendamento})

            # Ordenar todos os horários
            all_times.sort(key=lambda x: datetime.strptime(x['time'], '%H:%M'))

            # Criar um dicionário com os horários ordenados
            all_slots[current_date] = {
                'times': all_times
            }
    return all_slots

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
    today = date.today()
    agendamentos = Agendamento.select()
    slots = get_all_slots_for_month(today.year, today.month)
    # Ordenar os slots por data
    slots_sorted = dict(sorted(slots.items()))
    return render_template('listar.html', agendamentos=agendamentos, slots=slots_sorted, datetime=datetime)

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

    # Calcular os horários disponíveis para a data do agendamento
    horarios_disponiveis = get_available_slots(agendamento.data)
    
    # Adicionar o horário atual do agendamento se não estiver na lista de horários disponíveis
    agendamento_horario_str = agendamento.horario.strftime('%H:%M')
    if agendamento_horario_str not in horarios_disponiveis:
        horarios_disponiveis.append(agendamento_horario_str)
        horarios_disponiveis.sort()

    return render_template('editar.html', form=form, agendamento=agendamento, horarios=horarios_disponiveis, agendamento_horario_str=agendamento_horario_str)





@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    agendamento = Agendamento.get_or_none(Agendamento.id == id)
    if agendamento:
        agendamento.delete_instance()
        flash('Agendamento deletado com sucesso!', 'success')
    else:
        flash('Agendamento não encontrado!', 'danger')
    return redirect(url_for('listar'))

@app.route('/get_horarios_disponiveis', methods=['GET'])
def get_horarios_disponiveis():
    data_str = request.args.get('data')
    data = datetime.strptime(data_str, '%Y-%m-%d').date()
    horarios_disponiveis = get_available_slots(data)
    return jsonify(horarios_disponiveis)

if __name__ == '__main__':
    app.run(debug=True)