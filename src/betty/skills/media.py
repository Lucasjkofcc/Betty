import subprocess as sp


def players_tocando():
    resultado = sp.run(
        ["playerctl", "-a", "status"],
        capture_output=True,
        text=True,
    )

    tocando = []

    for linha in resultado.stdout.splitlines():
        if "Playing" in linha:
            player = linha.rsplit(" ", 1)[0]
            tocando.append(player)

    return tocando


def pausar_midias():
    players = players_tocando()

    for player in players:
        sp.run(
            ["playerctl", "--player", player, "pause"],
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )

    return players


def retomar_midias(players):
    for player in players:
        sp.run(
            ["playerctl", "--player", player, "play"],
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
        )
def pausar_temporario():
    sp.Popen(["playerctl", "pause"])
def retomar_temporario():
    sp.Popen(["playerctl", "play"])