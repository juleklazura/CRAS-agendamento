from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from forms import AgendamentoForm
from models import Agendamento, db
from peewee import IntegrityError
from datetime import datetime, timedelta, date
import calendar
from peewee import BooleanField
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

def get_all_slots_for_week(start_date):
    all_slots = {}
    for i in range(7):
        current_date = start_date + timedelta(days=i)
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
    min_date = date.today().strftime('%Y-%m-%d')  # Define a data mínima como o dia atual
    form.data.render_kw = {'min': min_date}  # Passa a data mínima para o campo de data

    if form.validate_on_submit():
        selected_date = form.data.data
        today = date.today()

        # Verificar se a data selecionada é anterior ao dia atual
        if selected_date < today:
            flash('Não é possível agendar em dias anteriores ao atual!', 'danger')
            return render_template('agendar.html', form=form, min_date=min_date)

        # Verificar se a data selecionada é um sábado ou domingo
        if selected_date.weekday() >= 5:
            flash('Não é possível agendar nos sábados e domingos!', 'danger')
            return render_template('agendar.html', form=form, min_date=min_date)

        # Verificar se o CPF já está cadastrado, apenas se não estiver vazio
        if form.cpf.data.strip():  # Verificar se o CPF não está vazio
            if Agendamento.select().where(Agendamento.cpf == form.cpf.data).exists():
                flash('Erro: CPF já cadastrado!', 'danger')
                return render_template('agendar.html', form=form, min_date=min_date)

        try:
            novo_agendamento = Agendamento.create(
                nome=form.nome.data,
                cpf=form.cpf.data,
                telefone=form.telefone.data,
                data=selected_date,
                horario=form.horario.data
            )
            flash('Agendamento criado com sucesso!', 'success')  # Mensagem de sucesso
            return redirect(url_for('listar'))
        except IntegrityError:
            flash('Erro: CPF já cadastrado!', 'danger')
            return render_template('agendar.html', form=form, min_date=min_date)

    return render_template('agendar.html', form=form, min_date=min_date)


@app.route('/listar', defaults={'year': None, 'week': None})
@app.route('/listar/<int:year>/<int:week>')
def listar(year, week):
    today = date.today()
    if not year or not week:
        year, week = today.isocalendar()[0], today.isocalendar()[1]
    
    start_date = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w").date()
    agendamentos = Agendamento.select()
    slots = get_all_slots_for_week(start_date)
    
    # Ordenar os slots por data
    slots_sorted = dict(sorted(slots.items()))

    return render_template('listar.html', agendamentos=agendamentos, slots=slots_sorted, datetime=datetime, year=year, week=week)

@app.route('/toggle_presence/<int:id>', methods=['POST'])
def toggle_presence(id):
    agendamento = Agendamento.get_or_none(Agendamento.id == id)
    if agendamento:
        agendamento.presence = not agendamento.presence  # Inverte o valor de presence
        agendamento.save()
        flash('Status de presença atualizado com sucesso!', 'success')
    else:
        flash('Agendamento não encontrado!', 'danger')
    return redirect(url_for('listar'))


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    agendamento = Agendamento.get_or_none(Agendamento.id == id)
    if not agendamento:
        flash('Agendamento não encontrado!', 'danger')
        return redirect(url_for('listar'))

    form = AgendamentoForm(obj=agendamento)
    min_date = date.today().strftime('%Y-%m-%d')  # Define a data mínima como o dia atual
    form.data.render_kw = {'min': min_date}  # Passa a data mínima para o campo de data

    if form.validate_on_submit():
        selected_date = form.data.data
        today = date.today()
        
        # Verificar se a data selecionada é anterior ao dia atual
        if selected_date < today:
            flash('Não é possível agendar em dias anteriores ao atual!', 'danger')
            return render_template('editar.html', form=form, agendamento=agendamento, agendamento_horario_str=agendamento.horario.strftime('%H:%M'), min_date=min_date, horarios=get_available_slots(agendamento.data))

        # Verificar se a data selecionada é um sábado ou domingo
        if selected_date.weekday() >= 5:
            flash('Não é possível agendar nos sábados e domingos!', 'danger')
            return render_template('editar.html', form=form, agendamento=agendamento, agendamento_horario_str=agendamento.horario.strftime('%H:%M'), min_date=min_date, horarios=get_available_slots(agendamento.data))
        
        selected_horario = form.horario.data.strftime('%H:%M')
        current_horario = agendamento.horario.strftime('%H:%M')

        # Obter todos os horários disponíveis para a nova data selecionada
        horarios_disponiveis = get_available_slots(selected_date)

        # Adicionar o horário original de volta aos horários disponíveis se a data for a mesma
        if selected_date == agendamento.data and current_horario not in horarios_disponiveis:
            horarios_disponiveis.append(current_horario)
        
        horarios_disponiveis.sort()

        if selected_horario not in horarios_disponiveis:
            flash('O horário selecionado não está mais disponível!', 'danger')
            return render_template('editar.html', form=form, agendamento=agendamento, agendamento_horario_str=current_horario, min_date=min_date, horarios=horarios_disponiveis)

        if form.cpf.data.strip():  # Verificar se o CPF não está vazio
            # Verificar se o CPF já está cadastrado
            if Agendamento.select().where(Agendamento.cpf == form.cpf.data, Agendamento.id != id).exists():
                flash('Erro: CPF já cadastrado!', 'danger')
                return render_template('editar.html', form=form, agendamento=agendamento, agendamento_horario_str=agendamento.horario.strftime('%H:%M'), min_date=min_date, horarios=get_available_slots(agendamento.data))

        agendamento.nome = form.nome.data
        agendamento.cpf = form.cpf.data
        agendamento.telefone = form.telefone.data
        agendamento.data = form.data.data
        agendamento.horario = form.horario.data
        agendamento.save()
        flash('Agendamento atualizado com sucesso!', 'success')
        return redirect(url_for('listar'))

    # Garantir que o horário atual esteja disponível no formulário de edição
    horarios = get_available_slots(agendamento.data)
    if agendamento.horario.strftime('%H:%M') not in horarios:
        horarios.append(agendamento.horario.strftime('%H:%M'))
        horarios.sort()

    return render_template('editar.html', form=form, agendamento=agendamento, agendamento_horario_str=agendamento.horario.strftime('%H:%M'), min_date=min_date, horarios=horarios)

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