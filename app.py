from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from forms import AgendamentoForm, LoginForm
from models import Agendamento, db, User
from peewee import IntegrityError
from datetime import datetime, timedelta, date, timezone
import calendar
from peewee import BooleanField
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha_chave_secreta'


def get_available_slots(data):
    hora_inicio_manha = datetime.strptime('08:30', '%H:%M').time()
    hora_fim_manha = datetime.strptime('11:15', '%H:%M').time()
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
    horarios_disponiveis = [time for time in horarios_disponiveis if not Agendamento.select().where(Agendamento.data == data, Agendamento.horario == time, Agendamento.nome == 'Indisponível').exists()]

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

def login_required(f):
    @wraps(f) 
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/ocupar/<data>/<horario>', methods=['POST'])
@login_required
def ocupar(data, horario):
    horario = datetime.strptime(horario, '%H:%M').time()
    data = datetime.strptime(data, '%Y-%m-%d').date()
    
    # Verificar se o horário está disponível antes de ocupar
    if not Agendamento.select().where(Agendamento.data == data, Agendamento.horario == horario).exists():
        Agendamento.create(
            nome='Indisponível',
            cpf=None,
            telefone=None,
            data=data,
            horario=horario,
            presence=False
        )
        flash('Horário marcado como Indisponível!', 'success')
    else:
        flash('Erro: O horário já está Indisponível!', 'danger')
    
    # Redirecionar para a página da semana de listagem
    year, week = data.isocalendar()[0], data.isocalendar()[1]
    return redirect(url_for('listar', year=year, week=week))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    # Verificar se a conta está bloqueada
    blocked_until = session.get('blocked_until')
    if blocked_until and datetime.now(timezone.utc) < blocked_until:
        seconds_left = (blocked_until - datetime.now(timezone.utc)).total_seconds()
        flash(f'Sua conta está bloqueada. Tente novamente após {int(seconds_left)} segundos.', 'danger')
        form.username.render_kw = {'disabled': True}  # Desativar o campo de nome de usuário
        form.password.render_kw = {'disabled': True}  # Desativar o campo de senha
        form.submit.render_kw = {'disabled': True}  # Desativar o botão de envio
        return render_template('login.html', form=form)

    if form.validate_on_submit():
        user = User.get_or_none(User.username == form.username.data)
        if user and user.verify_password(form.password.data):
            session['user_id'] = user.id
            flash('Login realizado com sucesso!', 'success')
            # Reiniciar contagem de tentativas de login e desbloquear a conta
            session.pop('login_attempts', None)
            session.pop('blocked_until', None)
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas. Por favor, tente novamente.', 'danger')
            # Se o login falhar, aumente o contador de tentativas de login malsucedidas
            session.setdefault('login_attempts', 0)
            session['login_attempts'] += 1
            # Bloqueie a conta após 3 tentativas de login malsucedidas
            if session['login_attempts'] >= 5:
                flash('Número máximo de tentativas de login excedido. Sua conta foi bloqueada.', 'danger')
                # Define um tempo de bloqueio de 5 minutos (300 segundos)
                session['blocked_until'] = datetime.now(timezone.utc) + timedelta(seconds=120)
            return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/agendar', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
def toggle_presence(id):
    agendamento = Agendamento.get_or_none(Agendamento.id == id)
    if agendamento:
        agendamento.presence = not agendamento.presence  # Inverte o valor de presence
        agendamento.save()
        flash('Status de presença atualizado com sucesso!', 'success')
    else:
        flash('Agendamento não encontrado!', 'danger')
    
    # Redirecionar para a página da semana de listagem
    if agendamento:
        year, week = agendamento.data.isocalendar()[0], agendamento.data.isocalendar()[1]
    else:
        # Caso o agendamento não seja encontrado, redirecione para a semana atual
        today = date.today()
        year, week = today.isocalendar()[0], today.isocalendar()[1]
    return redirect(url_for('listar', year=year, week=week))


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
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
@login_required
def deletar(id):
    agendamento = Agendamento.get_or_none(Agendamento.id == id)
    if agendamento:
        agendamento.delete_instance()
        flash('Agendamento deletado com sucesso!', 'success')
    else:
        flash('Agendamento não encontrado!', 'danger')
    
    # Redirecionar para a página da semana de listagem
    if agendamento:
        year, week = agendamento.data.isocalendar()[0], agendamento.data.isocalendar()[1]
    else:
        # Caso o agendamento não seja encontrado, redirecione para a semana atual
        today = date.today()
        year, week = today.isocalendar()[0], today.isocalendar()[1]
    return redirect(url_for('listar', year=year, week=week))

@app.route('/get_horarios_disponiveis', methods=['GET'])
@login_required
def get_horarios_disponiveis():
    data_str = request.args.get('data')
    data = datetime.strptime(data_str, '%Y-%m-%d').date()
    horarios_disponiveis = get_available_slots(data)
    return jsonify(horarios_disponiveis)

if __name__ == '__main__':
    app.run(debug=True)