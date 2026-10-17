from datetime import datetime
def get_time():
    agora = datetime.now()
    hora_atual = agora.strftime("%H:%M:%S")
    return hora_atual
