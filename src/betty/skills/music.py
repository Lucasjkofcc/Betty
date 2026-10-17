import subprocess

def musica(comando):
    acoes = {
        "proxima": "next",
        "anterior": "previous",
        "pausar": "pause",
        "continuar": "play",
    }

    acao = acoes.get(comando)

    if acao:
        subprocess.run(["playerctl", "--player=spotify", acao],check=False)