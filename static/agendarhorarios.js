var horariosPermitidos = [
    '08:30', '08:45',
    '09:00', '09:15', '09:30', '09:45',
    '10:00', '10:15', '10:30', '10:45',
    '11:00', '11:15', '11:30',
    '13:00', '13:15', '13:30', '13:45',
    '14:00', '14:15', '14:30', '14:45',
    '15:00', '15:15', '15:30', '15:45',
    '16:00'
];

// Função para desabilitar os horários fora do intervalo permitido
function atualizarHorarios() {
    var horarioSelect = document.getElementById('horario');
    var dataInput = document.getElementById('data');
    var selectedDate = new Date(dataInput.value);
    var today = new Date();
    
    // Verifica se o dia selecionado não é sábado nem domingo
    if (selectedDate.getDay() !== 5 && selectedDate.getDay() !== 6) {
        // Se a data selecionada for hoje
        if (selectedDate.setHours(0,0,0,0) === today.setHours(0,0,0,0)) {
            // Desabilita os horários que já passaram
            var horaAtual = today.getHours();
            var minutoAtual = today.getMinutes();
            horarioSelect.innerHTML = '<option value="" disabled selected>Selecione um horário</option>';
            for (var i = 0; i < horariosPermitidos.length; i++) {
                var horaMinuto = horariosPermitidos[i].split(':');
                var hora = parseInt(horaMinuto[0]);
                var minuto = parseInt(horaMinuto[1]);
                if ((hora > horaAtual || (hora === horaAtual && minuto > minutoAtual)) &&
                    ((hora >= 8 && hora < 12) || (hora >= 13 && hora < 16))) {
                    horarioSelect.innerHTML += '<option value="' + horariosPermitidos[i] + '">' + horariosPermitidos[i] + '</option>';
                }
            }
        } else if (selectedDate > today) { // Verifica se a data selecionada é depois de hoje
            // Habilita todos os horários permitidos
            horarioSelect.innerHTML = '<option value="" disabled selected>Selecione um horário</option>';
            for (var i = 0; i < horariosPermitidos.length; i++) {
                var horaMinuto = horariosPermitidos[i].split(':');
                var hora = parseInt(horaMinuto[0]);
                if ((hora >= 8 && hora < 12) || (hora >= 13 && hora <= 16)) {
                    horarioSelect.innerHTML += '<option value="' + horariosPermitidos[i] + '">' + horariosPermitidos[i] + '</option>';
                }
            }
        } else {
            // Se a data selecionada for antes de hoje, exibe uma mensagem de erro
            horarioSelect.innerHTML = '<option value="" disabled selected>Data/horário inválido</option>';
        }
    } else {
        // Desabilita todos os horários se for sábado ou domingo
        horarioSelect.innerHTML = '<option value="" disabled selected>Agendamentos apenas de segunda a sexta-feira</option>';
    }
}

// Adiciona um listener de mudança de data no input da data
document.getElementById('data').addEventListener('change', atualizarHorarios);

// Chama a função para desabilitar horários quando a página é carregada
atualizarHorarios();