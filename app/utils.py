from app.models import Agendamento
from datetime import datetime, timedelta, date

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
