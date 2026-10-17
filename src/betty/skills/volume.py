import subprocess

def volume_now():
    result = subprocess.run(
        ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
        capture_output=True,
        text=True
    )

    parts = result.stdout.split()

    volume = round(float(parts[1]) * 100)
    muted = "[MUTED]" in parts

    if muted:
        return f"Volume em {volume} por cento. Está mudo."

    return f"Volume em {volume} por cento."
def volume_up(amount=5):
    subprocess.run(
        ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{amount}%+"]
    )
    return f"Aumentando o volume em {amount} por cento."


def volume_down(amount=5):
    subprocess.run(
        ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{amount}%-"]
    )
    return f"Diminuindo o volume em {amount} por cento."

def mute():
    subprocess.run(
        ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"]
    )

    return volume_now()
