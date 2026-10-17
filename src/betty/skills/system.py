from datetime import datetime
import psutil

def uptime_info():
    boot = datetime.fromtimestamp(psutil.boot_time())
    agora = datetime.now()

    uptime = agora - boot
    segundos = int(uptime.total_seconds())

    dias, resto = divmod(segundos, 86400)
    horas, resto = divmod(resto, 3600)
    minutos, _ = divmod(resto, 60)

    partes = []

    if dias:
        partes.append(f"{dias} {'dia' if dias == 1 else 'dias'}")

    if horas:
        partes.append(f"{horas} {'hora' if horas == 1 else 'horas'}")

    if minutos:
        partes.append(f"{minutos} {'minuto' if minutos == 1 else 'minutos'}")

    return "O sistema está ligado há " + ", ".join(partes) + "."

def cpu_percent():
    return psutil.cpu_percent(interval=1)


def cpu_freq():
    return psutil.cpu_freq().current


def cpu_info():
    usage = cpu_percent()
    freq = cpu_freq()

    return f"CPU em {usage:.0f} por cento, frequência atual de {freq / 1000:.2f} gigahertz."


def cpu_check():
    usage = cpu_percent()

    if usage >= 90:
        return f"Sério que você está sobrecarregando a CPU até {usage:.0f} por cento? Que criatura imprudente, eu diria."

    return None


def ram_percent():
    return psutil.virtual_memory().percent


def ram_info():
    ram = psutil.virtual_memory()

    usada = ram.used / (1024 ** 3)
    total = ram.total / (1024 ** 3)

    return f"Estou usando {usada:.1f} de {total:.1f} gigabytes de memória RAM."


def disk_info():
    disk = psutil.disk_usage("/")

    usada = disk.used / (1024 ** 3)
    total = disk.total / (1024 ** 3)

    return f"O disco está com {usada:.1f} de {total:.1f} gigabytes utilizados."


def temperatures():
    temps = psutil.sensors_temperatures()
    result = []

    for name, entries in temps.items():
        for entry in entries:
            result.append(f"{name}: {entry.current:.0f} graus")

    return ", ".join(result)
