import psutil


def get_battery():
    battery = psutil.sensors_battery().percent
    if battery is None:
        return None
    return int(battery)


def get_plugged():
    return psutil.sensors_battery().power_plugged


def battery_check():
    battery = get_battery()
    plugged = get_plugged()

    if battery <= 15 and not plugged:
        return f"Francamente, a bateria está em {battery} por cento e caindo. Coloque para carregar agora mesmo, eu diria."
    if battery >= 80 and plugged:
        return f"A bateria já chegou a {battery} por cento. Tire do carregador antes que pegue fogo, eu diria."
    return None
