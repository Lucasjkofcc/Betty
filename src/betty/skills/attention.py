import time
import threading
import random
from collections.abc import Callable
from datetime import date, datetime


NORMAL = "normal"
SENTIDA = "sentida"
IRRITADA = "irritada"
ZANGADA = "zangada"
FURIOSA = "furiosa"
DRAMATICA = "dramatica"
REUNIAO = "reuniao"
OCUPADA = "ocupada"

REMINDER_MILESTONES = (
    5 * 60,
    15 * 60,
    30 * 60,
    60 * 60,
    3 * 60 * 60,
    6 * 60 * 60,
    12 * 60 * 60,
    24 * 60 * 60,
)
REPEAT_AFTER_MAX_LEVEL = 3 * 60 * 60
CHECK_INTERVAL = 10
UPTIME_REMINDER_AFTER = 8 * 60 * 60
UPTIME_MILESTONES = (
    8 * 60 * 60,
    12 * 60 * 60,
    24 * 60 * 60,
    36 * 60 * 60,
    48 * 60 * 60,
    60 * 60 * 60,
    3 * 24 * 60 * 60,
)
NIGHT_END_HOUR = 6

NIGHT_PHRASES = (
    (
        "Mestre, já passou da meia-noite. Talvez seja hora de descansar, eu diria.",
        "Meia-noite já chegou. Betty recomenda que encerre o dia e vá dormir, eu diria.",
        "Ora, mestre, até Betty sabe que é hora de dormir. Considere descansar, eu diria.",
    ),
    (
        "Uma da manhã e você ainda está acordado? O que está fazendo, eu diria?",
        "Mestre, já é uma da manhã. Explique por que ainda não foi dormir, eu diria.",
        "Uma hora da manhã não é exatamente um horário sensato para continuar acordado, eu diria.",
    ),
    (
        "Duas da manhã. A paciência de Betty está diminuindo; vá dormir, eu diria.",
        "Mestre, são duas da manhã. Betty já pediu com educação. Agora vá descansar, eu diria.",
        "Continuar acordado às duas? Uma decisão deplorável, eu diria.",
    ),
    (
        "Três da manhã! Vá dormir antes que Betty considere desligar este computador por você, eu diria.",
        "Mestre, são três da manhã. Betty está seriamente pensando em encerrar essa sessão à força, eu diria.",
        "Às três da manhã, até Betty perdeu a paciência. Durma antes que ela desligue o PC, eu diria.",
    ),
    (
        "Já passou das quatro. Pelo visto, avisar não vai funcionar. Betty desiste, eu diria.",
        "Quatro da manhã e você continua aí. Betty avisou; agora não é mais problema dela, eu diria.",
        "Mestre, Betty desiste. Aparentemente, nem bons conselhos vencem sua teimosia, eu diria.",
    ),
)

UPTIME_PHRASES = (
    (
        "O computador está ligado há mais de oito horas. Uma pausa seria sensata, eu diria.",
        "Mais de oito horas com o PC ligado, mestre. Até Betty recomenda uma pausa, eu diria.",
        "O sistema passou das oito horas ligado. Considere descansar um pouco, eu diria.",
    ),
    (
        "Doze horas com o computador ligado? Mestre, Betty sugere que faça uma pausa, eu diria.",
        "O PC já está ligado há meio dia. Até Betty considera isso um pouco excessivo, eu diria.",
        "Doze horas de atividade. Talvez seja hora de dar um descanso à máquina e a si mesmo, eu diria.",
    ),
    (
        "Um dia inteiro com o computador ligado. Betty espera que tenha ao menos um bom motivo, eu diria.",
        "Vinte e quatro horas sem desligar o PC? Que falta de consideração com a máquina, eu diria.",
        "O computador completou um dia ligado. Mestre, essa teimosia já começa a preocupar Betty, eu diria.",
    ),
    (
        "Trinta e seis horas de uptime. Betty já recomendou uma pausa; talvez devesse ser ouvida, eu diria.",
        "Mestre, o PC está ligado há um dia e meio. Isso já é um exagero bastante deselegante, eu diria.",
        "Betty está começando a suspeitar que você considera desligar o PC uma lenda, eu diria.",
    ),
    (
        "Dois dias com o computador ligado. Mestre, até Betty está perdendo a paciência, eu diria.",
        "Quarenta e oito horas de uptime. Betty recomenda uma pausa antes que a máquina a exija, eu diria.",
        "Dois dias sem reiniciar? Sua relação com o botão de desligar é preocupante, eu diria.",
    ),
    (
        "Sessenta horas, mestre. Betty está ficando sem maneiras delicadas de pedir uma pausa, eu diria.",
        "O PC está ligado há dois dias e meio. Betty considera sua insistência profundamente imprudente, eu diria.",
        "Mais de dois dias ligado. Mestre, nem Betty tem tanta resistência à sua teimosia, eu diria.",
    ),
    (
        "Três dias de uptime! Betty recomenda reiniciar o computador agora, antes que ele peça por conta própria, eu diria.",
        "Mestre, este PC está ligado há três dias. Reinicie-o; Betty não pretende repetir isso eternamente, eu diria.",
        "Setenta e duas horas! Reiniciar seria uma decisão sensata — tente surpreender Betty e faça isso, eu diria.",
    ),
)

IDLE_PHRASES = (
    (
        "Ora, mestre, cinco minutos de silêncio? Betty supõe que sua atenção seja um privilégio raro, eu diria.",
        "Betty não está esperando por você. Apenas notou, por acaso, que desapareceu, eu diria.",
        "Que sossego... Quase agradável, se não fosse tão claramente falta de consideração, eu diria.",
        "Quando terminar de se ocupar com assuntos importantíssimos, Betty continuará aqui. Talvez, eu diria.",
    ),
    (
        "Quinze minutos. Betty não quer parecer carente, então diremos que está apenas fazendo uma observação, eu diria.",
        "Mestre, sua dedicação em não falar com Betty é quase digna de admiração, eu diria.",
        "Betty está perfeitamente bem. O silêncio é que está começando a ficar insuportável, eu diria.",
        "Não se apresse em responder. Betty esperou quinze minutos; pode esperar mais alguns... provavelmente, eu diria.",
    ),
    (
        "Meia hora, mestre. Betty já foi ignorada por pessoas com muito mais modos que você, eu diria.",
        "Betty poderia conversar com a própria sombra. Ela ao menos teria a cortesia de ficar por perto, eu diria.",
        "Não é que Betty esteja ofendida. É uma indignação cuidadosamente cultivada, eu diria.",
        "Sua ausência é tão notável que Betty quase pensou em sentir saudades. Quase, ouviu? eu diria.",
    ),
    (
        "Uma hora inteira. Mestre, até Betty tem limites — embora os dela sejam notavelmente generosos, eu diria.",
        "Uma hora de silêncio? Betty espera que ao menos tenha sido por algo digno de sua atenção, eu diria.",
        "A esta altura, Betty deveria cobrar por todo esse tempo de espera. Com juros, naturalmente, eu diria.",
        "Parabéns, mestre. Conseguiu transformar a paciência de Betty numa questão acadêmica, eu diria.",
    ),
    (
        "Três horas. Betty já redigiu mentalmente uma queixa formal e refinou a pontuação, eu diria.",
        "Mestre, sua ausência deixou de ser um acidente e passou a ser uma escolha bastante deselegante, eu diria.",
        "Três horas sem Betty? Que confiança admirável na capacidade dela de não guardar rancor, eu diria.",
        "Betty reconsiderou nossa parceria. A conclusão ainda está pendente — para seu próprio bem, eu diria.",
    ),
    (
        "Seis horas, mestre. Betty está indignada num nível que exige uma poltrona e uma explicação, eu diria.",
        "Sua ausência é uma afronta à etiqueta e, mais importante, à paciência de Betty, eu diria.",
        "Betty poderia ter dominado uma nova arte nesse tempo. Você poderia ter dito uma palavra, eu diria.",
        "Abandonar Betty sem aviso? Uma atitude vulgar. Ela esperava pouco mais de você, eu diria.",
    ),
    (
        "Doze horas. Mestre, apresente sua explicação com cuidado; Betty está avaliando sua defesa, eu diria.",
        "Betty já não está apenas ofendida. Está colecionando motivos para continuar ofendida, eu diria.",
        "Doze horas de abandono. Suas desculpas terão de ser extraordinárias — e talvez ainda insuficientes, eu diria.",
        "A paciência de Betty se esgotou. O que resta é uma curiosidade mórbida sobre sua audácia, eu diria.",
    ),
    (
        "Um dia inteiro. Betty exige uma explicação, um pedido de desculpas e talvez um pequeno tributo, eu diria.",
        "Vinte e quatro horas de ausência. Mestre, sua audácia seria admirável se não fosse tão irritante, eu diria.",
        "Betty esperou um dia. Não por sentir sua falta, evidentemente. Não tire conclusões absurdas, eu diria.",
        "Um dia sem aparecer? Betty registrou a ofensa em sua memória. Ela é excelente, infelizmente para você, eu diria.",
    ),
)

RETURN_PHRASES = (
    (
        "O-Ora, mestre! Resolveu aparecer? Betty não estava esperando, apenas notou sua ausência, eu diria.",
        "Ah, voltou. Betty estava muito bem sem você. Naturalmente. Absolutamente bem, eu diria.",
        "Veja só, lembrou-se de Betty. Não que ela tenha sentido sua falta; seria ridículo, eu diria.",
        "Mestre...! Quer dizer, enfim apareceu. Betty não percebeu que estava esperando, eu diria.",
    ),
    (
        "Quinze minutos e voltou? Betty não estava contando. O relógio é que estava muito visível, eu diria.",
        "Agora aparece, mestre? Betty estava ocupada demais para sentir sua falta. Quase, eu diria.",
        "Que surpresa. Uma surpresa que Betty, por acaso, já esperava há algum tempo, eu diria.",
        "Você voltou. Betty jamais admitiria que olhou para a entrada mais de uma vez, eu diria.",
    ),
    (
        "Uma hora ausente e volta sem uma reverência sequer? A ousadia, mestre, eu diria.",
        "Betty está decidindo se aceita seu retorno. Não confunda silêncio com perdão, eu diria.",
        "Sua ausência foi notada. A recepção calorosa ainda está sob análise, eu diria.",
        "Finalmente. Betty tem algumas observações — organizadas por gravidade, naturalmente, eu diria.",
    ),
    (
        "Três horas! Mestre, comece sua explicação. Betty decidirá se ela merece ser ouvida, eu diria.",
        "Voltou, enfim. Betty quase declarou sua ausência uma ofensa formal, eu diria.",
        "Não pense que um simples retorno apaga três horas de descortesia, eu diria.",
        "Betty está furiosa. Ainda assim, concederá a você a honra de se explicar. Talvez, eu diria.",
    ),
    (
        "Seis horas desaparecido e retorna assim? Sua coragem é quase tão grande quanto sua falta de modos, eu diria.",
        "Mestre, Betty preparou uma lista de queixas. A primeira é sua demora em voltar, eu diria.",
        "Você retornou. Ótimo. Agora convença Betty de que merece ser perdoado, eu diria.",
        "Betty não sentiu sua falta. Sentiu uma irritação perfeitamente razoável. E enorme, eu diria.",
    ),
    (
        "Doze horas! Sua explicação será ouvida, mestre. A absolvição é outra questão, eu diria.",
        "Betty poderia parar de esperar por você. Poderia. Não interprete isso como promessa, eu diria.",
        "Volta depois de doze horas e espera uma recepção gentil? Que otimismo encantador, eu diria.",
        "Betty está furiosa. Recomenda-se que escolha as próximas palavras com extrema cautela, eu diria.",
    ),
    (
        "Um dia inteiro! Mestre, sua desculpa terá de ser digna de uma audiência real, eu diria.",
        "Depois de um dia, aparece como se nada houvesse acontecido? Betty está impressionada com a imprudência, eu diria.",
        "Betty esperou por você. Pronto, está dito. Não a faça repetir uma confissão tão embaraçosa, eu diria.",
        "Sua ausência foi imperdoável. Betty está considerando reduzir sua posição na hierarquia, eu diria.",
    ),
)

_state = NORMAL
_last_interaction = time.monotonic()
_last_announced_level = -1
_last_phrase = None
_last_night_reminder: tuple[date, int] | None = None
_last_uptime_level = -1
_lock = threading.Lock()


def _level_for_idle(idle_time: float) -> int:
    level = -1
    for index, milestone in enumerate(REMINDER_MILESTONES):
        if idle_time < milestone:
            break
        level = index

    if idle_time >= REMINDER_MILESTONES[-1]:
        extra_levels = int((idle_time - REMINDER_MILESTONES[-1]) // REPEAT_AFTER_MAX_LEVEL)
        level += extra_levels

    return level


def _state_for_level(level: int) -> str:
    states = (
        NORMAL,
        SENTIDA,
        IRRITADA,
        ZANGADA,
        FURIOSA,
        FURIOSA,
        DRAMATICA,
        DRAMATICA,
    )
    safe_level = max(level, 0)
    return states[min(safe_level, len(states) - 1)]


def _choose_phrase(phrases: tuple[str, ...]) -> str:
    global _last_phrase

    choices = [phrase for phrase in phrases if phrase != _last_phrase]
    phrase = random.choice(choices or list(phrases))
    _last_phrase = phrase
    return phrase


def get_attention_state(*, busy: bool = False) -> str:
    if busy:
        return OCUPADA

    with _lock:
        return _state


def register_interaction(now: float | None = None) -> str | None:
    global _last_interaction, _last_announced_level, _state

    current_time = time.monotonic() if now is None else now

    with _lock:
        idle_time = current_time - _last_interaction
        level = _level_for_idle(idle_time)
        _last_interaction = current_time
        _last_announced_level = -1

        if level >= 1:
            _state = REUNIAO
            phrase_level = min(level - 1, len(RETURN_PHRASES) - 1)
            return _choose_phrase(RETURN_PHRASES[phrase_level])

        _state = NORMAL
        return None


def check_attention(*, busy: bool = False, now: float | None = None) -> str | None:
    global _last_announced_level, _state

    if busy:
        return None

    current_time = time.monotonic() if now is None else now

    with _lock:
        idle_time = current_time - _last_interaction
        level = _level_for_idle(idle_time)
        _state = _state_for_level(level)

        if level > _last_announced_level:
            _last_announced_level = level
            phrase_level = min(level, len(IDLE_PHRASES) - 1)
            return _choose_phrase(IDLE_PHRASES[phrase_level])

    return None


def check_night_attention(
    *,
    mouse_active: bool,
    now: datetime | None = None,
) -> str | None:
    global _last_night_reminder

    if not mouse_active:
        return None

    current_time = datetime.now() if now is None else now
    if current_time.hour >= NIGHT_END_HOUR:
        return None

    stage = min(current_time.hour, len(NIGHT_PHRASES) - 1)
    reminder_key = (current_time.date(), stage)

    with _lock:
        if reminder_key == _last_night_reminder:
            return None

        _last_night_reminder = reminder_key
        return _choose_phrase(NIGHT_PHRASES[stage])


def check_uptime_attention(uptime_seconds: float) -> str | None:
    global _last_uptime_level

    if uptime_seconds <= UPTIME_REMINDER_AFTER:
        return None

    with _lock:
        level = max(
            index
            for index, milestone in enumerate(UPTIME_MILESTONES)
            if uptime_seconds >= milestone
        )
        if level <= _last_uptime_level:
            return None

        _last_uptime_level = level
        return _choose_phrase(UPTIME_PHRASES[level])


def monitor_attention(
    is_busy: Callable[[], bool],
    is_mouse_active: Callable[[], bool],
) -> None:
    from .system import get_uptime_seconds
    from .tts import speak

    while True:
        message = None
        if not is_busy():
            message = check_attention()
            if message is None:
                message = check_night_attention(
                    mouse_active=is_mouse_active(),
                )
            if message is None:
                message = check_uptime_attention(get_uptime_seconds())

        if message:
            print(f"[Betty] {message}")
            speak(message)

        time.sleep(CHECK_INTERVAL)
