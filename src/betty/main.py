import time
import threading
import random


from .skills import (
    battery_check,
    get_battery,
    has_battery,
    has_camera,
    speak,
    listen,
    get_time,
    cpu_info,
    cpu_check,
    uptime_info,
    volume_now,
    volume_up,
    volume_down,
    mute,
    open_program,
    open_steam_game,
    search_web,
    poweroff,
    reboot,
    calcular,
    ocr,
    analyze_screen,
    facial_check,
    get_temperature,
    pausar_midias,
    retomar_midias,
    pausar_temporario,
    retomar_temporario,
    proxima_media,
    anterior_media,
    audio_queue,
    monitor_attention,
    monitor_mouse_activity,
    mouse_active_within,
    monitor_spelling,
    register_interaction,
)

# Importamos o is_speaking para sincronização
from .skills.tts import is_speaking

from .qwen import (
    analyze_screen,
    classify,
    summarize_search,
    conversar,
    personalizar_resposta,
)

from .memory import save_memory, get_memory

history = []
print("[Betty] iniciada, eu diria")

modo_voz = False
task_in_progress = threading.Event()
screen_task_in_progress = threading.Event()
battery_available = False



def responder(texto, *, personalizar=True, fala=None):
    resposta = personalizar_resposta(texto) if personalizar else texto
    print(f"[Betty] {resposta}")

    pausar_temporario()

    try:
        speak(fala if fala is not None else resposta)
    finally:
        retomar_temporario()

def monitor(*, check_battery: bool):
    while True:
        bateria = battery_check() if check_battery else None

        if bateria:
            print(f"[Betty] {bateria}")
            speak(bateria)

        cpu = cpu_check()

        if cpu:
            print(f"[Betty] {cpu}")
            speak(cpu)

        time.sleep(40)


def monitor_screen():
    while True:
        time.sleep(random.randint(10 * 60, 30 * 60))

        screen_task_in_progress.set()
        try:
            descricao = analyze_screen()
            if not descricao:
                print("[Betty] A análise da tela não retornou uma descrição.")
                continue

            responder(f"Na tela: {descricao}")
        except Exception as error:
            print(f"[Betty] Erro ao analisar a tela: {error}")
        finally:
            screen_task_in_progress.clear()

def _processar_comando(comando):
    global modo_voz

    if comando.lower().strip() == "voz":
        modo_voz = True
        responder("Modo voz ativado.")
        return

    if comando.lower().strip() == "teclado":
        modo_voz = False
        responder("Modo teclado ativado.")
        return

    # Comando de parada no modo voz
    if modo_voz and comando.lower().strip() in ["pare", "sair", "desativar"]:
        modo_voz = False
        responder("Modo voz desativado.")
        return

    contexto = "\n".join(f"Usuário: {mensagem}" for mensagem in history[-10:])

    acao = classify(comando, contexto)

    #print(f"[Betty] IA: {acao!r}")

    history.append(comando)

    if acao == "TIME":
        resultado = f"São {get_time()}."
        responder(resultado)

    elif acao == "BATTERY":
        if not battery_available:
            responder("Este dispositivo não possui uma bateria disponível.")
            return

        battery = get_battery()
        if battery is None:
            responder("Não foi possível obter o nível da bateria.")
            return

        resultado = f"Bateria em {battery} por cento."
        responder(resultado)

    elif acao == "CPU":
        resultado = cpu_info()
        responder(resultado)

    elif acao == "UPTIME":
        resultado = uptime_info()
        responder(resultado)

    elif acao == "VOLUME_NOW":
        resultado = volume_now()
        responder(resultado)

    elif acao == "POWEROFF":
        poweroff()

    elif acao == "REBOOT":
        reboot()

    elif acao.startswith("VOLUME_UP"):
        partes = acao.split()

        if len(partes) > 1:
            quantidade = int(partes[1].replace("%", ""))
            resultado = volume_up(quantidade)
        else:
            resultado = volume_up()

        responder(resultado)

    elif acao == "TEMPERATURE":
        temperatura = int(round(get_temperature()))
        responder(
            f"{temperatura}°C",
            personalizar=False,
            fala=f"{temperatura} graus Celsius",
        )

    elif acao.startswith("VOLUME_DOWN"):
        partes = acao.split()

        if len(partes) > 1:
            quantidade = int(partes[1].replace("%", ""))
            resultado = volume_down(quantidade)
        else:
            resultado = volume_down()

        responder(resultado)

    elif acao == "MUTE":
        mute()
        resultado = volume_now()

        responder(resultado)

    elif acao == "NEXT_MEDIA":
        proxima_media()

    elif acao == "PREVIOUS_MEDIA":
        anterior_media()

    elif acao.startswith("OPEN_PROGRAM"):
        partes = acao.split(maxsplit=1)

        if len(partes) > 1:
            programa = partes[1]
            resultado = open_program(programa)

            responder(resultado)

    elif acao.startswith("OPEN_GAME"):
        jogo = acao.split(" ", 1)[1]
        resultado = open_steam_game(jogo)

        responder(resultado)

    elif acao.startswith("SEARCH_WEB"):
        partes = acao.split("|", 1)

        if len(partes) > 1:
            query = partes[1].strip()
        else:
            query = comando

        print(f"[Betty] Pesquisando: {query}")

        resultados = search_web(query)

        if not resultados:
            resultado = "Não encontrei resultados."
            responder(resultado)
            return

        resumo = summarize_search(query, resultados)

        print(f"[Betty] {resumo}")
        speak(resumo)
    elif acao.startswith("SAVE_MEMORY|"):
        comando_lower = comando.lower().strip()

        palavras_pergunta = (
            "qual ",
            "quem ",
            "onde ",
            "quando ",
            "como ",
            "por que ",
            "porque ",
            "o que ",
            "você lembra",
            "voce lembra",
        )

        eh_pergunta = comando_lower.endswith("?") or comando_lower.startswith(
            palavras_pergunta
        )

        if eh_pergunta:
            print(
                f"[Betty] "
                f"{personalizar_resposta('Isso parece ser uma pergunta. Memória não alterada.')}"
            )
            return

        partes = acao.split("|", 2)

        if len(partes) == 3:
            chave = partes[1].strip()
            valor = partes[2].strip()

            save_memory(chave, valor)

            responder("A Betty vai se lembrar disso.")
    elif acao.startswith("GET_MEMORY|"):
        partes = acao.split("|", 1)

        if len(partes) == 2:
            chave = partes[1].strip()
            valor = get_memory(chave)

            if valor is None:
                resultado = "Não tenho essa informação na memória. Eu diria"
            else:
                resultado = f"Na minha memória, é: {valor}. Eu diria"

            responder(resultado)
    elif acao == "POWEROFF":
        poweroff()
    elif acao == "REBOOT":
        reboot()
    elif acao.startswith("CALCULATE|"):
        expressao = acao.split("|", 1)[1].strip()

        try:
            resultado = calcular(expressao)
        except Exception:
            responder("Não consegui calcular isso.")
        else:
            responder(f"O resultado é: {resultado}.")
    elif acao == "READ_SCREEN":
        resultado = analyze_screen()
        responder(f"Li: {resultado}.")

    elif acao == "UNKNOWN":
        contexto = "\n".join(
            f"Usuário: {mensagem}"
            for mensagem in history[-10:]
        )

        resposta = conversar(comando, contexto)

        print(f"[Betty] {resposta}")
        speak(resposta)


def processar_comando(comando):
    task_in_progress.set()

    try:
        mensagem_retorno = register_interaction()
        if mensagem_retorno:
            print(f"[Betty] {mensagem_retorno}")
            speak(mensagem_retorno)

        _processar_comando(comando)
    finally:
        task_in_progress.clear()


def main():
    if modo_voz:
        # Espera o TTS terminar de falar antes de ouvir
        if is_speaking.is_set():
            time.sleep(0.1)
            return

        print("[Betty] Estou Ouvindo, eu diria")
        comando = listen()
        print(f"[Usuário]: {comando}")
        if comando:
            processar_comando(comando)
    else:
        comando = input(">>> ")
        if comando:
            processar_comando(comando)


def run():
    global battery_available

    battery_available = has_battery()
    camera_available = has_camera()

    if battery_available:
        print("[Betty] Bateria detectada; monitoramento ativado.")
    else:
        print("[Betty] Bateria não detectada; funções de bateria desativadas.")

    if camera_available:
        facial_check_thread = threading.Thread(
            target=facial_check,
            daemon=True,
        )
        facial_check_thread.start()
    else:
        print("[Betty] Câmera não detectada; detecção facial desativada.")

    monitor_thread = threading.Thread(
        target=monitor,
        kwargs={"check_battery": battery_available},
        daemon=True,
    )
    monitor_thread.start()

    screen_monitor_thread = threading.Thread(target=monitor_screen, daemon=True)
    screen_monitor_thread.start()
    mouse_activity_thread = threading.Thread(
        target=monitor_mouse_activity,
        daemon=True,
    )
    mouse_activity_thread.start()
    spelling_thread = threading.Thread(
        target=monitor_spelling,
        daemon=True,
    )
    spelling_thread.start()
    attention_thread = threading.Thread(
        target=monitor_attention,
        args=(
            lambda: (
                task_in_progress.is_set()
                or screen_task_in_progress.is_set()
                or is_speaking.is_set()
                or audio_queue.unfinished_tasks > 0
            ),
            mouse_active_within,
        ),
        daemon=True,
    )
    attention_thread.start()

    try:
        while True:
            main()
            time.sleep(0.1) # Cpu friendly

    except KeyboardInterrupt:
        print("\n[Betty] encerrada. Eu diria")
        

if __name__ == "__main__":
    run()
