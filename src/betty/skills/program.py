import subprocess


PROGRAMS = {
    "firefox": ["firefox"],
    "librewolf": ["librewolf"],
    "zed": ["zed"],
    "kitty": ["kitty"],
    "terminal": ["kitty"],
    "prism": ["flatpak", "run", "org.prismlauncher.PrismLauncher"],
    "minecraft": ["flatpak", "run", "org.prismlauncher.PrismLauncher"],
}
STEAM_GAMES = {
    "ddlc": "698780",
}

def open_program(program):
    if program not in PROGRAMS:
        return f"Não conheço o programa {program}. eu diria"

    subprocess.Popen(
        PROGRAMS[program],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return f"Abrindo {program}. eu diria"
def open_steam_game(game):
    if game not in STEAM_GAMES:
        return f"Não conheço o jogo {game}. eu diria"

    subprocess.Popen(
        [
            "steam",
            f"steam://run/{STEAM_GAMES[game]}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return f"Abrindo {game}.eu diria"
