import psutil


def has_battery() -> bool:
    try:
        return psutil.sensors_battery() is not None
    except (NotImplementedError, OSError) as error:
        print(f"[Betty] Não foi possível verificar a bateria: {error}")
        return False


def get_battery() -> int | None:
    battery = psutil.sensors_battery()
    if battery is None or battery.percent is None:
        return None
    return int(battery.percent)


def get_plugged() -> bool | None:
    battery = psutil.sensors_battery()
    if battery is None:
        return None
    return battery.power_plugged


def battery_check() -> str | None:
    battery = get_battery()
    plugged = get_plugged()

    if battery is None or plugged is None:
        return None

    if battery <= 15 and not plugged:
        return f"Francamente, a bateria está em {battery} por cento e caindo. Coloque para carregar agora mesmo, eu diria."
    if battery >= 80 and plugged:
        return f"A bateria já chegou a {battery} por cento. Tire do carregador antes que pegue fogo, eu diria."
    return None
