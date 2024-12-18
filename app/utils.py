from app.models import Agendamento
from datetime import datetime, timedelta, date

def get_available_slots(data):
    hora_inicio_manha = datetime.strptime('08:30', '%H:%M').time()
    hora_fim_manha = datetime.strptime('11:30', '%H:%M').time()
    hora_inicio_tarde = datetime.strptime('13:00', '%H:%M').time()
    hora_fim_tarde = datetime.strptime('16:00', '%H:%M').time()
    intervalo = timedelta(minutes=30)

    # Obter todos os agendamentos do dia de uma vez
    agendamentos = Agendamento.select().where(Agendamento.data == data)
    horarios_ocupados = {agendamento.horario.strftime('%H:%M') for agendamento in agendamentos}
    horarios_indisponiveis = {agendamento.horario.strftime('%H:%M') for agendamento in agendamentos if agendamento.nome == 'Indisponível'}

    horarios_disponiveis = []

    def adicionar_horarios_disponiveis(hora_inicio, hora_fim):
        horario_atual = hora_inicio
        while datetime.combine(data, horario_atual) <= datetime.combine(data, hora_fim):
            horario_atual_str = horario_atual.strftime('%H:%M')
            if horario_atual_str not in horarios_ocupados and horario_atual_str not in horarios_indisponiveis:
                horarios_disponiveis.append(horario_atual_str)
            horario_atual = (datetime.combine(data, horario_atual) + intervalo).time()

    adicionar_horarios_disponiveis(hora_inicio_manha, hora_fim_manha)
    adicionar_horarios_disponiveis(hora_inicio_tarde, hora_fim_tarde)

    return sorted(horarios_disponiveis)

def get_all_slots_for_week(start_date):
    all_slots = {}
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        if current_date.weekday() < 5:  # Exclude weekends
            available_slots = get_available_slots(current_date)
            agendamentos = Agendamento.select().where(Agendamento.data == current_date)
            scheduled_slots = {agendamento.horario.strftime('%H:%M') for agendamento in agendamentos}

            all_times = [{'time': time, 'agendamento': None} for time in available_slots]
            all_times += [{'time': agendamento.horario.strftime('%H:%M'), 'agendamento': agendamento} for agendamento in agendamentos]
            all_times.sort(key=lambda x: datetime.strptime(x['time'], '%H:%M'))

            all_slots[current_date] = {
                'times': all_times
            }
    return all_slots
